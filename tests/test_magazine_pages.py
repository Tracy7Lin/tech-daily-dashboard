import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.magazine_pages import build_magazine_pages
from tech_daily.models import DailyReport


class MagazinePagesTests(unittest.TestCase):
    def test_build_magazine_pages_returns_cover_topic_and_dossier_blocks(self) -> None:
        report = DailyReport(
            date="2026-05-17",
            headline="今天最值得关注的是安全与治理。",
            hottest_topics=["安全与治理"],
            total_entries=0,
            companies_covered=0,
            active_companies=["OpenAI", "Google"],
            theme_tracking_brief={
                "primary_theme": "安全与治理",
                "theme_summary": "安全与治理仍是最近几天的主专题。",
                "participating_companies": ["OpenAI", "Google"],
                "next_day_theme_focus": ["安全与治理"],
            },
            theme_dossier_brief={
                "primary_theme": "安全与治理",
                "theme_state": "emerging",
                "theme_definition": "不同公司正在把安全能力前置到产品和平台层。",
                "tracking_decision": "建议继续跟踪。",
            },
        )
        pages = build_magazine_pages(report)
        self.assertEqual(pages["cover"]["primary_theme"], "安全与治理")
        self.assertEqual(pages["topic_page"]["title"], "安全与治理")
        self.assertEqual(pages["dossier_page"]["title"], "安全与治理")

    def test_build_magazine_pages_includes_recent_issue_links(self) -> None:
        report = DailyReport(
            date="2026-05-17",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        pages = build_magazine_pages(report)
        self.assertTrue(pages["cover"]["recent_issues"])
        self.assertTrue(pages["cover"]["recent_issues"][0]["href"].endswith("/index.html"))


if __name__ == "__main__":
    unittest.main()
