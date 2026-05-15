import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.theme_tracking_analysis import analyze_theme_tracking


class ThemeTrackingAnalysisTests(unittest.TestCase):
    def test_analyze_theme_tracking_selects_primary_theme_and_participating_companies(self) -> None:
        reports = [
            {
                "date": "2026-05-13",
                "hottest_topics": ["安全与治理", "模型与能力发布"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "OpenAI"},
                                "comparison_angle": "安全机制前置",
                            }
                        ],
                    }
                ],
            },
            {
                "date": "2026-05-14",
                "hottest_topics": ["安全与治理"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "OpenAI"},
                                "comparison_angle": "平台与安全控制",
                            },
                            {
                                "raw": {"company_name": "Google"},
                                "comparison_angle": "产品功能约束",
                            },
                        ],
                    }
                ],
            },
            {
                "date": "2026-05-15",
                "hottest_topics": ["安全与治理"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "Google"},
                                "comparison_angle": "产品功能落地",
                            }
                        ],
                    }
                ],
            },
        ]
        daily_briefs = [
            {"top_content_themes": ["安全与治理"]},
            {"top_content_themes": ["安全与治理"]},
            {"top_content_themes": ["安全与治理"]},
        ]
        cross_day_briefs = [
            {"warming_themes": ["安全与治理"], "steady_companies": ["OpenAI", "Google"]},
        ]

        brief = analyze_theme_tracking(
            date_range=("2026-05-13", "2026-05-15"),
            reports=reports,
            daily_briefs=daily_briefs,
            cross_day_briefs=cross_day_briefs,
        )

        self.assertIn("安全与治理", brief.candidate_themes)
        self.assertEqual(brief.primary_theme, "安全与治理")
        self.assertIn("OpenAI", brief.participating_companies)
        self.assertIn("Google", brief.participating_companies)
        self.assertTrue(brief.continue_tracking)
        self.assertTrue(brief.next_day_theme_focus)

    def test_analyze_theme_tracking_limits_candidate_pool_to_top_three_themes(self) -> None:
        reports = [
            {"date": "2026-05-15", "hottest_topics": ["A", "B", "C", "D"], "topic_clusters": []},
        ]

        brief = analyze_theme_tracking(
            date_range=("2026-05-15", "2026-05-15"),
            reports=reports,
            daily_briefs=[],
            cross_day_briefs=[],
        )

        self.assertEqual(len(brief.candidate_themes), 3)


if __name__ == "__main__":
    unittest.main()
