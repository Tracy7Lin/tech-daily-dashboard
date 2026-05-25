import unittest
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_response import ResearchAgentResponder


class ResearchAgentResponseTests(unittest.TestCase):
    def test_runtime_research_responder_company_position_uses_shared_policy_shape(self) -> None:
        context = {
            "question": "Google 在这个专题里处于什么位置？",
            "question_type": "company_position",
            "primary_theme": "安全与治理",
            "tracking_decision": "建议继续跟踪。",
            "theme_state": "emerging",
            "primary_source": "theme_dossier.json",
            "company_positions": {"Google": "更偏产品功能约束"},
            "entity": "Google",
            "companies": ["Google"],
        }
        responder = ResearchAgentResponder(mode="rule", client=None)
        response = responder._rule_answer(context)
        self.assertIn("目前更偏向", response["answer"])

    def test_responder_uses_llm_for_runtime_first_answer(self) -> None:
        context = {
            "question": "这个主专题现在怎么理解？",
            "question_type": "dossier_summary",
            "primary_theme": "安全与治理",
            "theme_state": "emerging",
            "tracking_decision": "继续跟踪",
            "primary_source": "theme_dossier.json",
        }
        responder = ResearchAgentResponder(mode="hybrid", client=object())

        with patch.object(
            responder,
            "_generate_llm_answer",
            return_value={
                "answer": "安全与治理仍处萌芽阶段，但值得继续跟踪。",
                "mode_used": "llm",
                "evidence_items": [],
                "grounding_mode": "grounded",
                "answer_note": "",
            },
        ):
            answer = responder.answer(context)

        self.assertEqual(answer["mode_used"], "llm")
        self.assertIn("萌芽阶段", answer["answer"])

    def test_responder_allows_general_llm_answer_with_reference_note(self) -> None:
        context = {
            "question": "什么是知识蒸馏，它通常适合用在什么场景？",
            "question_type": "out_of_scope",
            "primary_theme": "",
            "theme_state": "",
            "tracking_decision": "",
            "primary_source": "report.json",
            "grounding_mode": "general",
            "selected_context": {},
            "selected_sources": [],
        }
        responder = ResearchAgentResponder(mode="hybrid", client=object())

        with patch.object(
            responder,
            "_generate_llm_answer",
            return_value={
                "answer": "知识蒸馏通常是把大模型的行为压缩到更小模型里，常用于部署成本敏感或边缘侧推理场景。",
                "mode_used": "llm",
                "evidence_items": [],
                "grounding_mode": "general",
                "answer_note": "这部分回答不直接来自当前日报，仅供参考。",
            },
        ):
            answer = responder.answer(context)

        self.assertEqual(answer["grounding_mode"], "general")
        self.assertIn("不直接来自当前日报", answer["answer_note"])


if __name__ == "__main__":
    unittest.main()
