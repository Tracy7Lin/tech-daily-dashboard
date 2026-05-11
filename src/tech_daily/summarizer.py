from __future__ import annotations

from .llm_runtime import build_llm_client, normalize_generation_mode
from .llm_summarizer import LLMSummarizer
from .models import RawEntry
from .rule_summarizer import RuleSummarizer, build_summary
from .settings import DEFAULT_SETTINGS, Settings


class Summarizer:
    def __init__(
        self,
        mode: str | None = None,
        fallback_enabled: bool | None = None,
        rule_summarizer: RuleSummarizer | None = None,
        llm_summarizer=None,
        settings: Settings | None = None,
    ) -> None:
        runtime = settings or DEFAULT_SETTINGS
        self.mode = normalize_generation_mode(mode or runtime.summary_mode)
        self.fallback_enabled = runtime.llm_fallback_enabled if fallback_enabled is None else fallback_enabled
        self.rule_summarizer = rule_summarizer or RuleSummarizer()
        self.llm_summarizer = llm_summarizer or LLMSummarizer(build_llm_client(runtime))

    def summarize(self, entry: RawEntry, tags: list[str], category: str) -> str:
        if self.mode == "rule":
            return self.rule_summarizer.summarize(entry, tags, category)
        if self.mode == "llm":
            return self._summarize_with_llm(entry, tags, category)
        return self._summarize_hybrid(entry, tags, category)

    def _summarize_with_llm(self, entry: RawEntry, tags: list[str], category: str) -> str:
        return self.llm_summarizer.summarize(entry, tags, category)

    def _summarize_hybrid(self, entry: RawEntry, tags: list[str], category: str) -> str:
        if not getattr(self.llm_summarizer, "is_available", lambda: False)():
            return self.rule_summarizer.summarize(entry, tags, category)
        try:
            return self.llm_summarizer.summarize(entry, tags, category)
        except Exception:
            if not self.fallback_enabled:
                raise
            return self.rule_summarizer.summarize(entry, tags, category)
