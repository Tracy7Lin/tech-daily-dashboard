import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from .paths import DATA_DIR, PROJECT_ROOT, SITE_DIR
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
    llm_model: str = "deepseekv4"
    llm_timeout_seconds: int = 20
    llm_fallback_enabled: bool = True


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_dotenv(env_path: Path | None) -> dict[str, str]:
    target = env_path or (PROJECT_ROOT / ".env")
    if not target.exists():
        return {}

    values: dict[str, str] = {}
    for line in target.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _read_value(name: str, default: str, dotenv_values: dict[str, str]) -> str:
    return os.getenv(name, dotenv_values.get(name, default)).strip()


def load_settings(env_path: Path | None = None) -> Settings:
    dotenv_values = _read_dotenv(env_path)
    return Settings(
        summary_mode=normalize_generation_mode(_read_value("TECH_DAILY_SUMMARY_MODE", "hybrid", dotenv_values)),
        editorial_mode=normalize_generation_mode(_read_value("TECH_DAILY_EDITORIAL_MODE", "hybrid", dotenv_values)),
        llm_api_url=_read_value("TECH_DAILY_LLM_API_URL", "https://api.openai.com/v1/responses", dotenv_values),
        llm_api_key=_read_value("TECH_DAILY_LLM_API_KEY", "", dotenv_values),
        llm_model=_read_value("TECH_DAILY_LLM_MODEL", "deepseekv4", dotenv_values),
        llm_timeout_seconds=int(_read_value("TECH_DAILY_LLM_TIMEOUT_SECONDS", "20", dotenv_values)),
        llm_fallback_enabled=_read_bool("TECH_DAILY_LLM_FALLBACK_ENABLED", True)
        if "TECH_DAILY_LLM_FALLBACK_ENABLED" in os.environ
        else dotenv_values.get("TECH_DAILY_LLM_FALLBACK_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"},
    )


DEFAULT_SETTINGS = load_settings()
