from pathlib import Path


def test_workflow_metrics_are_hidden_until_build_finishes():
    html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    result_start = html.index('<div id="result" class="hidden">')
    metrics_start = html.index('<div class="metrics" id="runMetrics">')
    tabs_start = html.index('<div class="tabs">', result_start)
    assert result_start < metrics_start < tabs_start
    assert 'id="taskCount"' in html
    assert 'id="artifactCount"' in html
    assert 'id="validation"' in html


def test_understand_confirmation_uses_consistent_action_alignment():
    html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    assert '.stage-actions{display:flex;justify-content:flex-end;align-items:center' in html
    assert 'class="stage-actions"><button class="primary" onclick="advanceStage()">Confirm requirements &amp; continue' in html or 'class="stage-actions"><button class="primary" onclick="advanceStage()">Confirm requirements & continue' in html


def test_url_shortener_submit_handler_remains_present():
    source = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert '<form id="form" class="form">' in source
    assert 'addEventListener("submit"' in source or "addEventListener('submit'" in source
    assert "fetch(url,options)" in source
    assert "api('/demo/api/urls'" in source
    assert "method:'POST'" in source or 'method:"POST"' in source


def test_plan_stage_shows_reviewable_tasks_before_execution():
    html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    assert "function planPreviewMarkup()" in html
    assert "PROPOSED EXECUTION BACKLOG" in html
    assert "Owner:" in html
    assert "Deliverable:" in html
    assert "Acceptance:" in html
    assert "DEPENDENCY & PARALLELISM" in html
    assert "The actual task list will appear after execution." not in html
    assert "body=planPreviewMarkup()" in html


def test_plan_preview_tracks_execution_task_ids_and_dependencies():
    html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    planner = (Path(__file__).parents[1] / "app" / "planner.py").read_text(encoding="utf-8")
    for task_id in ("T1", "T2", "T4", "T5", "T6", "T7", "T8"):
        assert f"id:'{task_id}'" in html
        assert f'Task("{task_id}"' in planner


def test_artifact_bundle_download_and_professional_workspace_label():
    html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    main = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert "Download all artifacts (.zip)" in html
    assert "/artifacts/download" in html
    assert "Engineering workspace" in html
    assert "Local prototype" not in html
    assert "Final review gate · Step 6" in html
    assert 'def download_artifacts(run_id: str)' in main
    assert 'application/zip' in main
