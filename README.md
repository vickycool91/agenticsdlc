# Agentic SDLC Studio

A local, human-supervised prototype that turns a software requirement into a traceable engineering workflow. The mandatory example product is a runnable URL Shortener.

## Learn the project

Start with **[docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md)**. It also documents the generated-code conventions, what is template-driven versus model-assisted, and the review expectations. It explains each workflow stage, how to use the UI, how to run the URL Shortener demo, where the code lives, and the prototype's limitations. For the component architecture and design trade-offs, read **[docs/Architecture.MD](docs/Architecture.MD)**.

## Run on Windows

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8000`. If `python` is not recognized but the Python launcher is installed, use `py` instead.

## Run tests

```cmd
python -m pytest -q
```

## Workflow

Understand → Plan → Design → Build → Validate → Review. The Studio records clarification assumptions and design decisions, generates reviewable artifacts, presents validation evidence, and pauses for human approval. Approval does not deploy the application.

## Try the URL Shortener

From the Studio select **Launch URL Shortener demo**, or visit `http://127.0.0.1:8000/demo`. Create a short link, open it to test the redirect, then refresh the list to inspect click counts. The local demo uses SQLite and is for learning only; do not expose it publicly or use it for production traffic.

## Project map

- `app/` — FastAPI routes, orchestration, planning, artifact generation and validation.
- `agentic/agents/` — specialist role boundaries.
- `agentic/blueprints/tpl_url_shortener/` — reusable URL Shortener templates.
- `examples/url-shortener/output/` — standalone generated URL Shortener example.
- `web/` — Studio browser interface.
- `docs/` — architecture and learning documentation.
- `tests/` — Studio-level tests.

## Prototype boundary

This is a demo/learning prototype, not a production autonomous engineering platform. It does not provide production-grade authentication, tenant isolation, sandboxing, durable distributed execution, deployment automation or production SLO guarantees. See the Learning Guide's production-gaps section before adapting it for real workloads.

## Troubleshooting: Execute Agents appears to do nothing

The Studio keeps requirement, repository context, agent mode, reviewer and decision selections in browser-side workflow state while navigating between stages. This is important because each stage panel is re-rendered as the user moves forward. The Build action submits the preserved values to `POST /api/runs`; the browser displays an execution state while the backend orchestrator runs and then renders the returned tasks, artifacts, validation and trace.

If execution fails, the Build panel now displays the returned API error instead of silently remaining on the same stage. Also check the terminal running `python run.py` for a Python traceback. A browser request for `/favicon.ico` is handled by a small SVG response and is unrelated to agent execution.

To verify the backend independently, open `http://127.0.0.1:8000/api/health`; it should return `{"status":"ok", ...}`. Then use the Studio's Build stage and click **Execute engineering workflow**.


**Demo access gate:** The runnable URL Shortener is intentionally locked until an engineering run completes and a reviewer approves it. After approval, use **Launch URL Shortener demo**. Link creation reports success or a validation/API error without silently clearing the entered URL.
