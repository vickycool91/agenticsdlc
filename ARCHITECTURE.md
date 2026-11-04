# Agentic SDLC Studio — Architecture

## 1. Purpose

Agentic SDLC Studio is a local, human-supervised prototype that turns a software requirement into a sequence of reviewable engineering activities and artifacts. The included URL Shortener is the reference application used to demonstrate the workflow end to end.

The product has two related but distinct parts:

- **The Studio:** captures a requirement, plans work, generates engineering artifacts, validates the result and asks a human to approve the run.
- **The URL Shortener demo:** a small application used to demonstrate a generated product. Access to the demo is gated by approval of the latest completed Studio run.

This is a prototype, not a production-ready autonomous software delivery platform. In particular, approval is not deployment, and generated code must still be reviewed before it is used in a real environment.

## 2. High-level architecture

```text
                           Human reviewer
                                |
                                v
+----------------------------------------------------------------+
| Browser UI: web/index.html                                     |
| Understand -> Plan -> Design -> Build -> Validate -> Review    |
+----------------------------------------------------------------+
                                |
                                | HTTP / JSON
                                v
+----------------------------------------------------------------+
| FastAPI application: app/main.py                               |
| - run creation and retrieval                                   |
| - approval and artifact download                               |
| - URL Shortener demo routes                                    |
+----------------------------------------------------------------+
             |                                  |
             v                                  v
+-----------------------------+    +-----------------------------+
| Workflow engine             |    | URL Shortener service       |
| app/orchestrator.py         |    | app/url_shortener.py        |
|                             |    |                             |
| planner.py                  |    | URL validation              |
| artifacts.py                |    | short-code generation       |
| validators.py               |    | SQLite persistence         |
| agentic/agents/*             |    | redirect and click counts  |
+-----------------------------+    +-----------------------------+
             |                                  |
             v                                  v
+-----------------------------+    +-----------------------------+
| Local run artifacts         |    | SQLite database             |
| artifacts/                  |    | demo data                    |
| runs_index.json             |    +-----------------------------+
+-----------------------------+
```

## 3. Main components and responsibilities

| Component | Responsibility |
|---|---|
| `web/index.html` | Browser workspace and guided stage navigation. Displays requirements, decisions, task progress, generated artifacts, validation findings and approval controls. |
| `app/main.py` | FastAPI routes, request validation, run lifecycle API, artifact download and demo endpoints. Enforces the approval gate for the demo. |
| `app/models.py` | Pydantic request and response models used at API boundaries. |
| `app/planner.py` | Requirement scenario detection, normalization, ambiguity/assumption capture and task dependency planning. |
| `app/orchestrator.py` | Coordinates execution of dependency-ready tasks, records task outcomes and assembles the run result. |
| `agentic/agents/` | Specialist role modules for planning, engineering, architecture, testing, risk and technical writing. These establish role boundaries; they are not evidence of a distributed fleet of independently operating agents. |
| `app/artifacts.py` | Produces the run's engineering deliverables using project context and generation templates. |
| `app/validators.py` | Performs configured artifact and scenario checks and records validation findings. |
| `app/llm.py` | Optional OpenAI-compatible Chat Completions adapter used for selected tasks when remote mode is enabled. |
| `app/url_shortener.py` | URL Shortener domain/service logic and SQLite persistence used by the demo. |
| `tests/` | API, planner, orchestration, UI regression, demo and generated-artifact tests. |

## 4. Guided workflow

The UI presents the following human-facing stages:

1. **Understand** — capture the requirement and identify missing information, assumptions and ambiguity.
2. **Plan** — turn the requirement into work items and dependency relationships.
3. **Design** — review the proposed architecture, API/data-flow choices and important trade-offs.
4. **Build** — execute the planned workflow and generate source and supporting engineering artifacts.
5. **Validate** — inspect validation outcomes and evidence produced by the run.
6. **Review** — inspect the result and explicitly approve or reject it.

