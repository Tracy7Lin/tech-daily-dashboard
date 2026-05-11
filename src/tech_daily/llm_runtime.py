from __future__ import annotations

from .llm_client import LLMClient

VALID_GENERATION_MODES = {"rule", "llm", "hybrid"}


def normalize_generation_mode(value: str | None, default: str = "hybrid") -> str:
    normalized = (value or "").strip().lower()
    if normalized in VALID_GENERATION_MODES:
        return normalized
    return default


def build_llm_client(settings) -> LLMClient:
    return LLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
