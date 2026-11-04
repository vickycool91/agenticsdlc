from app.planner import detect_scenario, normalize, build_tasks

def test_detect_ambiguous_requirement():
    assert detect_scenario("Make the service faster and more reliable.","auto","")=="ambiguous"

def test_brownfield_has_impact_task():
    tasks=build_tasks("brownfield")
    assert any(t.id=="T3" and t.agent=="impact" for t in tasks)
    assert next(t for t in tasks if t.id=="T4").depends_on==["T2","T3"]

def test_scale_requirement_surfaces_missing_slos():
    result=normalize("Build a scalable API", "greenfield")
    assert "target throughput and latency SLOs" in result["ambiguities"]