The stage order is deliberate. A later stage should not be treated as accepted merely because an earlier stage completed. The browser UI owns the guided presentation; the backend run endpoint performs the actual workflow execution. The approval endpoint accepts approval only for a run that has reached the expected reviewable state.

### API surface

The primary workflow endpoints are:

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/runs` | Start a workflow run. |
| `GET` | `/api/runs/{run_id}` | Retrieve the run and its current result. |
| `POST` | `/api/runs/{run_id}/approve` | Record the reviewer's approval decision. |
| `GET` | `/api/runs/{run_id}/artifacts/download` | Download the generated artifact bundle. |

The URL Shortener demo routes include:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/demo` | Serve the demo UI, subject to the approval gate. |
| `POST` | `/demo/api/urls` | Create or retrieve a short URL. |
| `GET` | `/demo/api/urls` | List stored URL records. |
| `GET` | `/demo/api/urls/{code}/analytics` | Read click analytics for a short code. |
| `GET` | `/demo/{code}` | Resolve a short code and redirect. |

## 5. Planning and task orchestration

The planner classifies a request into a scenario such as greenfield, brownfield or ambiguous. It normalizes the requirement and records assumptions or unresolved details so that they can be reviewed rather than silently treated as facts.

The task planner creates a dependency graph. The current reference graph includes requirement normalization, architecture/data-flow work, optional brownfield impact analysis, implementation/API contract, tests, documentation, risk review and final validation/summary. A task becomes eligible when its dependencies have completed. Independent eligible tasks can execute concurrently.

The orchestrator uses a local `ThreadPoolExecutor` with a bounded worker count to execute dependency-ready work. This provides useful concurrency for the local prototype, particularly for I/O-bound work. It is **not** a distributed queue/worker architecture: a run is coordinated within the application process and the task graph is executed as part of the run request. The configured retry-related metadata should not be interpreted as a durable, production-grade retry and recovery system.

## 6. Code and artifact generation

Generated deliverables are written beneath the run's artifact directory. The generation layer uses templates and run context to create source files and supporting documents. The human-code-quality update improves the reference URL Shortener output by using conventional Python structure, descriptive names, type annotations, explicit validation and behaviour-oriented tests.

The current implementation should be described accurately:

- The URL Shortener reference source is substantially template-driven.
- Mock mode uses deterministic outputs and does not require an external model.
- Remote mode uses the configured model adapter for selected architecture, implementation and risk-related tasks; it does not mean every file is independently authored by an LLM.
- Specialist role modules define responsibilities, while the main orchestrator coordinates deterministic task handlers and selected model-assisted operations.
- Generated code and artifacts are proposals for review. Passing the workflow's checks does not prove that arbitrary generated code is secure, correct or production-ready.

### Optional model configuration

Remote mode uses an OpenAI-compatible Chat Completions endpoint. Configuration is supplied through environment variables:

- `ASES_LLM_MODE`
- `ASES_LLM_BASE_URL`
- `ASES_LLM_MODEL`
- `ASES_LLM_API_KEY`

API keys must be provided through environment/secrets configuration and must not be committed to source control or included in generated artifacts. The adapter has a finite request timeout; model availability and response quality are external dependencies.

## 7. Run state and persistence

Run metadata is indexed in `artifacts/runs_index.json`, and generated deliverables are stored on the local filesystem. The runtime also maintains in-process run state used by the API and orchestrator. Consequently, the JSON index should not be mistaken for a transactional workflow database or a complete durable checkpoint/recovery mechanism.

The reference demo stores URL records in SQLite. Its `urls` table maps a short code to the original URL and records creation time and click count. SQLite is chosen for ease of local setup and demonstration, not as a universal production storage recommendation.

## 8. URL Shortener request flow

