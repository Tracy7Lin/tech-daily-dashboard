import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.capabilities.topic_comparison import TopicComparisonCapability
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


class TopicComparisonCapabilityTests(unittest.TestCase):
    def test_generate_returns_structured_summary_comparison_and_trend(self) -> None:
        capability = TopicComparisonCapability(mode="rule")
        entries = [
            _entry("openai", "OpenAI", "Trusted Contact", summary="Safety update", tags=["safety", "consumer"]),
            _entry("google", "Google", "Account safety tools", summary="Security update", tags=["safety"]),
        ]

        result = capability.generate(
            topic_title="安全与治理",
            entries=entries,
            involved_companies=["OpenAI", "Google"],
        )

        self.assertTrue(result.summary)
        self.assertTrue(result.comparison)
        self.assertTrue(result.trend)
        self.assertEqual(result.mode_used, "rule")


if __name__ == "__main__":
    unittest.main()
