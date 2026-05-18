import unittest
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_response import ResearchAgentResponder


class ResearchAgentResponseTests(unittest.TestCase):
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
            },
        ):
            answer = responder.answer(context)

        self.assertEqual(answer["mode_used"], "llm")
        self.assertIn("萌芽阶段", answer["answer"])


if __name__ == "__main__":
    unittest.main()