```text
Create short URL
Browser -> POST /demo/api/urls
       -> approval gate
       -> validate HTTP/HTTPS URL
       -> look for an existing mapping
       -> generate a unique short code if needed
       -> persist mapping in SQLite
       -> return short URL and creation result

Resolve short URL
Browser -> GET /demo/{code}
       -> approval gate
       -> look up code in SQLite
       -> increment click count
       -> issue HTTP redirect to original URL

Analytics
Browser -> GET /demo/api/urls/{code}/analytics
       -> approval gate
       -> read mapping and click count
       -> return analytics response
```

The service uses a configurable short-code length with a default of seven characters and a URL-safe alphanumeric alphabet. Code generation uses a cryptographically strong random-choice source and bounded collision attempts. Repeated submissions of the same original URL reuse the existing mapping. The service validates the URL scheme and network location; this alone is not sufficient protection against phishing, malware or server-side request forgery in a public production service.

## 9. Human approval and safety boundaries

The human approval checkpoint is a core design choice, not a cosmetic UI step. A reviewer should inspect the requirement interpretation, design, generated changes, tests, validation evidence and known risks before approving. Approval records a decision; it does not deploy, publish or automatically merge generated code.

The demo routes are protected by an approval check against the latest run. Both the demo page and its API routes must remain behind this gate. Any change to the gate should be accompanied by API tests to prevent bypass through direct HTTP requests.

## 10. Current limitations

The current local prototype does not provide the following production capabilities as a complete system:

- enterprise SSO, fine-grained RBAC or tenant isolation;
- distributed workflow scheduling, durable task queues or robust checkpoint/retry recovery;
- transactional run-state storage and versioned object storage for artifacts;
- isolated container or microVM execution for arbitrary generated code;
- a complete CI/CD deployment or merge integration;
- comprehensive audit identity, policy enforcement and approval attestation;
- production-grade rate limiting, abuse detection and URL reputation/takedown workflows;
- end-to-end OpenTelemetry instrumentation and service-level objectives.

Do not expose the local prototype directly to the public internet or use it as an unrestricted code execution service.

## 11. Recommended production evolution

A production-oriented version could evolve toward the following architecture:

```text
Web UI -> Authenticated API -> Workflow database
                    |                |
                    |                v
                    |          Durable workflow engine
                    |                |
                    v                v
              Policy / approval   Queue -> isolated workers
                    |                |          |
                    v                v          v
                Audit log       Model gateway  Sandboxed build/test
                                     |          |
                              Secrets manager  v
                                         Artifact/object storage
                                                  |
                                      CI checks / review / delivery
```

Recommended additions include:

1. A transactional database for runs, tasks, decisions and state transitions.
2. A durable queue/workflow engine with idempotent tasks, checkpoints, bounded retries and dead-letter handling.
3. Isolated ephemeral containers or microVMs for builds and tests, with restricted network and filesystem access.
4. A model gateway with provider abstraction, prompt/version tracking, cost controls, output validation and secret redaction.
5. SSO, RBAC, tenant boundaries, policy checks and tamper-evident audit events.
6. Versioned object storage for artifacts and source diffs.
7. CI integration that creates reviewable pull requests rather than deploying automatically.
8. OpenTelemetry traces, structured logs, metrics, dashboards and explicit SLOs.
9. URL abuse controls such as rate limits, domain/reputation checks, reporting, takedown and operational monitoring.

## 12. Local development and verification

Run commands from the project root. Follow the repository README for environment setup and startup. The test suite can be run with:

```bash
python -m pytest -q
```

The test suite covers the planner, workflow API, demo API, URL Shortener behaviour, UI regression checks and generated-artifact behaviour. A green test run is useful regression evidence, but it is not a substitute for security review, dependency scanning or testing in the target deployment environment.

## 13. Related documentation

- `docs/LEARNING_GUIDE.md` — beginner-friendly walkthrough and exercises.
- `docs/Architecture.MD` — architecture document retained at its original documentation path for compatibility.
