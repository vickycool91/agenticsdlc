from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
def test_health_and_scenarios():
    assert client.get("/api/health").json()["status"]=="ok"
    assert "greenfield" in client.get("/api/scenarios").json()

def test_run_workflow_and_approval(tmp_path, monkeypatch):
    # Isolate artifacts for this test; no external model or network required.
    from app import main
    main.engine.artifact_root=tmp_path
    response=client.post("/api/runs",json={"requirement":"Build a scalable URL shortener service with APIs, persistence, and analytics.","scenario":"greenfield","mode":"mock"})
    assert response.status_code==200
    data=response.json(); assert data["status"] in {"awaiting_approval","needs_attention"}
    assert data["artifacts"] and data["validation"]
    bundle=client.get(f"/api/runs/{data['run_id']}/artifacts/download")
    if data["status"] == "awaiting_approval":
        assert bundle.status_code == 200
        assert bundle.headers["content-type"] == "application/zip"
        import io, zipfile
        with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
            assert "engineering_summary.md" in archive.namelist()
    else:
        assert bundle.status_code == 200
    approved=client.post(f"/api/runs/{data['run_id']}/approve",json={"approved":True,"reviewer":"reviewer","comment":"Reviewed"})
    assert approved.status_code==200 and approved.json()["status"]=="approved"

def test_url_shortener_demo_is_launchable_and_persists_links(tmp_path, monkeypatch):
    from app import main
    main.demo_service.db_path = str(tmp_path / "demo.sqlite3")
    main.demo_service.__init__(main.demo_service.db_path)
    page = client.get("/demo")
    assert page.status_code == 200
    assert "/demo/api/urls" in page.text
    created = client.post("/demo/api/urls", json={"url": "https://example.com/a/long/path"})
    assert created.status_code == 201
    code = created.json()["code"]
    listed = client.get("/demo/api/urls")
    assert any(item["code"] == code for item in listed.json())
    assert client.get(f"/demo/api/urls/{code}/analytics").json()["click_count"] == 0
    redirect = client.get(f"/demo/{code}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/a/long/path"

def test_favicon_is_served():
    response = client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('image/svg+xml')


def test_stage_ui_preserves_inputs_until_agent_execution():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / 'web' / 'index.html').read_text(encoding='utf-8')
    # Stage markup is replaced on every navigation, so user inputs must live in JS state.
    assert 'const workflowInputs=' in html
    assert 'function captureStageInputs()' in html
    assert 'function restoreStageInputs()' in html
    assert 'captureStageInputs();completedStage=Math.max(completedStage,selectedStage)' in html
    assert 'requirement:workflowInputs.requirement' in html or 'const req=workflowInputs.requirement' in html
    assert 'mode:workflowInputs.mode' in html


def test_approval_is_blocked_when_validation_needs_attention():
    from app.orchestrator import WorkflowOrchestrator
    import pytest
    engine = WorkflowOrchestrator()
    engine.runs["blocked1"] = {"run_id":"blocked1", "status":"needs_attention"}
    with pytest.raises(ValueError, match="required validation checks pass"):
        engine.approve("blocked1", True, "reviewer", "")
