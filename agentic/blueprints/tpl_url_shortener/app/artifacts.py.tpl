from pathlib import Path
import json

OPENAPI = '''openapi: 3.1.0
info:
  title: URL Shortener API
  version: 1.0.0
paths:
  /api/urls:
    post:
      summary: Create a short URL
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [url]
              properties:
                url: {type: string, format: uri}
      responses:
        '201': {description: Created or existing short link}
        '422': {description: Invalid URL}
  /{code}:
    get:
      summary: Resolve a short code
      parameters:
        - {in: path, name: code, required: true, schema: {type: string}}
      responses:
        '307': {description: Redirect}
        '404': {description: Not found}
  /api/urls/{code}/analytics:
    get:
      summary: Read click analytics
      parameters:
        - {in: path, name: code, required: true, schema: {type: string}}
      responses:
        '200': {description: Analytics}
        '404': {description: Not found}
'''
URL_SOURCE = r'''from __future__ import annotations

import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS urls ("
    "code TEXT PRIMARY KEY, "
    "original_url TEXT NOT NULL UNIQUE, "
    "created_at REAL NOT NULL, "
    "click_count INTEGER NOT NULL DEFAULT 0 CHECK (click_count >= 0)"
    ")"
)


class URLShortener:
    """Persist short links and keep a simple redirect counter in SQLite."""

    _CODE_CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    _MAX_CODE_ATTEMPTS = 20

    def __init__(self, database_path: str | Path = "url_shortener.db", code_length: int = 7) -> None:
        self.database_path = str(database_path)
        self.code_length = max(5, int(code_length))

        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def validate_url(url: str) -> str:
        """Accept absolute HTTP(S) URLs; reject relative and other schemes."""
        value = str(url).strip()
        parsed = urlsplit(value)

        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a complete URL beginning with http:// or https://")

        return value

    def _new_code(self) -> str:
        return "".join(
            secrets.choice(self._CODE_CHARACTERS)
            for _ in range(self.code_length)
        )

    def shorten(self, url: str) -> dict[str, Any]:
        """Create a short link, reusing the existing code for an exact URL."""
        destination = self.validate_url(url)

        with self._connect() as connection:
            existing = connection.execute(
                "SELECT code FROM urls WHERE original_url = ?",
                (destination,),
            ).fetchone()
            if existing is not None:
                return {"code": existing["code"], "url": destination, "created": False}

            for _attempt in range(self._MAX_CODE_ATTEMPTS):
                code = self._new_code()
                try:
                    connection.execute(
                        "INSERT INTO urls (code, original_url, created_at) VALUES (?, ?, ?)",
                        (code, destination, time.time()),
                    )
                except sqlite3.IntegrityError:
                    # A concurrent request may have inserted this destination first.
                    existing = connection.execute(
                        "SELECT code FROM urls WHERE original_url = ?",
                        (destination,),
                    ).fetchone()
                    if existing is not None:
                        return {"code": existing["code"], "url": destination, "created": False}
                    # Otherwise the generated code collided with an existing row.
                    continue

                return {"code": code, "url": destination, "created": True}

        raise RuntimeError("Could not allocate a unique short code. Please try again.")

    def resolve(self, code: str) -> str | None:
        """Return the destination and increment its redirect count."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT original_url FROM urls WHERE code = ?",
                (code,),
            ).fetchone()
            if row is None:
                return None

            connection.execute(
                "UPDATE urls SET click_count = click_count + 1 WHERE code = ?",
                (code,),
            )
            return str(row["original_url"])

    def analytics(self, code: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT code, original_url, created_at, click_count FROM urls WHERE code = ?",
                (code,),
            ).fetchone()
            return dict(row) if row is not None else None

    def list_urls(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the newest links first, with a defensive upper bound."""
        safe_limit = max(1, min(int(limit), 500))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT code, original_url, created_at, click_count "
                "FROM urls ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
            return [dict(row) for row in rows]
'''

