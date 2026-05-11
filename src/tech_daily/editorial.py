from __future__ import annotations

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

    def build_daily_headline(self, topic_clusters, company_reports, total_entries: int) -> str:
        return self._call("build_daily_headline", topic_clusters, company_reports, total_entries)

    def build_topic_summary(self, title, entries):
        return self._call("build_topic_summary", title, entries)

    def build_topic_comparison(self, entries):
        return self._call("build_topic_comparison", entries)

    def build_topic_trend(self, title, entries):
        return self._call("build_topic_trend", title, entries)

    def _call(self, method_name: str, *args):
        if self.mode == "rule":
            return getattr(self.rule_editor, method_name)(*args)
        if self.mode == "llm":
            return getattr(self.llm_editor, method_name)(*args)
        if not getattr(self.llm_editor, "is_available", lambda: False)():
            return getattr(self.rule_editor, method_name)(*args)
        try:
            return getattr(self.llm_editor, method_name)(*args)
        except Exception:
            if not self.fallback_enabled:
                raise
            return getattr(self.rule_editor, method_name)(*args)


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
