from pathlib import Path
from app.orchestrator import WorkflowOrchestrator

def test_run_metadata_survives_orchestrator_restart(tmp_path):
    first = WorkflowOrchestrator(tmp_path)
    run = {
        "run_id": "abc123",
        "artifacts_dir": str(tmp_path / "abc123"),
        "artifacts": ["README.md"],
        "status": "awaiting_approval",
    }
    Path(run["artifacts_dir"]).mkdir()
    (Path(run["artifacts_dir"]) / "README.md").write_text("demo")
    first.runs[run["run_id"]] = run
    first._save_runs()

    second = WorkflowOrchestrator(tmp_path)
    assert "abc123" in second.runs
    restored = second.runs["abc123"]
    artifact = Path(restored["artifacts_dir"]) / "README.md"
    assert artifact.read_text() == "demo"
