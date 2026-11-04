from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import json, shutil
from .planner import normalize, detect_scenario, build_tasks, URL_REQUIREMENT
from .artifacts import generate_bundle
from .validators import validate_artifacts, run_reference_tests
from .llm import ModelAdapter

SCENARIOS={
 "greenfield":{"requirement":URL_REQUIREMENT,"repository_context":"","description":"Create a scalable URL shortener with APIs, persistence, and analytics."},
 "brownfield":{"requirement":"Add idempotency to the payment submission endpoint and improve its integration tests.","repository_context":"Illustrative repository: payments/api.py exposes POST /payments; services/payment_service.py creates payment records; repositories/payment_repository.py persists them; tests/test_payments.py covers basic success only. Client retries may create duplicate payment records.","description":"Enhance an existing service and demonstrate impact analysis."},
 "ambiguous":{"requirement":"Make the service faster and more reliable.","repository_context":"","description":"Identify missing acceptance criteria before implementation."}}

class WorkflowOrchestrator:
 def __init__(self,artifact_root="artifacts",max_retries=1): self.artifact_root=Path(artifact_root); self.max_retries=max_retries; self.runs={}
 @staticmethod
 def _event(run,task_id,event,detail=""):
  run["trace"].append({"timestamp":datetime.now(timezone.utc).isoformat(),"task_id":task_id,"event":event,"detail":detail})
 def start(self,run_id,requirement,scenario_requested,mode,repository_context=""):
  scenario=detect_scenario(requirement,scenario_requested,repository_context); normalized=normalize(requirement,scenario,repository_context); is_url="shortener" in requirement.lower()
  task_specs=build_tasks(scenario); run={"run_id":run_id,"requirement":requirement,"scenario":scenario,"mode":mode,"status":"running","normalized_requirement":normalized,"tasks":{t.id:t.view() for t in task_specs},"trace":[],"artifacts":[],"validation":None,"test_result":None,"approval":{"status":"required","decision":None},"review_questions":normalized["ambiguities"]}
  self.runs[run_id]=run; self._event(run,None,"run_started",f"scenario={scenario}; mode={mode}")
  run_dir=self.artifact_root/run_id
  if run_dir.exists(): shutil.rmtree(run_dir)
  run_dir.mkdir(parents=True,exist_ok=True); model=ModelAdapter(mode)
  run["tasks"]["T1"]["status"]="completed"; run["tasks"]["T1"]["output"]={"normalized_requirement":normalized}; self._event(run,"T1","task_completed","Normalization and ambiguity scan complete")
  outputs={"T1":run["tasks"]["T1"]["output"]}; specs={t.id:t for t in task_specs}; pending={t.id for t in task_specs if t.id!="T1"}; failed=set()
  def execute(tid):
   t=specs[tid]; out={"agent":t.agent,"summary":""}
   summaries={"T2":"Architecture/data-flow design covers API, persistence, analytics, scaling, and reliability.","T3":"Impact map: API -> domain service -> repository -> transaction -> integration tests; add idempotency key and duplicate/concurrency tests.","T4":"Generated implementation scaffold and API contract.","T5":"Generated tests for happy path, invalid input, idempotency, and unknown identifiers.","T6":"Generated implementation and operator documentation.","T7":"Reviewed security, scale assumptions, collision handling, analytics load, and production gaps.","T8":"Validate artifact completeness, syntax, contract markers, and bundled reference tests."}
   out["summary"]=summaries[tid]
   if tid=="T3": out["impacted_components"]=["payments/api.py","services/payment_service.py","repositories/payment_repository.py","tests/test_payments.py"]
   if mode=="remote" and tid in {"T2","T4","T7"}:
    try: out["model_review"]=model.complete_json("You are a cautious software engineering reviewer. Do not claim tests ran. Return recommendations and concerns arrays.",json.dumps({"task":t.name,"requirement":requirement,"context":repository_context[:5000]}))
    except Exception as exc: out["model_warning"]=str(exc)
   return out
  while pending:
   ready=[tid for tid in pending if all(dep in outputs for dep in specs[tid].depends_on)]
   blocked=[tid for tid in pending if any(dep in failed for dep in specs[tid].depends_on)]
   for tid in blocked:
    run["tasks"][tid]["status"]="blocked"; run["tasks"][tid]["error"]="Dependency failed."; pending.remove(tid); failed.add(tid); self._event(run,tid,"task_blocked","A dependency failed")
   if not ready:
    for tid in list(pending): run["tasks"][tid]["status"]="blocked"; pending.remove(tid); failed.add(tid); self._event(run,tid,"task_blocked","No runnable dependency layer")
    break
   self._event(run,None,"parallel_layer_started",",".join(ready))
   with ThreadPoolExecutor(max_workers=min(4,len(ready))) as pool:
    futures={pool.submit(execute,tid):tid for tid in ready}
    for future in as_completed(futures):
     tid=futures[future]; state=run["tasks"][tid]; state["status"]="running"; state["attempts"]+=1; self._event(run,tid,"task_started",f"attempt={state['attempts']}")
     try:
      out=future.result(); outputs[tid]=out; state["output"]=out; state["status"]="completed"; self._event(run,tid,"task_completed",out["summary"])
     except Exception as exc:
      state["status"]="failed"; state["error"]=str(exc); failed.add(tid); self._event(run,tid,"task_failed",str(exc))
     pending.remove(tid)
  try:
   run["artifacts"]=generate_bundle(run_dir,normalized,[run["tasks"][t.id] for t in task_specs],scenario,requirement,repository_context)
   self._event(run,"T8","artifacts_written",f"{len(run['artifacts'])} files written")
   validation=validate_artifacts(run_dir)
   # Tests are run against the bundled reference service, never arbitrary generated files.
   test_result=run_reference_tests(Path(__file__).resolve().parents[1]) if is_url else {"status":"not_run","reason":"Reference service tests are scoped to the mandatory URL shortener scenario."}
   run["validation"],run["test_result"]=validation,test_result
   report={"artifact_validation":validation,"reference_tests":test_result}; (run_dir/"validation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
   (run_dir/"execution_trace.json").write_text(json.dumps(run["trace"],indent=2),encoding="utf-8")
   with (run_dir/"engineering_summary.md").open("a",encoding="utf-8") as f: f.write(f"\n\n## Validation outcome\n- Artifact checks: **{validation['status']}**\n- Bundled reference tests: **{test_result['status']}**\n- Human approval: **required**\n")
   run["status"]="awaiting_approval" if validation["status"]=="passed" and test_result["status"] in {"passed","not_run"} else "needs_attention"
   self._event(run,"T8","validation_completed",f"artifacts={validation['status']}; tests={test_result['status']}")
   (run_dir/"execution_trace.json").write_text(json.dumps(run["trace"],indent=2),encoding="utf-8")
  except Exception as exc:
   run["status"]="failed"; run["error"]=f"{type(exc).__name__}: {exc}"; self._event(run,"T8","validation_failed",run["error"])
  run["artifacts_dir"]=str(run_dir); return self.public_view(run)
 def public_view(self,run):
  return {"run_id":run["run_id"],"requirement":run["requirement"],"scenario":run["scenario"],"mode":run["mode"],"status":run["status"],"normalized_requirement":run["normalized_requirement"],"tasks":list(run["tasks"].values()),"trace":run["trace"],"artifacts":run["artifacts"],"artifacts_dir":run.get("artifacts_dir"),"validation":run.get("validation"),"test_result":run.get("test_result"),"approval":run["approval"],"review_questions":run["review_questions"],"error":run.get("error")}
 def approve(self,run_id,approved,reviewer,comment=""):
  run=self.runs.get(run_id)
  if not run: raise KeyError(run_id)
  if run["status"] not in {"awaiting_approval","needs_attention"}: raise ValueError(f"Run cannot be approved from status {run['status']}.")
  run["approval"]={"status":"approved" if approved else "rejected","decision":approved,"reviewer":reviewer,"comment":comment,"timestamp":datetime.now(timezone.utc).isoformat()}; run["status"]="approved" if approved else "rejected"
  self._event(run,None,"human_approval_recorded",f"approved={approved}; reviewer={reviewer}")
  (Path(run["artifacts_dir"])/"execution_trace.json").write_text(json.dumps(run["trace"],indent=2),encoding="utf-8")
  return self.public_view(run)
