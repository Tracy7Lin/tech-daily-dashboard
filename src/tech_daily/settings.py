import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from .paths import DATA_DIR, SITE_DIR
from .llm_runtime import normalize_generation_mode


@dataclass(frozen=True)
class Settings:
    timezone: ZoneInfo = ZoneInfo("Asia/Shanghai")
    site_output_dir: str = str(SITE_DIR)
    data_output_dir: str = str(DATA_DIR)
    max_topic_cards: int = 5
    summary_mode: str = "hybrid"
    editorial_mode: str = "hybrid"
    llm_api_url: str = "https://api.openai.com/v1/responses"
    llm_api_key: str = ""
    llm_model: str = "gpt-5.5"
    llm_timeout_seconds: int = 20
    llm_fallback_enabled: bool = True


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    return Settings(
        summary_mode=normalize_generation_mode(os.getenv("TECH_DAILY_SUMMARY_MODE", "hybrid")),
        editorial_mode=normalize_generation_mode(os.getenv("TECH_DAILY_EDITORIAL_MODE", "hybrid")),
        llm_api_url=os.getenv("TECH_DAILY_LLM_API_URL", "https://api.openai.com/v1/responses").strip(),
        llm_api_key=os.getenv("TECH_DAILY_LLM_API_KEY", "").strip(),
        llm_model=os.getenv("TECH_DAILY_LLM_MODEL", "gpt-5.5").strip(),
        llm_timeout_seconds=int(os.getenv("TECH_DAILY_LLM_TIMEOUT_SECONDS", "20")),
        llm_fallback_enabled=_read_bool("TECH_DAILY_LLM_FALLBACK_ENABLED", True),
    )


DEFAULT_SETTINGS = load_settings()
