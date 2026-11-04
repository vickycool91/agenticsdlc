from pathlib import Path
import ast, subprocess, sys

def validate_artifacts(run_dir: Path) -> dict:
    checks=[]
    required=["requirement.json","plan.json","architecture.md","api/openapi.yaml","docs/implementation.md","risk_review.md","engineering_summary.md"]
    missing=[p for p in required if not (run_dir/p).is_file()]
    checks.append({"name":"artifact completeness","status":"passed" if not missing else "failed","details":{"missing":missing}})
    pyfiles=list((run_dir/"src").glob("*.py"))+list((run_dir/"tests").glob("*.py")); errors=[]
    for p in pyfiles:
        try: ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
        except SyntaxError as exc: errors.append({"file":str(p.relative_to(run_dir)),"error":str(exc)})
    checks.append({"name":"python syntax","status":"passed" if not errors else "failed","details":{"files_checked":len(pyfiles),"errors":errors}})
    contract=[]; api=(run_dir/"api/openapi.yaml").read_text(encoding="utf-8") if (run_dir/"api/openapi.yaml").exists() else ""
    if (run_dir/"src/url_shortener.py").exists():
        if "/api/urls:" not in api or "/{code}:" not in api: contract.append("OpenAPI contract lacks create or redirect path")
    elif (run_dir/"requirement.json").exists():
        requirement_data=__import__("json").loads((run_dir/"requirement.json").read_text(encoding="utf-8"))
        raw=requirement_data.get("normalized_problem", "").lower()
        expected="/payments:" if "payment" in raw else "/health:"
        if expected not in api: contract.append(f"OpenAPI contract lacks expected path {expected}")
    if (run_dir/"src/url_shortener.py").exists():
        code=(run_dir/"src/url_shortener.py").read_text(encoding="utf-8")
        for token in ["def shorten(","def resolve(","def analytics(","CREATE TABLE"]:
            if token not in code: contract.append(f"URL shortener missing {token}")
    checks.append({"name":"contract and implementation checks","status":"passed" if not contract else "failed","details":{"errors":contract}})
    return {"status":"passed" if all(c["status"]=="passed" for c in checks) else "failed","checks":checks,"human_approval":"required","safety_note":"Generated code is syntax-checked but not executed automatically."}

def run_reference_tests(project_root: Path) -> dict:
    try:
        proc=subprocess.run([sys.executable,"-m","pytest","-q","tests/test_url_shortener.py"],cwd=str(project_root),capture_output=True,text=True,timeout=60)
        return {"status":"passed" if proc.returncode==0 else "failed","returncode":proc.returncode,"stdout":proc.stdout[-3000:],"stderr":proc.stderr[-1500:]}
    except Exception as exc: return {"status":"failed","error":f"{type(exc).__name__}: {exc}"}