TEST_SOURCE = r'''from __future__ import annotations

import pytest

from src.url_shortener import URLShortener


def test_create_resolve_and_record_clicks(tmp_path):
    service = URLShortener(tmp_path / "links.sqlite3")

    result = service.shorten("https://example.com/products/42")
    assert result["created"] is True
    assert len(result["code"]) == 7
    assert service.resolve(result["code"]) == "https://example.com/products/42"
    assert service.analytics(result["code"])["click_count"] == 1


def test_repeated_request_reuses_the_existing_short_code(tmp_path):
    service = URLShortener(tmp_path / "links.sqlite3")

    first = service.shorten("https://example.com/account")
    second = service.shorten("https://example.com/account")

    assert second["code"] == first["code"]
    assert second["created"] is False


def test_rejects_urls_with_unsupported_schemes(tmp_path):
    service = URLShortener(tmp_path / "links.sqlite3")

    with pytest.raises(ValueError, match="http:// or https://"):
        service.shorten("javascript:alert(1)")


def test_unknown_code_has_no_destination_or_analytics(tmp_path):
    service = URLShortener(tmp_path / "links.sqlite3")

    assert service.resolve("missing") is None
    assert service.analytics("missing") is None


def test_list_urls_returns_newest_links_and_click_counts(tmp_path):
    service = URLShortener(tmp_path / "links.sqlite3")
    older = service.shorten("https://example.com/older")
    newer = service.shorten("https://example.com/newer")
    service.resolve(older["code"])

    rows = service.list_urls()
    assert [row["code"] for row in rows] == [newer["code"], older["code"]]
    assert rows[1]["click_count"] == 1
'''

def put(root: Path, rel: str, content: str, names: list[str]):
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content.strip()+"\n",encoding="utf-8"); names.append(rel)

