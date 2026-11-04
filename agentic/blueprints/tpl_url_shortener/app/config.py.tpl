import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    llm_mode: str = os.getenv("ASES_LLM_MODE", "mock").lower()
    llm_base_url: str = os.getenv("ASES_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    llm_model: str = os.getenv("ASES_LLM_MODEL", "")
    llm_api_key: str = os.getenv("ASES_LLM_API_KEY", "")
    artifact_dir: str = os.getenv("ASES_ARTIFACT_DIR", "artifacts")
    max_retries: int = int(os.getenv("ASES_MAX_RETRIES", "1"))
settings = Settings()
