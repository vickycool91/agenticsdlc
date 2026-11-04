# Agentic SDLC Studio — Learning Guide

This guide explains the Studio as a small, runnable example of an agent-assisted software delivery lifecycle. It is intended for someone learning both the workflow and the codebase. The project is a prototype: the workflow is real and inspectable, but specialist-agent behavior is intentionally deterministic/mock-friendly rather than a production multi-agent platform.

## 1. What the Studio does

Give the Studio a software requirement. It records the requirement and selected assumptions, creates a work plan and proposed design, generates a set of engineering artifacts, runs validation, and presents the result for a human decision. For this assignment, the required example is a URL Shortener.

The Studio has two related but separate parts:

- **Engineering workspace:** guides and records the SDLC workflow, decisions, artifacts, validation and approval.
- **Generated URL Shortener demo:** a runnable web application where you can create short links, follow redirects and inspect click counts.

The demo application is not the Studio itself. It is an example product produced for the Studio to showcase.

## 2. End-to-end workflow

The UI presents six stages. The stage indicator is a navigation aid; the run's status and evidence are shown in the corresponding panels and tabs.

### Stage 1 — Understand

**Goal:** turn a broad request into a clear problem statement and identify missing requirements.

For the URL Shortener, the initial requirement is something like: “Build a scalable URL shortener service with APIs, persistence, and analytics.” That is not yet precise enough to implement. The Studio presents clarifications such as:

- Scale target: startup, growth or hyperscale.
- Analytics depth: basic counts, standard event dimensions or advanced privacy-sensitive analytics.
- Custom aliases: allowed or not.
- Link expiry: optional, never or default expiry.
- Link creation policy: API-key holders or anonymous rate-limited users.

**What to learn:** requirements are decisions, not just prose. Scale changes architecture; analytics changes data capture and storage; expiry changes redirect behavior and cleanup. The selected answers are recorded as assumptions for the run. Confirm them before continuing.

### Stage 2 — Plan

**Goal:** break the requirement into deliverable work items and dependencies.

A useful plan makes work observable: each item has a scope, dependencies and an indication of criticality. Review the sequence and look for missing work such as API contracts, persistence, validation, tests, operational concerns and documentation.

**What to learn:** planning is more than a task list. Dependencies determine what can run in parallel and what blocks later work. A plan should be traceable back to the requirement and forward to artifacts and tests.

### Stage 3 — Design

**Goal:** make important technical choices explicit before code generation.

The URL Shortener design review surfaces decisions such as:

- Short-code generation: random base62 with collision retry, or a sequence-based strategy.
- Production datastore: PostgreSQL with replicas/partitioning, or a key-value store such as DynamoDB.
- Analytics capture: asynchronous buffered writes, or synchronous writes on redirects.
- Redirect status: 302 temporary, or 301 permanent.

For each choice, consider consistency, collision behavior, latency, operational complexity, cost and future scale. The local demo uses SQLite so it can run on a laptop without external infrastructure; that is a demo implementation choice, not a claim that SQLite is the production datastore for hyperscale traffic.

**What to learn:** architecture is a set of trade-offs. There is rarely one universally correct option. Record why a choice fits the target scale and constraints.

### Stage 4 — Build

**Goal:** generate implementation and supporting engineering artifacts from the requirement, plan and design context.

Inspect the generated artifact list. Typical deliverables include application code, API description, database schema, tests, deployment material and engineering documentation. Read the artifacts rather than assuming that a successful generation step means the design is production-ready.

**What to learn:** generated code is a proposal that must be reviewed. Check whether the implementation reflects the approved requirements and design decisions. Look for missing security, observability, operational and failure-handling details.

### Stage 5 — Validate

**Goal:** collect evidence that the generated result meets its checks.

Review test outcomes, coverage information where available, and guardrail findings. A passing test suite only proves the behaviors covered by those tests; it does not prove production scalability, security or resilience.

**What to learn:** validation should be tied to requirements. For example, URL creation needs tests for valid URLs, invalid input and alias conflicts; redirect behavior needs tests for existing, missing and expired codes; analytics needs tests that a redirect increments the expected count.

### Stage 6 — Review

**Goal:** make a human accountable for the final engineering outcome.

Read the engineering summary, inspect important artifacts, review validation evidence and residual risks, then approve or reject. Approval is a workflow decision; it does not deploy the service to production.

**What to learn:** human approval is a control point. It should consider requirement fit, design trade-offs, test evidence, known limitations and operational readiness.

## 3. How to use the UI

1. Start a new run and enter a requirement, or select the URL Shortener example.
2. In **Understand**, review each clarification and change the proposed answer where appropriate. Confirm to continue.
3. Open **Plan** and inspect the work items and dependencies.
4. Open **Design** and review the proposed architecture choices and trade-offs. Submit a change request if the design does not fit.
5. Continue through **Build** and inspect generated artifacts.
6. Open **Validation** and review test evidence and findings.
7. In **Review**, read the summary and risks, add an optional comment, and approve or reject.
8. Use the workflow trace/activity view to understand what happened and in what order.

The tabs provide different views of the same run: overview for the requirement and assumptions, plan for work decomposition, workflow for execution history, design for architecture decisions, artifacts for generated files, validation for test evidence, risks for residual concerns, summary for the engineering outcome, and activity for recorded events.

## 4. Try the generated URL Shortener

Launch the demo from the Studio's **Launch URL Shortener demo** action, or visit `http://127.0.0.1:8000/demo` while the Studio is running.

1. Paste a long URL such as `https://www.example.com/articles/agentic-sdlc-learning`.
2. Optionally enter a custom alias if enabled.
3. Select an expiry option if offered.
4. Create the short link.
5. Open the short link in a new tab. This exercises the redirect endpoint.
6. Return to the demo and refresh the list. Inspect the click count/analytics.

