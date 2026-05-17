import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.chat_agent_memory import resolve_follow_up_route


class ChatAgentMemoryTests(unittest.TestCase):
    def test_resolve_follow_up_route_maps_company_follow_up_to_company_position(self) -> None:
        route = resolve_follow_up_route(
            "那 Google 呢？",
            [
                {
                    "role": "assistant",
                    "question_type": "dossier_summary",
                    "resolved_theme": "安全与治理",
                    "resolved_company": "",
                }
            ],
            companies=["Google", "OpenAI"],
            primary_theme="安全与治理",
        )
        self.assertEqual(route, ("company_position", "Google"))

    def test_resolve_follow_up_route_maps_continue_to_timeline_focus(self) -> None:
        route = resolve_follow_up_route(
            "继续说时间线",
            [
                {
                    "role": "assistant",
                    "question_type": "timeline_focus",
                    "resolved_theme": "安全与治理",
                    "resolved_company": "",
                }
            ],
            companies=["Google"],
            primary_theme="安全与治理",
        )
        self.assertEqual(route, ("timeline_focus", "安全与治理"))

    def test_resolve_follow_up_route_maps_why_to_company_position(self) -> None:
        route = resolve_follow_up_route(
            "为什么？",
            [
                {
                    "role": "assistant",
                    "question_type": "company_position",
                    "resolved_theme": "安全与治理",
                    "resolved_company": "Google",
                }
            ],
            companies=["Google", "OpenAI"],
            primary_theme="安全与治理",
        )
        self.assertEqual(route, ("company_position", "Google"))

    def test_resolve_follow_up_route_maps_generic_continue_to_dossier_summary(self) -> None:
        route = resolve_follow_up_route(
            "继续",
            [
                {
                    "role": "assistant",
                    "question_type": "dossier_summary",
                    "resolved_theme": "安全与治理",
                    "resolved_company": "",
                }
            ],
            companies=["Google", "OpenAI"],
            primary_theme="安全与治理",
        )
        self.assertEqual(route, ("dossier_summary", "安全与治理"))


if __name__ == "__main__":
    unittest.main()
