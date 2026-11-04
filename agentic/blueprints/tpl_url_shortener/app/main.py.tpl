from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .models import RunRequest, ApprovalRequest
from .orchestrator import WorkflowOrchestrator, SCENARIOS
from .config import settings

app=FastAPI(title="Agentic Software Engineering System",version="1.0.0",description="Dependency-aware engineering workflow with validation and human approval.")
engine=WorkflowOrchestrator(settings.artifact_dir,settings.max_retries)
WEB=Path(__file__).resolve().parents[1]/"web"
app.mount("/static",StaticFiles(directory=str(WEB)),name="static")
@app.get("/",response_class=HTMLResponse)
def home(): return (WEB/"index.html").read_text(encoding="utf-8")
@app.get("/api/health")
def health(): return {"status":"ok","service":"ases","default_mode":"mock"}
@app.get("/api/scenarios")
def scenarios(): return SCENARIOS
@app.post("/api/runs")
def create_run(req:RunRequest):
    run_id=uuid4().hex[:12]
    try: return engine.start(run_id,req.requirement,req.scenario,req.mode,req.repository_context)
    except Exception as exc: raise HTTPException(status_code=500,detail=f"Workflow failed: {type(exc).__name__}: {exc}")
@app.get("/api/runs/{run_id}")
def get_run(run_id:str):
    run=engine.runs.get(run_id)
    if not run: raise HTTPException(status_code=404,detail="Run not found in this process. Runs are in-memory in this prototype.")
    return engine.public_view(run)
@app.post("/api/runs/{run_id}/approve")
def approve(run_id:str,req:ApprovalRequest):
    try: return engine.approve(run_id,req.approved,req.reviewer,req.comment)
    except KeyError: raise HTTPException(status_code=404,detail="Run not found")
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc))
@app.get("/api/runs/{run_id}/artifacts/{artifact_path:path}")
def get_artifact(run_id:str,artifact_path:str):
    run=engine.runs.get(run_id)
    if not run: raise HTTPException(status_code=404,detail="Run not found")
    base=Path(run["artifacts_dir"]).resolve(); target=(base/artifact_path).resolve()
    if base not in target.parents or not target.is_file(): raise HTTPException(status_code=404,detail="Artifact not found")
    return FileResponse(target,filename=target.name)
