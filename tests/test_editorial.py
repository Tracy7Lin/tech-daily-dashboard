import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.editorial import (
    build_daily_headline,
    build_topic_comparison,
    build_topic_summary,
    build_topic_trend,
)
from tech_daily.models import EnrichedEntry, RawEntry


def _entry(
    company_slug: str,
    company_name: str,
    title: str,
    *,
    summary: str = "",
    tags: list[str] | None = None,
    category: str = "technology",
    importance: int = 4,
) -> EnrichedEntry:
    return EnrichedEntry(
        raw=RawEntry(
            company_slug=company_slug,
            company_name=company_name,
            source_label="news",
            title=title,
            url=f"https://example.com/{company_slug}",
            summary=summary,
            published_at="Thu, 07 May 2026 10:00:00 GMT",
        ),
        tags=tags or ["ai"],
        category=category,
        importance=importance,
        summary_cn="summary",
        comparison_angle="angle",
    )


class EditorialTests(unittest.TestCase):
    def test_build_daily_headline_reads_like_editorial_signal(self) -> None:
        clusters = [
            type("Cluster", (), {"title": "安全与治理", "entries": [1, 2, 3]})(),
            type("Cluster", (), {"title": "模型与能力发布", "entries": [1, 2]})(),
        ]
        company_reports = [
            type("Report", (), {"company_name": "OpenAI", "has_updates": True})(),
            type("Report", (), {"company_name": "Google", "has_updates": True})(),
            type("Report", (), {"company_name": "Apple", "has_updates": True})(),
        ]
        headline = build_daily_headline(clusters, company_reports, 6)
        self.assertIn("今天最值得关注的信号", headline)
        self.assertIn("安全与治理", headline)
        self.assertIn("OpenAI", headline)

    def test_build_topic_summary_names_actual_focus(self) -> None:
        entries = [
            _entry(
                "openai",
                "OpenAI",
                "Introducing Trusted Contact in ChatGPT",
                summary="Optional safety feature for ChatGPT users.",
                tags=["safety", "consumer"],
            ),
            _entry(
                "google",
                "Google",
                "5 helpful tools from Google to keep your accounts safe",
                summary="Security and account protection updates for Google users.",
                tags=["safety"],
                category="general",
            ),
        ]
        summary = build_topic_summary("安全与治理", entries)
        self.assertIn("安全与治理", summary)
        self.assertIn("OpenAI", summary)
        self.assertIn("Google", summary)

    def test_build_topic_comparison_avoids_raw_internal_category_names(self) -> None:
        entries = [
            _entry(
                "openai",
                "OpenAI",
                "Parloa builds service agents customers want to talk to",
                summary="Customer service agents for enterprise deployment.",
                tags=["ai", "enterprise", "customer", "model"],
            ),
            _entry(
                "amazon",
                "Amazon",
                "Amazon CEO Andy Jassy explains how Amazon keeps retail prices low",
                summary="Lower costs for customers.",
                tags=["customer"],
                category="general",
            ),
        ]
        comparison = build_topic_comparison(entries)
        self.assertIn("OpenAI", comparison)
        self.assertIn("Amazon", comparison)
        self.assertNotIn("general", comparison)
        self.assertNotIn("technology", comparison)
        self.assertNotIn("product", comparison)

    def test_build_topic_trend_reads_like_industry_takeaway(self) -> None:
        entries = [
            _entry(
                "openai",
                "OpenAI",
                "Advancing voice intelligence with new models in the API",
                summary="New models in the API for voice experiences.",
                tags=["ai", "model", "developer"],
            ),
            _entry(
                "google",
                "Google",
                "New AI-powered bidding and budgeting innovations in Search and Shopping",
                summary="AI tools for productized marketing workflows.",
                tags=["ai", "product"],
                category="product",
            ),
        ]
        trend = build_topic_trend("模型与能力发布", entries)
        self.assertIn("说明", trend)
        self.assertNotIn("正在继续演进", trend)

    def test_build_topic_summary_uses_hardware_specific_angle_instead_of_generic_fallback(self) -> None:
        entries = [
            _entry(
                "nvidia",
                "NVIDIA",
                "Linked and Loaded: Gaijin Single Sign-On Now Available on GeForce NOW",
                summary="Single sign-on for gaming devices and services.",
                tags=["enterprise", "hardware"],
                category="product",
                importance=2,
            ),
            _entry(
                "apple",
                "Apple",
                "AI meets accessibility in this year’s Swift Student Challenge",
                summary="AI features in accessibility workflows.",
                tags=["ai"],
                category="technology",
                importance=2,
            ),
        ]
        summary = build_topic_summary("其他重要动态", entries)
        self.assertIn("终端或设备入口探索", summary)
        self.assertNotIn("重点方向仍在继续试探", summary)


if __name__ == "__main__":
    unittest.main()
