from __future__ import annotations

from .capabilities.brief_generation import BriefGenerationCapability, BriefGenerationInput
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
        self.capability = BriefGenerationCapability(
            mode=self.mode,
            fallback_enabled=self.fallback_enabled,
            rule_summarizer=self.rule_summarizer,
            llm_summarizer=self.llm_summarizer,
            settings=runtime,
        )

    def summarize(self, entry: RawEntry, tags: list[str], category: str) -> str:
        payload = BriefGenerationInput(
            company=entry.company_name,
            title=entry.title,
            summary=entry.summary,
            tags=tags,
            category=category,
            url=entry.url,
            published_at=entry.published_at,
            raw_entry=entry,
        )
        return self.capability.generate(payload).summary_cn
