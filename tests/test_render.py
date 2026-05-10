import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import CompanyReport, DailyReport, TopicCluster
from tech_daily.render import render_index, write_site


class RenderTests(unittest.TestCase):
    def test_render_index_contains_topic_section(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=["AI Agent"],
            total_entries=1,
            companies_covered=1,
            topic_clusters=[
                TopicCluster(
                    topic_id="ai-agent",
                    title="AI Agent",
                    summary="summary",
                    comparison="comparison",
                    trend="trend",
                )
            ],
            company_reports=[CompanyReport(company_slug="openai", company_name="OpenAI", has_updates=False)],
            source_statuses=[],
        )
        html = render_index(report)
        self.assertIn("主题对比", html)

    def test_write_site_preserves_existing_archive_entries(self) -> None:
        older_report = DailyReport(
            date="2026-05-09",
            headline="older",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        newer_report = DailyReport(
            date="2026-05-10",
            headline="newer",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_site(older_report, output_dir)
            write_site(newer_report, output_dir)
            archive_html = (output_dir / "archive.html").read_text(encoding="utf-8")
            self.assertIn("2026-05-10", archive_html)
            self.assertIn("2026-05-09", archive_html)


if __name__ == "__main__":
    unittest.main()
