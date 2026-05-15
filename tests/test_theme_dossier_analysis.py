import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.theme_dossier_analysis import analyze_theme_dossier


class ThemeDossierAnalysisTests(unittest.TestCase):
    def test_analyze_theme_dossier_builds_state_timeline_and_positions(self) -> None:
        reports = [
            {
                "date": "2026-05-13",
                "hottest_topics": ["安全与治理"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "OpenAI", "title": "OpenAI expands safety tools"},
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
                                "raw": {"company_name": "OpenAI", "title": "OpenAI adds policy controls"},
                                "comparison_angle": "平台与安全控制",
                            },
                            {
                                "raw": {"company_name": "Google", "title": "Google introduces safe defaults"},
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
                                "raw": {"company_name": "Google", "title": "Google expands education safeguards"},
                                "comparison_angle": "产品功能落地",
                            }
                        ],
                    }
                ],
            },
        ]
        theme_tracking_briefs = [
            {"primary_theme": "安全与治理", "participating_companies": ["OpenAI"]},
            {"primary_theme": "安全与治理", "participating_companies": ["OpenAI", "Google"]},
            {"primary_theme": "安全与治理", "participating_companies": ["Google"]},
        ]

        brief = analyze_theme_dossier(
            date_range=("2026-05-13", "2026-05-15"),
            reports=reports,
            daily_briefs=[],
            cross_day_briefs=[],
            theme_tracking_briefs=theme_tracking_briefs,
        )

        self.assertEqual(brief.primary_theme, "安全与治理")
        self.assertEqual(brief.theme_state, "fragmenting")
        self.assertIn("OpenAI", brief.participating_companies)
        self.assertIn("Google", brief.participating_companies)
        self.assertGreaterEqual(len(brief.timeline_events), 3)
        self.assertIn("OpenAI", brief.company_positions)
        self.assertIn("Google", brief.company_positions)
        self.assertIn("安全与治理", brief.theme_definition)
        self.assertTrue(brief.tracking_decision)

    def test_analyze_theme_dossier_marks_single_day_theme_as_emerging(self) -> None:
        reports = [
            {
                "date": "2026-05-15",
                "hottest_topics": ["AI Agent"],
                "topic_clusters": [
                    {
                        "title": "AI Agent",
                        "entries": [
                            {
                                "raw": {"company_name": "OpenAI", "title": "OpenAI ships new agent tools"},
                                "comparison_angle": "平台能力外放",
                            }
                        ],
                    }
                ],
            }
        ]
        theme_tracking_briefs = [{"primary_theme": "AI Agent", "participating_companies": ["OpenAI"]}]

        brief = analyze_theme_dossier(
            date_range=("2026-05-15", "2026-05-15"),
            reports=reports,
            daily_briefs=[],
            cross_day_briefs=[],
            theme_tracking_briefs=theme_tracking_briefs,
        )

        self.assertEqual(brief.theme_state, "emerging")
        self.assertEqual(len(brief.timeline_events), 1)


if __name__ == "__main__":
    unittest.main()