The demo persists its local data in the SQLite database under `examples/url-shortener/output/`. It is intended for local learning and demonstration, not public internet exposure or production traffic. Do not use real customer or sensitive URLs in a demo database.

## 5. Codebase map

| Path | Responsibility |
|---|---|
| `run.py` | Starts the local FastAPI/uvicorn server. |
| `app/main.py` | HTTP routes for the Studio, run lifecycle, artifacts and demo. |
| `app/orchestrator.py` | Coordinates a run, stores run metadata and exposes run state. |
| `app/planner.py` | Creates the work breakdown/dependency plan. |
| `app/artifacts.py` | Produces the engineering artifact set. |
| `app/validators.py` | Runs project validation and guardrail checks. |
| `app/models.py` | Shared data models. |
| `app/url_shortener.py` | URL Shortener service logic used by the demo. |
| `web/index.html` | Studio browser UI and its client-side interactions. |
| `agentic/agents/` | Specialist role modules used to organize agent responsibilities. |
| `agentic/blueprints/tpl_url_shortener/` | Reusable templates for the URL Shortener output. |
| `examples/url-shortener/output/` | Generated, standalone URL Shortener example. |
| `tests/` | Studio-level automated tests. |

## 6. Architecture at a glance

```text
Browser
  |
  v
Studio UI (web/index.html)
  |
  v
FastAPI routes (app/main.py)
  |
  v
Workflow Orchestrator (app/orchestrator.py)
  |---- Requirement interpretation / recorded assumptions
  |---- Planner (app/planner.py)
  |---- Specialist role modules (agentic/agents/)
  |---- Artifact generation (app/artifacts.py)
  |---- Validation (app/validators.py)
  |
  v
Run metadata + generated artifacts
  |
  v
Human review / approve or reject

Separate demo path:
Browser -> /demo -> URL Shortener API/service -> SQLite
```

The workflow orchestration and the generated URL Shortener are deliberately distinguishable. The Studio manages engineering work; the demo shows one generated product running locally.

## 7. Local setup and commands

From the project root in Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8000`. To run the Studio tests:

```cmd
python -m pytest -q
```

If `python` is not recognized but the Python launcher is installed, replace `python` with `py` in the commands above.

## 8. Prototype boundaries and production gaps

This repository is a learning/demo prototype, not a production-ready autonomous engineering platform. Before production use, evaluate and implement at least:

- Durable, transactional workflow state and artifact storage with backups and retention.
- Authentication, authorization, tenant isolation and audit controls.
- Secrets management and safe handling of source code and user requirements.
- Sandboxed execution for generated code and tests; resource/time limits.
- Supply-chain scanning, dependency pinning, SAST/DAST and license checks.
- Production datastore, migrations, backups, rate limiting and abuse prevention for the URL Shortener.
- Observability, alerting, SLOs, capacity/load testing, disaster recovery and operational runbooks.
- Stronger agent evaluation, tool permissions, prompt-injection defenses and human checkpoints.

A green validation panel is evidence from the included checks only. It is not a production certification.

## 9. Suggested learning sequence

- First, run the Studio and complete one URL Shortener workflow without changing defaults.
- Next, change one requirement (for example, expiry) and observe which plan/design/artifact sections should change.
- Then inspect `app/orchestrator.py` and trace the API route into the planner, artifact generator and validator.
- Finally, launch the demo and follow a link to see how create, redirect and analytics behavior connect end-to-end.

## 10. Guided workflow gates (updated)

The Studio presents one primary workspace and one active step at a time. The sidebar's **New engineering run** action only resets the workspace; it does not execute agents. There is no second "Run engineering workflow" form competing with the Understand panel.

The six steps are intentionally gated:

1. **Understand** — enter the requirement and confirm scope assumptions.
2. **Plan** — review the planning approach and accept the plan.
3. **Design** — choose the architecture options and confirm them.
4. **Build** — the explicit **Execute engineering workflow** action starts the backend run. This is the only step that launches agent execution.
5. **Validate** — inspect generated artifact checks, bundled test results and workflow trace.
6. **Review** — open the review panel and record approval or rejection.

A step cannot be selected before the preceding gate is completed. The UI no longer jumps directly from Understand to Review after the backend returns. The backend currently executes the dependency-aware agent task graph as one build operation; validation follows that operation and final approval remains a separate human decision. In other words, the human-facing workflow is sequential, while independent agent tasks inside Build may run concurrently according to their dependencies.


**Demo access gate:** The runnable URL Shortener is intentionally locked until an engineering run completes and a reviewer approves it. After approval, use **Launch URL Shortener demo**. Link creation reports success or a validation/API error without silently clearing the entered URL.

## 11. Generated-code quality and review expectations

The URL Shortener artifact is produced from a maintained Python template. It is not a raw dump of a model response. The template uses the same conventions expected in a reviewed service: standard-library imports grouped at the top, type hints on public methods, descriptive names, short methods with one responsibility, parameterized SQL, bounded collision handling, and tests named around observable behavior. The generated test suite is run independently as part of the Studio's regression tests.

Remote model mode currently assists with selected architecture, implementation-review and risk-review tasks; it does not write every source file from scratch. The generated source therefore remains deterministic and reviewable. For a brownfield requirement, provide the actual repository structure, relevant modules, API contracts and tests. Without that context, the Studio can only produce a scaffold and proposed contract; it cannot responsibly invent project-specific implementation details.

Before accepting generated code, a developer should still check that it matches the agreed design, uses the project's established conventions, handles failure paths, protects secrets and untrusted input, and has appropriate unit, integration, concurrency and security coverage. No coding style can guarantee a particular result from AI-detection tools, and detector scores are not a substitute for code review, tests or evidence of authorship.
