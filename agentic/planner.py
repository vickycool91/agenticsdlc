from dataclasses import dataclass, asdict

URL_REQUIREMENT = "Build a scalable URL shortener service with APIs, persistence, and analytics."
@dataclass
class Task:
    id: str
    name: str
    agent: str
    depends_on: list[str]
    status: str = "pending"
    attempts: int = 0
    output: dict | None = None
    error: str | None = None
    def view(self): return asdict(self)

def detect_scenario(requirement: str, requested: str, repository_context: str) -> str:
    if requested != "auto": return requested
    r = requirement.lower()
    if any(w in r for w in ["existing", "refactor", "bug", "enhance", "legacy", "endpoint", "repository"]) or repository_context.strip(): return "brownfield"
    if any(w in r for w in ["faster", "better", "improve", "reliable", "optimize"]) and not any(w in r for w in ["build", "create", "implement", "add"]): return "ambiguous"
    return "greenfield"

def normalize(requirement: str, scenario: str, repository_context: str = "") -> dict:
    req = " ".join(requirement.strip().split()); low = req.lower(); missing = []
    if any(w in low for w in ["scalable", "fast", "high performance"]): missing += ["target throughput and latency SLOs", "expected peak traffic and growth"]
    if any(w in low for w in ["analytics", "metrics", "reporting"]): missing += ["analytics event definitions, retention, and privacy requirements"]
    if scenario == "ambiguous": missing += ["measurable acceptance criteria", "scope and priority", "constraints and definition of done"]
    if scenario == "brownfield" and not repository_context.strip(): missing += ["repository structure, current API contract, and relevant tests"]
    return {"raw_requirement": requirement, "normalized_problem": req, "scenario": scenario,
      "assumptions": ["Deliver a reviewable prototype, not an automatically deployed production service.", "Generated artifacts require human review before merge or release."],
      "ambiguities": list(dict.fromkeys(missing)), "repository_context_provided": bool(repository_context.strip())}

def build_tasks(scenario: str) -> list[Task]:
    tasks = [Task("T1", "Normalize requirement and record assumptions", "requirement", []),
             Task("T2", "Design architecture and data flow", "architecture", ["T1"])]
    if scenario == "brownfield":
        tasks.append(Task("T3", "Analyze impacted modules, APIs, and data flows", "impact", ["T1"]))
        code_deps = ["T2", "T3"]
    else: code_deps = ["T2"]
    tasks.extend([Task("T4", "Generate implementation and API contract", "code", code_deps),
      Task("T5", "Generate unit, integration, and contract tests", "tests", ["T4"]),
      Task("T6", "Generate implementation and operator documentation", "docs", ["T2", "T4"]),
      Task("T7", "Review risks and validation strategy", "risk", ["T2", "T4", "T5", "T6"]),
      Task("T8", "Validate artifacts and assemble engineering summary", "validation", ["T4", "T5", "T6", "T7"])])
    return tasks
