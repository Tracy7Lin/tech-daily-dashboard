import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.chat_agent_pipeline import build_embedded_chat_context
from tech_daily.models import DailyReport


class ChatAgentPipelineTests(unittest.TestCase):
    def test_build_embedded_chat_context_includes_response_bank(self) -> None:
        report = DailyReport(
            date="2026-05-15",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=0,
            companies_covered=0,
            agent_brief={"editorial_signal": "今天最值得关注的是安全与治理。", "ops_signal": "当前优先处理 tesla。"},
            cross_day_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={
                "primary_theme": "安全与治理",
                "theme_summary": "安全与治理仍是最近几天最值得继续跟踪的专题。",
                "theme_evolution": "这个专题最近几天持续出现。",
                "participating_companies": ["Google"],
            },
        )

        context = build_embedded_chat_context(report)

        self.assertIn("response_bank", context)
        self.assertIn("daily_summary", context["response_bank"])
        self.assertIn("theme_focus", context["response_bank"])
        self.assertIn("ops_status", context["response_bank"])


if __name__ == "__main__":
    unittest.main()
