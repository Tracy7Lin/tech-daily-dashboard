import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.agent_analysis import analyze_daily_intel


class AgentAnalysisTests(unittest.TestCase):
    def test_analyze_daily_intel_builds_structured_brief(self) -> None:
        report = {
            "date": "2026-05-14",
            "headline": "today headline",
            "hottest_topics": ["安全与治理", "模型与能力发布"],
            "active_companies": ["OpenAI", "Google"],
        }
        snapshot = {
            "ops_status_analysis": {
                "operator_brief": "当前优先处理 tesla；最近已恢复 alibaba。",
                "high_priority": [{"company_slug": "tesla"}],
                "recently_recovered": [{"company_slug": "alibaba"}],
            }
        }

        brief = analyze_daily_intel(report, snapshot)

        self.assertEqual(brief.report_date, "2026-05-14")
        self.assertTrue(brief.editorial_signal)
        self.assertTrue(brief.ops_signal)
        self.assertIn("安全与治理", brief.top_content_themes)
        self.assertIn("tesla", "".join(brief.source_risks))


if __name__ == "__main__":
    unittest.main()
