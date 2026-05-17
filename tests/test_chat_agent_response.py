import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.chat_agent_analysis import classify_chat_question
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
                "source_statuses": [],
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
            theme_dossier_brief={
                "primary_theme": "安全与治理",
                "theme_definition": "安全与治理主题聚焦于把约束和控制前置到真实产品场景中。",
                "theme_state": "emerging",
                "theme_summary": "安全与治理仍是最近几天最值得继续看的主专题。",
                "company_positions": {"Google": "产品功能约束"},
                "timeline_events": [
                    {
                        "date": "2026-05-15",
                        "company": "Google",
                        "title": "Google expands education safeguards",
                        "why_it_matters": "说明安全要求开始进入更具体的产品场景。",
                    }
                ],
                "tracking_decision": "建议继续跟踪，因为主题仍在向更具体场景扩展。",
                "next_day_focus": ["安全与治理", "Google"],
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
        self.assertGreaterEqual(len(answer["evidence_points"]), 1)

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

    def test_classify_chat_question_supports_dossier_types(self) -> None:
        companies = ["Google"]
        primary_theme = "安全与治理"
        self.assertEqual(
            classify_chat_question("这个主专题现在怎么理解？", companies, primary_theme),
            ("dossier_summary", primary_theme),
        )
        self.assertEqual(
            classify_chat_question("为什么现在是 emerging？", companies, primary_theme),
            ("theme_state", primary_theme),
        )
        self.assertEqual(
            classify_chat_question("Google 在这个专题里处于什么位置？", companies, primary_theme),
            ("company_position", "Google"),
        )
        self.assertEqual(
            classify_chat_question("最近几天关键时间线说明了什么？", companies, primary_theme),
            ("timeline_focus", primary_theme),
        )

    def test_answer_chat_question_routes_dossier_summary_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("这个主专题现在怎么理解？", context)
        self.assertEqual(answer["question_type"], "dossier_summary")
        self.assertIn("安全与治理", answer["answer"])

    def test_answer_chat_question_routes_theme_state_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("为什么现在是 emerging？", context)
        self.assertEqual(answer["question_type"], "theme_state")
        self.assertIn("emerging", answer["answer"])
        self.assertTrue(any("emerging" in point or "阶段" in point for point in answer["evidence_points"]))

    def test_answer_chat_question_routes_company_position_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("Google 在这个专题里处于什么位置？", context)
        self.assertEqual(answer["question_type"], "company_position")
        self.assertIn("Google", answer["answer"])

    def test_answer_chat_question_routes_timeline_focus_question(self) -> None:
        context = build_chat_context(self.inputs)
        answer = answer_chat_question("最近几天关键时间线说明了什么？", context)
        self.assertEqual(answer["question_type"], "timeline_focus")
        self.assertIn("Google", answer["answer"])
        self.assertTrue(
            any("2026-05-15" in point or "Google expands education safeguards" in point for point in answer["evidence_points"])
        )

    def test_chat_responder_uses_history_for_follow_up(self) -> None:
        context = build_chat_context(self.inputs)
        responder = ChatAgentResponder(mode="rule", client=None)
        answer = responder.answer(
            "那 Google 呢？",
            context,
            history=[
                {
                    "role": "assistant",
                    "question_type": "dossier_summary",
                    "resolved_theme": "安全与治理",
                    "resolved_company": "",
                }
            ],
        )
        self.assertEqual(answer["question_type"], "company_position")
        self.assertEqual(answer["resolved_company"], "Google")

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
        self.assertIn("evidence_points", answer)

    def test_build_chat_response_bank_uses_python_generated_answers(self) -> None:
        context = build_chat_context(self.inputs)
        responder = ChatAgentResponder(mode="rule", client=None)
        bank = build_chat_response_bank(context, responder)
        self.assertIn("daily_summary", bank)
        self.assertIn("theme_focus", bank)
        self.assertIn("ops_status", bank)
        self.assertIn("google", bank["company_focus"])
        self.assertIn("dossier_summary", bank)
        self.assertIn("timeline_focus", bank)
        self.assertIn("google", bank["company_position_answers"])

    def test_build_chat_context_distinguishes_stable_no_news_company(self) -> None:
        inputs = ChatAgentInputs(
            report_date="2026-05-15",
            report={
                "headline": "headline",
                "company_reports": [
                    {"company_slug": "openai", "company_name": "OpenAI", "entries": []}
                ],
                "source_statuses": [
                    {
                        "company_slug": "openai",
                        "company_name": "OpenAI",
                        "source_label": "OpenAI News",
                        "ok": True,
                        "message": "fetched:10;kept:10;date_matched:0;final_included:0",
                        "fetched_count": 10,
                        "kept_count": 10,
                        "date_matched_count": 0,
                        "final_included_count": 0,
                    }
                ],
            },
            daily_brief={},
            cross_day_brief={},
            theme_tracking_brief={},
            theme_dossier_brief={},
            health_snapshot={},
        )
        context = build_chat_context(inputs)
        self.assertIn("官方信源抓取正常", context["company_answers"]["openai"])
        self.assertIn("今天没有落在日报日期范围内的有效动态", context["company_answers"]["openai"])

    def test_build_chat_context_distinguishes_unstable_company(self) -> None:
        inputs = ChatAgentInputs(
            report_date="2026-05-15",
            report={
                "headline": "headline",
                "company_reports": [
                    {"company_slug": "tesla", "company_name": "Tesla", "entries": []}
                ],
                "source_statuses": [
                    {
                        "company_slug": "tesla",
                        "company_name": "Tesla",
                        "source_label": "Tesla IR Press",
                        "ok": False,
                        "message": "http_error:403;kept:0;date_matched:0;final_included:0",
                        "fetched_count": 0,
                        "kept_count": 0,
                        "date_matched_count": 0,
                        "final_included_count": 0,
                    }
                ],
            },
            daily_brief={},
            cross_day_brief={},
            theme_tracking_brief={},
            theme_dossier_brief={},
            health_snapshot={},
        )
        context = build_chat_context(inputs)
        self.assertIn("信源暂未稳定", context["company_answers"]["tesla"])
        self.assertIn("Tesla 官方新闻入口当前持续拒绝抓取请求", context["company_answers"]["tesla"])


if __name__ == "__main__":
    unittest.main()
