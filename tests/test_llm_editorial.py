import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.llm_editorial import LLMEditorial
from tech_daily.models import EnrichedEntry, RawEntry
from tech_daily.rule_editorial import build_daily_headline, build_topic_comparison, build_topic_trend


class _StubClient:
    def __init__(self, payload):
        self.payload = payload

    def is_available(self) -> bool:
        return True

    def generate_json(self, **kwargs):
        return self.payload


def _entry(company_slug: str, company_name: str, title: str, summary: str, tags: list[str]) -> EnrichedEntry:
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
        tags=tags,
        category="technology",
        importance=4,
        summary_cn="summary",
        comparison_angle="angle",
    )


class LLMEditorialTests(unittest.TestCase):
    def test_build_daily_headline_removes_meta_phrasing(self) -> None:
        editorial = LLMEditorial(
            _StubClient(
                {
                    "headline": "可以看出，今天最值得关注的是模型与平台能力开始外溢到更具体的产品入口。",
                    "mentioned_companies": ["OpenAI", "Google"],
                }
            )
        )
        company_reports = [
            type("Report", (), {"company_name": "OpenAI", "has_updates": True})(),
            type("Report", (), {"company_name": "Google", "has_updates": True})(),
        ]
        topic_clusters = [
            type("Cluster", (), {"title": "模型与能力发布", "entries": [1, 2]})(),
            type("Cluster", (), {"title": "新产品发布", "entries": [1, 2]})(),
        ]

        headline = editorial.build_daily_headline(topic_clusters, company_reports, 4)
        self.assertNotIn("可以看出", headline)
        self.assertIn("模型与平台能力", headline)

    def test_build_daily_headline_uses_rule_path_for_low_entry_days(self) -> None:
        editorial = LLMEditorial(
            _StubClient(
                {
                    "headline": "OpenAI更新安全治理框架，Google发布新一代AI模型，安全与产品双线并进成今日焦点。",
                    "mentioned_companies": ["OpenAI", "Google"],
                }
            )
        )
        company_reports = [
            type("Report", (), {"company_name": "OpenAI", "has_updates": True})(),
            type("Report", (), {"company_name": "Google", "has_updates": True})(),
        ]
        topic_clusters = [
            type("Cluster", (), {"title": "安全与治理", "entries": [1]})(),
            type("Cluster", (), {"title": "新产品发布", "entries": [1]})(),
        ]

        headline = editorial.build_daily_headline(topic_clusters, company_reports, 3)
        self.assertEqual(headline, build_daily_headline(topic_clusters, company_reports, 3))

    def test_build_daily_headline_rejects_hype_language(self) -> None:
        editorial = LLMEditorial(
            _StubClient(
                {
                    "headline": "OpenAI与Google同日发布安全治理新框架，AI落地案例激增揭示行业拐点。",
                    "mentioned_companies": ["OpenAI", "Google"],
                }
            )
        )
        company_reports = [
            type("Report", (), {"company_name": "OpenAI", "has_updates": True})(),
            type("Report", (), {"company_name": "Google", "has_updates": True})(),
        ]
        topic_clusters = [
            type("Cluster", (), {"title": "安全与治理", "entries": [1, 2]})(),
            type("Cluster", (), {"title": "客户落地案例", "entries": [1, 2]})(),
        ]

        with self.assertRaises(ValueError):
            editorial.build_daily_headline(topic_clusters, company_reports, 4)

    def test_build_topic_summary_uses_rule_path_for_single_company_topic(self) -> None:
        editorial = LLMEditorial(
            _StubClient(
                {
                    "summary": (
                        "OpenAI发布了关于企业如何规模化AI的指导，强调从早期实验转向信任、"
                        "治理、工作流设计和质量管控以实现复合影响。这表明安全与治理已成为"
                        "企业AI部署的核心。"
                    )
                }
            )
        )
        entries = [
            _entry("openai", "OpenAI", "How enterprises are scaling AI", "AI governance at scale.", ["ai", "enterprise", "safety"]),
        ]

        from tech_daily.rule_editorial import build_topic_summary

        summary = editorial.build_topic_summary("安全与治理", entries)
        self.assertEqual(summary, build_topic_summary("安全与治理", entries))

    def test_build_topic_comparison_rejects_empty_generic_output(self) -> None:
        editorial = LLMEditorial(_StubClient({"comparison": "根据提供信息，不同公司都在推进相关工作。", "mentioned_companies": []}))
        entries = [
            _entry("openai", "OpenAI", "API update", "Model update for developers.", ["ai", "model", "developer"]),
            _entry("google", "Google", "Workspace update", "New AI features for users.", ["ai", "product"]),
        ]

        with self.assertRaises(ValueError):
            editorial.build_topic_comparison(entries)

    def test_build_topic_comparison_uses_rule_path_for_single_company_topic(self) -> None:
        editorial = LLMEditorial(
            _StubClient(
                {
                    "comparison": "OpenAI与Google形成差异。",
                    "mentioned_companies": ["OpenAI", "Google"],
                }
            )
        )
        entries = [
            _entry("openai", "OpenAI", "API update", "Model update for developers.", ["ai", "model", "developer"]),
        ]

        comparison = editorial.build_topic_comparison(entries)
        self.assertEqual(comparison, build_topic_comparison(entries))

    def test_build_topic_comparison_rejects_unlisted_companies(self) -> None:
        editorial = LLMEditorial(
            _StubClient(
                {
                    "comparison": "OpenAI强调治理，而Meta更重视开放生态。",
                    "mentioned_companies": ["OpenAI", "Meta"],
                }
            )
        )
        entries = [
            _entry("openai", "OpenAI", "API update", "Model update for developers.", ["ai", "model", "developer"]),
            _entry("google", "Google", "Workspace update", "New AI features for users.", ["ai", "product"]),
        ]

        with self.assertRaises(ValueError):
            editorial.build_topic_comparison(entries)

    def test_build_topic_trend_uses_rule_path_for_single_company_topic(self) -> None:
        editorial = LLMEditorial(
            _StubClient({"trend": "企业AI规模化正从早期实验转向以信任、治理和安全性为基石的系统化实践。"})
        )
        entries = [
            _entry("openai", "OpenAI", "How enterprises are scaling AI", "AI governance at scale.", ["ai", "enterprise", "safety"]),
        ]

        trend = editorial.build_topic_trend("安全与治理", entries)
        self.assertEqual(trend, build_topic_trend("安全与治理", entries))


if __name__ == "__main__":
    unittest.main()
