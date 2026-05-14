import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.capabilities.daily_editorial import DailyEditorialCapability


class DailyEditorialCapabilityTests(unittest.TestCase):
    def test_generate_returns_headline_and_brief(self) -> None:
        capability = DailyEditorialCapability(mode="rule")
        topic_clusters = [
            type("Cluster", (), {"title": "安全与治理", "entries": [1, 2, 3]})(),
            type("Cluster", (), {"title": "模型与能力发布", "entries": [1, 2]})(),
        ]
        company_reports = [
            type("Report", (), {"company_name": "OpenAI", "has_updates": True})(),
            type("Report", (), {"company_name": "Google", "has_updates": True})(),
        ]

        result = capability.generate(
            report_date="2026-05-14",
            topic_clusters=topic_clusters,
            company_reports=company_reports,
            total_entries=4,
        )

        self.assertTrue(result.headline)
        self.assertTrue(result.brief)
        self.assertEqual(result.mode_used, "rule")


if __name__ == "__main__":
    unittest.main()
