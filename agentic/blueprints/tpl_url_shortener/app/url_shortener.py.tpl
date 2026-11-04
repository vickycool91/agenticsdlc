from __future__ import annotations

import secrets
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = """CREATE TABLE IF NOT EXISTS urls (
    code TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    created_at REAL NOT NULL,
    click_count INTEGER NOT NULL DEFAULT 0
);"""


class URLShortener:
    """Small SQLite-backed URL shortener used by the Studio demo."""

    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, db_path: str = "url_shortener.db", code_length: int = 7):
        self.db_path = str(db_path)
        self.code_length = max(5, int(code_length))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def validate_url(url: str) -> str:
        value = str(url).strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a complete URL beginning with http:// or https://")
        return value

    def _new_code(self) -> str:
        return "".join(secrets.choice(self.ALPHABET) for _ in range(self.code_length))

    def shorten(self, url: str) -> dict:
        url = self.validate_url(url)
        with self._connect() as conn:
            # Idempotent creation: submitting the same URL returns its existing code.
            existing = conn.execute(
                "SELECT code FROM urls WHERE original_url=? ORDER BY created_at LIMIT 1", (url,)
            ).fetchone()
            if existing:
                return {"code": existing["code"], "url": url, "created": False}
            for _ in range(20):
                code = self._new_code()
                try:
                    conn.execute(
                        "INSERT INTO urls(code, original_url, created_at) VALUES(?,?,?)",
                        (code, url, time.time()),
                    )
                    return {"code": code, "url": url, "created": True}
                except sqlite3.IntegrityError:
                    continue
        raise RuntimeError("Could not allocate a unique short code. Please try again.")

    def resolve(self, code: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT original_url FROM urls WHERE code=?", (code,)).fetchone()
            if row is None:
                return None
            conn.execute("UPDATE urls SET click_count=click_count+1 WHERE code=?", (code,))
            return str(row["original_url"])

    def analytics(self, code: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT code, original_url, created_at, click_count FROM urls WHERE code=?", (code,)
            ).fetchone()
            return dict(row) if row else None

    def list_urls(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT code, original_url, created_at, click_count FROM urls ORDER BY created_at DESC LIMIT ?",
                (max(1, min(int(limit), 500)),),
            ).fetchall()
            return [dict(row) for row in rows]
