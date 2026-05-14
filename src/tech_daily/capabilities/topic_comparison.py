from __future__ import annotations

from dataclasses import dataclass

from ..llm_editorial import LLMEditorial
from ..llm_runtime import build_llm_client, normalize_generation_mode
from ..rule_editorial import RuleEditorial
from ..settings import DEFAULT_SETTINGS, Settings


@dataclass(slots=True)
class TopicComparisonOutput:
    summary: str
    comparison: str
    trend: str
    mode_used: str


class TopicComparisonCapability:
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

    def generate(self, topic_title: str, entries, involved_companies: list[str]) -> TopicComparisonOutput:
        summary, comparison, trend, mode_used = self._generate(topic_title, entries)
        return TopicComparisonOutput(
            summary=summary,
            comparison=comparison,
            trend=trend,
            mode_used=mode_used,
        )

    def _generate(self, topic_title: str, entries) -> tuple[str, str, str, str]:
        if self.mode == "rule":
            summary, comparison, trend = self._rule_outputs(topic_title, entries)
            return summary, comparison, trend, "rule"
        if self.mode == "llm":
            summary, comparison, trend = self._llm_outputs(topic_title, entries)
            return summary, comparison, trend, "llm"
        if not getattr(self.llm_editor, "is_available", lambda: False)():
            summary, comparison, trend = self._rule_outputs(topic_title, entries)
            return summary, comparison, trend, "rule"
        try:
            summary, comparison, trend = self._llm_outputs(topic_title, entries)
            return summary, comparison, trend, "llm"
        except Exception:
            if not self.fallback_enabled:
                raise
            summary, comparison, trend = self._rule_outputs(topic_title, entries)
            return summary, comparison, trend, "rule"

    def _rule_outputs(self, topic_title: str, entries) -> tuple[str, str, str]:
        return (
            self.rule_editor.build_topic_summary(topic_title, entries),
            self.rule_editor.build_topic_comparison(entries),
            self.rule_editor.build_topic_trend(topic_title, entries),
        )

    def _llm_outputs(self, topic_title: str, entries) -> tuple[str, str, str]:
        return (
            self.llm_editor.build_topic_summary(topic_title, entries),
            self.llm_editor.build_topic_comparison(entries),
            self.llm_editor.build_topic_trend(topic_title, entries),
        )