def generate_bundle(run_dir: Path, normalized: dict, plan: list[dict], scenario: str, requirement: str, repository_context: str="") -> list[str]:
    names=[]
    put(run_dir,"requirement.json",json.dumps(normalized,indent=2),names); put(run_dir,"plan.json",json.dumps(plan,indent=2),names)
    architecture=f'''# Architecture Overview\n\n## Problem\n{normalized["normalized_problem"]}\n\n## Scenario\n{scenario}\n\n## Proposed design\n- Stateless API layer validates requests and returns explicit status codes.\n- Domain service owns code allocation, URL resolution, and analytics.\n- Persistence stores code, destination, creation time, and click count.\n- Production-scale design: PostgreSQL as source of truth, cache for hot redirects, and asynchronous event stream for analytics.\n- Local reference uses SQLite and synchronous counters for reproducibility.\n\n## Data flow\n1. Client submits an absolute HTTP(S) URL. 2. API validates it. 3. Service stores a mapping. 4. Redirect resolves the code and records a click. 5. Analytics endpoint returns counts.\n\n## Scalability and reliability\nUse stateless replicas, PostgreSQL unique constraints and connection pooling, cache invalidation, async analytics, rate limiting, abuse detection, backups, and latency/error/saturation telemetry.\n\n## Trade-offs\nDeterministic hash-derived codes support repeat-request idempotency but require collision handling. Synchronous counters are simple but add redirect write load. SQLite is demo-only; use PostgreSQL for concurrent production traffic.\n'''
    put(run_dir,"architecture.md",architecture,names)
    if "shortener" in requirement.lower():
        api_contract=OPENAPI
    elif "payment" in requirement.lower():
        api_contract="""openapi: 3.1.0
info: {title: Payment API, version: 1.0.0}
paths:
  /payments:
    post:
      summary: Submit a payment with idempotency protection
      parameters:
        - in: header
          name: Idempotency-Key
          required: true
          schema: {type: string, minLength: 8}
      requestBody:
        required: true
        content:
          application/json:
            schema: {type: object, required: [amount, currency], properties: {amount: {type: number, exclusiveMinimum: 0}, currency: {type: string, minLength: 3, maxLength: 3}}}
      responses:
        '201': {description: Payment accepted}
        '409': {description: Idempotency key reused with a different request}
        '422': {description: Invalid request}
"""
    else:
        api_contract="""openapi: 3.1.0
info: {title: Service Improvement API, version: 1.0.0}
paths:
  /health:
    get:
      summary: Health check endpoint (proposed baseline)
      responses:
        '200': {description: Service health and dependency status}
"""
    put(run_dir,"api/openapi.yaml",api_contract,names)
    if "shortener" in requirement.lower():
        put(run_dir,"src/__init__.py","",names); put(run_dir,"src/url_shortener.py",URL_SOURCE,names); put(run_dir,"tests/test_url_shortener.py",TEST_SOURCE,names)
    else:
        put(run_dir,"src/implementation_scaffold.py",'''"""Reviewable implementation scaffold; domain behavior needs repository-specific refinement."""\ndef validate_input(value: str) -> str:\n    if not value or not value.strip():\n        raise ValueError("value must not be empty")\n    return value.strip()\n''',names)
        put(run_dir,"tests/test_scaffold.py",'''import pytest\nfrom app.implementation_scaffold import validate_input\ndef test_trim(): assert validate_input(" hello ")=="hello"\ndef test_empty():\n    with pytest.raises(ValueError): validate_input(" ")\n''',names)
    docs=f'''# Implementation Guide\n\n## Requirement\n{requirement}\n\n## Plan\n'''+"\n".join(f"- **{p['id']} {p['name']}** — {p['status']}" for p in plan)+'''\n\n## Verification\n1. Install requirements. 2. Run `pytest -q`. 3. Inspect OpenAPI and generated source. 4. Review risks and assumptions.\n\n## Operations\nAdd structured logs, request IDs, latency/error metrics, tracing, health checks, migration management, backup/restore tests, and alerting before production.\n'''
    put(run_dir,"docs/implementation.md",docs,names)
    risks='''# Risk Review\n\n| Risk | Impact | Mitigation / verification |\n|---|---|---|\n| Ambiguous scale targets | Wrong sizing/cost | Agree peak RPS, p95/p99 latency, retention, and availability SLOs |\n| Short-code collision | Wrong mapping / failed create | Unique constraint, bounded retries, collision tests |\n| Unsafe URL / abuse | Phishing | HTTP(S) validation, rate limits, abuse reporting, domain controls |\n| Analytics write amplification | Redirect latency | Queue events and aggregate asynchronously |\n| Model-generated unsafe code | Security defects | Treat as untrusted; syntax/tests/scanners and human review |\n| Prompt injection in repository | Unsafe tool use | Treat repo text as data, allowlist tools, isolate credentials |\n| Green tests hide production risk | Incidents | Load, concurrency, migration, security, and failure-injection tests |\n| In-memory run state | Lost runs on restart | Durable database and workflow engine |\n'''
    put(run_dir,"risk_review.md",risks,names)
    put(run_dir,"validation_report.json",json.dumps({"status":"pending","checks":[{"name":"artifact completeness","status":"pending"},{"name":"python syntax","status":"pending"},{"name":"reference tests","status":"pending"},{"name":"human approval","status":"required"}]},indent=2),names)
    put(run_dir,"execution_trace.json","[]",names)
    summary=f'''# Engineering Summary\n\n## Requirement\n{requirement}\n\n## Scenario\n{scenario}\n\n## Implementation plan\n- Normalize intent and record assumptions/ambiguities.\n- Design architecture and data flow.\n- Generate source and API contract.\n- Generate tests and documentation.\n- Review security, reliability, scalability, and validation risks.\n- Run checks and require human approval.\n\n## Generated artifacts\nSee `architecture.md`, `api/openapi.yaml`, `src/`, `tests/`, `docs/`, `risk_review.md`, and `validation_report.json`.\n\n## Limitations\nThis prototype does not deploy infrastructure. Brownfield analysis depends on supplied repository context. Review generated code before merge and add production load, concurrency, security, and migration tests.\n'''
    put(run_dir,"engineering_summary.md",summary,names)
    return names
