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

    def test_generate_llm_answer_uses_selected_blocks_as_primary_rag_context(self) -> None:
        captured: dict[str, str] = {}

        class FakeClient:
            def is_available(self) -> bool:
                return True

            def generate_json(self, *, instructions: str, input_text: str, schema_name: str, schema: dict) -> dict:
                captured["instructions"] = instructions
                captured["input_text"] = input_text
                return {
                    "answer": "这个专题目前仍在升温，Google 的动作说明它正在从原则走向执行。",
                    "evidence_items": [],
                    "evidence_points": ["2026-05-18 Google expands model safeguards"],
                    "follow_up_suggestions": ["为什么现在是 emerging？"],
                    "answer_note": "这部分判断结合了当前日报内容与模型推断。",
                }

        context = {
            "question": "最近几天关键时间线说明了什么？",
            "question_type": "timeline_focus",
            "primary_theme": "安全与治理",
            "tracking_decision": "建议继续跟踪。",
            "theme_state": "emerging",
            "primary_source": "theme_dossier.json",
            "grounding_mode": "hybrid",
            "selected_sources": ["theme_dossier.json"],
            "selected_blocks": [
                {
                    "source": "theme_dossier.json",
                    "kind": "timeline_event",
                    "block_id": "timeline-0",
                    "text": "2026-05-18 Google expands model safeguards 说明主题正在从原则走向执行。",
                }
            ],
            "selected_context": {
                "theme_dossier.json": [
                    {
                        "source": "theme_dossier.json",
                        "kind": "timeline_event",
                        "block_id": "timeline-0",
                        "text": "2026-05-18 Google expands model safeguards 说明主题正在从原则走向执行。",
                    }
                ]
            },
            "question_understanding": {
                "question_type": "timeline_focus",
                "entity": "",
                "explanation_dimension": "evolution",
                "resolved_theme": "安全与治理",
                "resolved_company": "",
                "assumption_used": "",
            },
            "research_skill_text": "skill",
            "knowledge_sources_text": "sources",
            "question_patterns_text": "patterns",
        }

        responder = ResearchAgentResponder(mode="hybrid", client=FakeClient())
        answer = responder.answer(context)

        self.assertEqual(answer["mode_used"], "llm")
        self.assertIn("选中证据块", captured["input_text"])
        self.assertIn("timeline_event", captured["input_text"])
        self.assertIn("grounding / evidence layer", captured["instructions"])


if __name__ == "__main__":
    unittest.main()
