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
    approved=client.post(f"/api/runs/{data['run_id']}/approve",json={"approved":True,"reviewer":"reviewer","comment":"Reviewed"})
    assert approved.status_code==200 and approved.json()["status"]=="approved"
