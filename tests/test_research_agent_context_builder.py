import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_context_builder import build_research_context
from tech_daily.research_agent_input import ResearchAgentInputs


class ResearchAgentContextBuilderTests(unittest.TestCase):
    def test_build_research_context_prioritizes_dossier_for_theme_state_questions(self) -> None:
        inputs = ResearchAgentInputs(
            report_date="2026-05-18",
            report={"headline": "headline"},
            daily_intel_brief={"editorial_signal": "today"},
            cross_day_intel_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={"primary_theme": "安全与治理"},
            theme_dossier={"primary_theme": "安全与治理", "theme_state": "emerging", "tracking_decision": "继续跟踪"},
            health_snapshot={"operator_brief": "ops"},
        )

        context = build_research_context(
            question="为什么现在是 emerging？",
            question_type="theme_state",
            entity="安全与治理",
            inputs=inputs,
        )

        self.assertEqual(context["primary_source"], "theme_dossier.json")
        self.assertEqual(context["theme_state"], "emerging")
        self.assertEqual(context["tracking_decision"], "继续跟踪")


if __name__ == "__main__":
    unittest.main()
