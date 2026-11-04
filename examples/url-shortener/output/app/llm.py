import json
import urllib.request
from .config import settings

class LLMError(RuntimeError):
    pass

class ModelAdapter:
    """Provider-independent adapter for OpenAI-compatible Chat Completions APIs."""
    def __init__(self, mode: str = "mock"):
        self.mode = mode
    def complete_json(self, system: str, user: str) -> dict:
        if self.mode == "mock":
            return {"mode": "mock", "note": "Deterministic mock adapter; orchestration and validation are real."}
        if not settings.llm_api_key or not settings.llm_model:
            raise LLMError("Remote mode requires ASES_LLM_API_KEY and ASES_LLM_MODEL.")
        payload = {"model": settings.llm_model, "temperature": 0.1,
                   "messages": [{"role": "system", "content": system + "\nReturn a valid JSON object only."},
                                {"role": "user", "content": user}],
                   "response_format": {"type": "json_object"}}
        req = urllib.request.Request(settings.llm_base_url + "/chat/completions", data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.llm_api_key}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                body = json.loads(response.read().decode())
            parsed = json.loads(body["choices"][0]["message"]["content"])
            if not isinstance(parsed, dict):
                raise ValueError("Model response was not a JSON object.")
            return parsed
        except Exception as exc:
            raise LLMError(f"LLM request/response failed: {type(exc).__name__}: {exc}") from exc
