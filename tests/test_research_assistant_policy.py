import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_assistant_policy import (
    build_company_position_answer,
    build_theme_state_answer,
    finalize_answer_payload,
)


class ResearchAssistantPolicyTests(unittest.TestCase):
    def test_build_theme_state_answer_includes_state_summary_and_decision(self) -> None:
        answer = build_theme_state_answer(
            primary_theme="安全与治理",
            theme_state="emerging",
            summary="这个主题已经形成持续信号。",
            tracking_decision="建议继续跟踪。",
        )
        self.assertIn("emerging", answer)
        self.assertIn("持续信号", answer)
        self.assertIn("建议继续跟踪", answer)

    def test_build_company_position_answer_mentions_theme_and_position(self) -> None:
        answer = build_company_position_answer(
            primary_theme="安全与治理",
            company="Google",
            position="更偏产品功能约束",
            tracking_decision="建议继续跟踪。",
        )
        self.assertIn("Google", answer)
        self.assertIn("安全与治理", answer)
        self.assertIn("更偏产品功能约束", answer)

    def test_finalize_answer_payload_rebuilds_evidence_points_from_items(self) -> None:
        payload = finalize_answer_payload(
            answer="结论",
            question_type="theme_state",
            resolved_theme="安全与治理",
            resolved_company="",
            sources_used=["theme_dossier.json"],
            evidence_items=[
                {
                    "source": "theme_dossier.json",
                    "label": "专题档案",
                    "detail": "当前主题阶段为 emerging。",
                    "reference": "theme-dossier",
                }
            ],
            follow_up_suggestions=["为什么现在是 emerging？"],
            mode_used="rule",
        )
        self.assertEqual(payload["evidence_points"], ["当前主题阶段为 emerging。"])


if __name__ == "__main__":
    unittest.main()
