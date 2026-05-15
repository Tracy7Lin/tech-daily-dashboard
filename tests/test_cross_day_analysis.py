import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.cross_day_analysis import analyze_cross_day_intel


class CrossDayAnalysisTests(unittest.TestCase):
    def test_analyze_cross_day_intel_builds_structured_brief(self) -> None:
        reports = [
            {"date": "2026-05-13", "hottest_topics": ["安全与治理"], "active_companies": ["OpenAI", "Google"]},
            {"date": "2026-05-14", "hottest_topics": ["安全与治理", "模型与能力发布"], "active_companies": ["OpenAI"]},
            {"date": "2026-05-15", "hottest_topics": ["模型与能力发布"], "active_companies": ["OpenAI", "Anthropic"]},
        ]
        snapshots = [
            {"report_date": "2026-05-13", "high_priority_runtime_issues": [{"company_slug": "tesla"}], "recently_recovered_runtime_issues": []},
            {"report_date": "2026-05-14", "high_priority_runtime_issues": [{"company_slug": "tesla"}], "recently_recovered_runtime_issues": [{"company_slug": "alibaba"}]},
            {"report_date": "2026-05-15", "high_priority_runtime_issues": [{"company_slug": "tesla"}], "recently_recovered_runtime_issues": [{"company_slug": "xiaomi"}]},
        ]

        brief = analyze_cross_day_intel(
            date_range=("2026-05-13", "2026-05-15"),
            reports=reports,
            intel_briefs=[],
            snapshots=snapshots,
        )

        self.assertEqual(brief.date_range, ("2026-05-13", "2026-05-15"))
        self.assertIn("安全与治理", brief.warming_themes)
        self.assertIn("OpenAI", brief.steady_companies)
        self.assertIn("tesla", brief.persistent_source_risks)
        self.assertTrue(brief.next_day_focus)

    def test_analyze_cross_day_intel_marks_single_day_entities_as_cooling_or_swing(self) -> None:
        reports = [
            {"date": "2026-05-14", "hottest_topics": ["安全与治理"], "active_companies": ["OpenAI"]},
            {"date": "2026-05-15", "hottest_topics": ["客户落地案例"], "active_companies": ["Anthropic"]},
        ]

        brief = analyze_cross_day_intel(
            date_range=("2026-05-14", "2026-05-15"),
            reports=reports,
            intel_briefs=[],
            snapshots=[],
        )

        self.assertIn("客户落地案例", brief.cooling_themes)
        self.assertIn("Anthropic", brief.swing_companies)


if __name__ == "__main__":
    unittest.main()
