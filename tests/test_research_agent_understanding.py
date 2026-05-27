import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_understanding import resolve_runtime_question_understanding


class ResearchAgentUnderstandingTests(unittest.TestCase):
    def test_resolve_runtime_question_understanding_falls_back_to_rule_when_client_unavailable(self) -> None:
        understanding = resolve_runtime_question_understanding(
            "什么是知识蒸馏，它通常适合用在什么场景？",
            ["Google"],
            "安全与治理",
            mode="hybrid",
            client=None,
        )
        self.assertEqual(understanding.question_scope, "general")
        self.assertTrue(understanding.needs_general_knowledge)

    def test_resolve_runtime_question_understanding_uses_llm_payload_when_valid(self) -> None:
        class FakeClient:
            def is_available(self) -> bool:
                return True

            def generate_json(self, **kwargs):
                return {
                    "question_type": "company_position",
                    "question_scope": "company",
                    "explanation_dimension": "comparison",
                    "entity": "Google",
                    "target_company": "Google",
                    "target_theme": "安全与治理",
                    "needs_general_knowledge": False,
                    "requested_tool": "",
                    "confidence": "high",
                    "assumption_used": "",
                }

        understanding = resolve_runtime_question_understanding(
            "Google 在这个专题里处于什么位置？",
            ["Google"],
            "安全与治理",
            mode="hybrid",
            client=FakeClient(),
        )
        self.assertEqual(understanding.question_scope, "company")
        self.assertEqual(understanding.resolved_company, "Google")
        self.assertEqual(understanding.explanation_dimension, "comparison")

    def test_resolve_runtime_question_understanding_derives_type_from_scope_when_llm_keeps_it_coarse(self) -> None:
        class FakeClient:
            def is_available(self) -> bool:
                return True

            def generate_json(self, **kwargs):
                return {
                    "question_scope": "general",
                    "explanation_dimension": "explanation",
                    "entity": "",
                    "target_company": "",
                    "target_theme": "",
                    "needs_general_knowledge": True,
                    "requested_tool": "",
                    "confidence": "medium",
                    "assumption_used": "",
                }

        understanding = resolve_runtime_question_understanding(
            "什么是知识蒸馏，它通常适合用在什么场景？",
            ["Google"],
            "安全与治理",
            mode="hybrid",
            client=FakeClient(),
        )
        self.assertEqual(understanding.question_type, "general_explainer")
        self.assertEqual(understanding.question_scope, "general")
        self.assertTrue(understanding.needs_general_knowledge)


if __name__ == "__main__":
    unittest.main()
