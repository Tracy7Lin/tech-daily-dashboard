from __future__ import annotations

from dataclasses import dataclass

from ..llm_editorial import LLMEditorial
from ..llm_runtime import build_llm_client, normalize_generation_mode
from ..rule_editorial import RuleEditorial
from ..settings import DEFAULT_SETTINGS, Settings


@dataclass(slots=True)
class DailyEditorialOutput:
    headline: str
    brief: str
    mode_used: str


class DailyEditorialCapability:
    def __init__(
        self,
        mode: str | None = None,
        fallback_enabled: bool | None = None,
        rule_editor: RuleEditorial | None = None,
        llm_editor=None,
        settings: Settings | None = None,
    ) -> None:
        runtime = settings or DEFAULT_SETTINGS
        self.mode = normalize_generation_mode(mode or runtime.editorial_mode)
        self.fallback_enabled = runtime.llm_fallback_enabled if fallback_enabled is None else fallback_enabled
        self.rule_editor = rule_editor or RuleEditorial()
        self.llm_editor = llm_editor or LLMEditorial(build_llm_client(runtime))

    def generate(self, report_date: str, topic_clusters, company_reports, total_entries: int) -> DailyEditorialOutput:
        headline, mode_used = self._generate_headline(topic_clusters, company_reports, total_entries)
        return DailyEditorialOutput(
            headline=headline,
            brief=headline,
            mode_used=mode_used,
        )

    def _generate_headline(self, topic_clusters, company_reports, total_entries: int) -> tuple[str, str]:
        if self.mode == "rule":
            return self.rule_editor.build_daily_headline(topic_clusters, company_reports, total_entries), "rule"
        if self.mode == "llm":
            return self.llm_editor.build_daily_headline(topic_clusters, company_reports, total_entries), "llm"
        if not getattr(self.llm_editor, "is_available", lambda: False)():
            return self.rule_editor.build_daily_headline(topic_clusters, company_reports, total_entries), "rule"
        try:
            return self.llm_editor.build_daily_headline(topic_clusters, company_reports, total_entries), "llm"
        except Exception:
            if not self.fallback_enabled:
                raise
            return self.rule_editor.build_daily_headline(topic_clusters, company_reports, total_entries), "rule"
