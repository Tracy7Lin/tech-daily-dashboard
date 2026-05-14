from __future__ import annotations

from dataclasses import dataclass

from ..llm_runtime import build_llm_client, normalize_generation_mode
from ..llm_summarizer import LLMSummarizer
from ..models import RawEntry
from ..rule_summarizer import RuleSummarizer, pick_focus
from ..settings import DEFAULT_SETTINGS, Settings


@dataclass(slots=True)
class BriefGenerationInput:
    company: str
    title: str
    summary: str
    tags: list[str]
    category: str
    url: str
    published_at: str
    raw_entry: RawEntry


@dataclass(slots=True)
class BriefGenerationOutput:
    summary_cn: str
    angle: str
    confidence: str
    mode_used: str


class BriefGenerationCapability:
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

    def generate(self, payload: BriefGenerationInput) -> BriefGenerationOutput:
        summary_cn, mode_used = self._generate_summary(payload)
        return BriefGenerationOutput(
            summary_cn=summary_cn,
            angle=pick_focus(payload.tags, payload.category),
            confidence="high",
            mode_used=mode_used,
        )

    def _generate_summary(self, payload: BriefGenerationInput) -> tuple[str, str]:
        if self.mode == "rule":
            return self.rule_summarizer.summarize(payload.raw_entry, payload.tags, payload.category), "rule"
        if self.mode == "llm":
            return self.llm_summarizer.summarize(payload.raw_entry, payload.tags, payload.category), "llm"
        if not getattr(self.llm_summarizer, "is_available", lambda: False)():
            return self.rule_summarizer.summarize(payload.raw_entry, payload.tags, payload.category), "rule"
        try:
            return self.llm_summarizer.summarize(payload.raw_entry, payload.tags, payload.category), "llm"
        except Exception:
            if not self.fallback_enabled:
                raise
            return self.rule_summarizer.summarize(payload.raw_entry, payload.tags, payload.category), "rule"
