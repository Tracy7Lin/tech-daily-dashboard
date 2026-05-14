from __future__ import annotations

from .capabilities.daily_editorial import DailyEditorialCapability
from .capabilities.topic_comparison import TopicComparisonCapability
from .llm_runtime import build_llm_client, normalize_generation_mode
from .llm_editorial import LLMEditorial
from .rule_editorial import (
    RuleEditorial,
    angle_for_entry,
)
from .settings import DEFAULT_SETTINGS, Settings


class EditorialService:
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
        self.topic_capability = TopicComparisonCapability(
            mode=self.mode,
            fallback_enabled=self.fallback_enabled,
            rule_editor=self.rule_editor,
            llm_editor=self.llm_editor,
            settings=runtime,
        )
        self.daily_capability = DailyEditorialCapability(
            mode=self.mode,
            fallback_enabled=self.fallback_enabled,
            rule_editor=self.rule_editor,
            llm_editor=self.llm_editor,
            settings=runtime,
        )

    def build_daily_headline(self, topic_clusters, company_reports, total_entries: int) -> str:
        return self.daily_capability.generate(
            report_date="",
            topic_clusters=topic_clusters,
            company_reports=company_reports,
            total_entries=total_entries,
        ).headline

    def build_topic_summary(self, title, entries):
        companies = sorted({entry.raw.company_name for entry in entries})
        return self.topic_capability.generate(title, entries, companies).summary

    def build_topic_comparison(self, entries):
        companies = sorted({entry.raw.company_name for entry in entries})
        return self.topic_capability.generate("", entries, companies).comparison

    def build_topic_trend(self, title, entries):
        companies = sorted({entry.raw.company_name for entry in entries})
        return self.topic_capability.generate(title, entries, companies).trend


DEFAULT_EDITORIAL_SERVICE = EditorialService()


def build_daily_headline(topic_clusters, company_reports, total_entries: int) -> str:
    return DEFAULT_EDITORIAL_SERVICE.build_daily_headline(topic_clusters, company_reports, total_entries)


def build_topic_summary(title, entries):
    return DEFAULT_EDITORIAL_SERVICE.build_topic_summary(title, entries)


def build_topic_comparison(entries):
    return DEFAULT_EDITORIAL_SERVICE.build_topic_comparison(entries)


def build_topic_trend(title, entries):
    return DEFAULT_EDITORIAL_SERVICE.build_topic_trend(title, entries)


__all__ = [
    "EditorialService",
    "angle_for_entry",
    "build_daily_headline",
    "build_topic_summary",
    "build_topic_comparison",
    "build_topic_trend",
]
