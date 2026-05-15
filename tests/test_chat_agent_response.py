import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.chat_agent_input import ChatAgentInputs
from tech_daily.chat_agent_response import ChatAgentResponder, build_chat_context, answer_chat_question, build_chat_response_bank
from tech_daily.llm_client import LLMClient


class ChatAgentResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inputs = ChatAgentInputs(
            report_date="2026-05-15",
            report={
                "headline": "今天最值得关注的信号是，安全与治理成为主线。",
                "company_reports": [
                    {
                        "company_name": "Google",
                        "entries": [
                            {"raw": {"title": "Google expands safety tools", "source_label": "Google Blog"}}
                        ],
                    }
                ],
            },
            daily_brief={
                "editorial_signal": "安全与治理成为内容主线。",
                "tomorrow_focus": ["安全与治理", "Google"],
            },
            cross_day_brief={
                "warming_themes": ["安全与治理"],
                "steady_companies": ["Google"],
            },
            theme_tracking_brief={
                "primary_theme": "安全与治理",
                "theme_summary": "安全与治理仍是最近几天最值得继续跟踪的专题。",
                "participating_companies": ["Google"],
                "theme_evolution": "这个专题最近几天持续出现，但目前仍以单一公司动作为主。",
                "next_day_theme_focus": ["安全与治理"],
            },
            health_snapshot={
                "ops_status_analysis": {"operator_brief": "当前优先处理 tesla、xiaomi。"},
                "high_priority_runtime_issues": [{"company_slug": "tesla"}, {"company_slug": "xiaomi"}],
            },
        )

    def test_answer_chat_question_routes_company_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("Google 最近几天在做什么？", context)
        self.assertEqual(answer["question_type"], "company_focus")
        self.assertIn("Google", answer["answer"])

    def test_answer_chat_question_routes_theme_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("为什么今天的主专题是安全与治理？", context)
        self.assertEqual(answer["question_type"], "theme_focus")
        self.assertIn("安全与治理", answer["answer"])

    def test_answer_chat_question_routes_ops_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("现在哪些信源还有问题？", context)
        self.assertEqual(answer["question_type"], "ops_status")
        self.assertIn("tesla", answer["answer"].lower())

    def test_chat_responder_hybrid_falls_back_to_rule_when_llm_unavailable(self) -> None:
        context = build_chat_context(self.inputs)
        responder = ChatAgentResponder(mode="hybrid", client=None)
        answer = responder.answer("今天最值得关注什么？", context)
        self.assertEqual(answer["question_type"], "daily_summary")
        self.assertEqual(answer["mode_used"], "rule")

    def test_chat_responder_uses_llm_when_available(self) -> None:
        context = build_chat_context(self.inputs)

        def fake_transport(url, headers, body, timeout):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"answer":"今天最值得关注的是安全与治理，因为最近几天这一主题持续出现。","follow_up_suggestions":["为什么今天的主专题是这个？","Google 最近几天在做什么？"]}'
                        }
                    }
                ]
            }

        client = LLMClient(
            api_url="https://api.deepseek.com/chat/completions",
            api_key="test-key",
            model="deepseek-v4-flash",
            timeout_seconds=10,
            transport=fake_transport,
        )
        responder = ChatAgentResponder(mode="hybrid", client=client)
        answer = responder.answer("今天最值得关注什么？", context)
        self.assertEqual(answer["mode_used"], "llm")
        self.assertIn("安全与治理", answer["answer"])

    def test_build_chat_response_bank_uses_python_generated_answers(self) -> None:
        context = build_chat_context(self.inputs)
        responder = ChatAgentResponder(mode="rule", client=None)
        bank = build_chat_response_bank(context, responder)
        self.assertIn("daily_summary", bank)
        self.assertIn("theme_focus", bank)
        self.assertIn("ops_status", bank)
        self.assertIn("google", bank["company_focus"])


if __name__ == "__main__":
    unittest.main()
