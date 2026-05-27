import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_context_builder import build_research_context
from tech_daily.research_agent_input import ResearchAgentInputs


class ResearchAgentContextBuilderTests(unittest.TestCase):
    def test_builder_uses_project_skill_and_selected_sources_for_dossier_question(self) -> None:
        inputs = ResearchAgentInputs(
            report_date="2026-05-18",
            report={
                "headline": "headline",
                "company_reports": [
                    {
                        "company_name": "Google",
                        "entries": [
                            {
                                "summary_cn": "Google 正在把安全与治理推向产品体系。",
                                "comparison_angle": "safety",
                                "raw": {"title": "Google expands model safeguards"},
                            }
                        ],
                    }
                ],
            },
            daily_intel_brief={"editorial_signal": "signal"},
            cross_day_intel_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={"primary_theme": "安全与治理"},
            theme_dossier={
                "primary_theme": "安全与治理",
                "theme_state": "emerging",
                "company_positions": {"Google": "生态整合"},
                "timeline_events": [{"date": "2026-05-18", "company": "Google", "title": "Google expands model safeguards"}],
            },
            health_snapshot={"operator_brief": "ops"},
        )

        context = build_research_context(
            "Google 在这个专题里处于什么位置？",
            "company_position",
            "Google",
            inputs,
        )

        self.assertEqual(context["primary_source"], "theme_dossier.json")
        self.assertIn("theme_dossier.json", context["selected_sources"])
        self.assertTrue(context["research_skill_text"])
        self.assertTrue(context["knowledge_sources_text"])
        self.assertTrue(context["question_patterns_text"])
        self.assertIn("theme_dossier.json", context["selected_context"])
        self.assertIsInstance(context["selected_context"]["theme_dossier.json"], list)
        self.assertTrue(context["selected_context"]["theme_dossier.json"][0]["text"])
        self.assertIn("Google", context["selected_context"]["theme_dossier.json"][0]["text"])
        self.assertIn("selected_blocks", context)
        self.assertGreater(len(context["selected_blocks"]), 0)

    def test_builder_marks_general_mode_when_daily_knowledge_has_no_direct_match(self) -> None:
        inputs = ResearchAgentInputs(
            report_date="2026-05-25",
            report={"headline": "headline"},
            daily_intel_brief={"editorial_signal": "signal"},
            cross_day_intel_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={"primary_theme": "安全与治理"},
            theme_dossier={"primary_theme": "安全与治理", "theme_state": "emerging"},
            health_snapshot={"operator_brief": "ops"},
        )

        context = build_research_context(
            "什么是知识蒸馏，它通常适合用在什么场景？",
            "out_of_scope",
            "",
            inputs,
        )

        self.assertEqual(context["grounding_mode"], "general")
        self.assertEqual(context["selected_sources"], [])
        self.assertEqual(context["selected_context"], {})

    def test_builder_prefers_structured_timeline_and_position_blocks_for_dossier_queries(self) -> None:
        inputs = ResearchAgentInputs(
            report_date="2026-05-18",
            report={"headline": "headline"},
            daily_intel_brief={"editorial_signal": "signal"},
            cross_day_intel_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={"primary_theme": "安全与治理"},
            theme_dossier={
                "primary_theme": "安全与治理",
                "theme_state": "active",
                "company_positions": {"OpenAI": "安全机制前置"},
                "timeline_events": [{"date": "2026-05-18", "company": "OpenAI", "title": "OpenAI expands governance controls", "why_it_matters": "说明主题正在从原则走向执行。"}],
            },
            health_snapshot={"operator_brief": "ops"},
        )

        context = build_research_context(
            "最近几天关键时间线说明了什么？",
            "timeline_focus",
            "",
            inputs,
        )

        self.assertEqual(context["primary_source"], "theme_dossier.json")
        self.assertEqual(context["selected_blocks"][0]["kind"], "timeline_event")
        self.assertIn("说明主题正在从原则走向执行", context["selected_blocks"][0]["text"])


if __name__ == "__main__":
    unittest.main()
