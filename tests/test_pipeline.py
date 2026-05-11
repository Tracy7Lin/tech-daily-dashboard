import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.classifier import classify_entry
from tech_daily.editorial import EditorialService
from tech_daily.models import Company, RawEntry, SourceStatus
from tech_daily.pipeline import _augment_status_counts, _build_daily_brief, _build_headline, generate_daily_report
from tech_daily.quality import filter_high_signal_entries, matches_report_date


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rule_editorial = EditorialService(mode="rule")

    def test_build_headline_distinguishes_no_same_day_updates(self) -> None:
        statuses = [
            SourceStatus(
                company_slug="meta",
                company_name="Meta",
                source_label="Meta News",
                source_url="https://example.com",
                ok=True,
                message="fetched:5;kept:5",
                fetched_count=5,
                kept_count=5,
                date_matched_count=0,
                final_included_count=0,
            )
        ]
        headline = _build_headline(0, statuses)
        self.assertEqual(headline, "今天未发现符合北京时间自然日范围的高价值官方动态。")

    def test_build_headline_distinguishes_filtered_same_day_updates(self) -> None:
        statuses = [
            SourceStatus(
                company_slug="meta",
                company_name="Meta",
                source_label="Meta News",
                source_url="https://example.com",
                ok=True,
                message="fetched:5;kept:5",
                fetched_count=5,
                kept_count=5,
                date_matched_count=2,
                final_included_count=0,
            )
        ]
        headline = _build_headline(0, statuses)
        self.assertEqual(headline, "今天抓到了同日官方动态，但在质量约束下未保留可发布条目。")

    def test_build_daily_brief_reads_more_like_daily_summary(self) -> None:
        report_entries = [
            Company(
                slug="openai",
                name="OpenAI",
                region="us",
                sources=[],
            )
        ]
        clusters = [
            type("Cluster", (), {"title": "模型与能力发布"})(),
            type("Cluster", (), {"title": "安全与治理"})(),
        ]
        company_reports = [
            type("Report", (), {"company_name": "OpenAI", "has_updates": True})(),
            type("Report", (), {"company_name": "Microsoft", "has_updates": True})(),
        ]
        with patch("tech_daily.pipeline.build_daily_headline", self.rule_editorial.build_daily_headline):
            brief = _build_daily_brief(clusters, company_reports, 5)
        self.assertIn("今天最值得关注的信号", brief)
        self.assertIn("模型与能力发布", brief)
        self.assertIn("OpenAI", brief)

    def test_augment_status_counts_updates_diagnostics(self) -> None:
        statuses = [
            SourceStatus(
                company_slug="meta",
                company_name="Meta",
                source_label="Meta News",
                source_url="https://example.com",
                ok=True,
                message="fetched:2;kept:2",
                fetched_count=2,
                kept_count=2,
            )
        ]
        raw = [
            RawEntry(
                company_slug="meta",
                company_name="Meta",
                source_label="Meta News",
                title="Meta launches AI",
                url="https://example.com/a",
                published_at="2026-05-10T10:00:00Z",
            )
        ]
        dated = raw
        final_entries = [classify_entry(raw[0])]
        updated = _augment_status_counts(statuses, raw, dated, final_entries)
        self.assertEqual(updated[0].date_matched_count, 1)
        self.assertEqual(updated[0].final_included_count, 1)
        self.assertIn("date_matched:1", updated[0].message)

    @patch("tech_daily.pipeline.collect_entries")
    @patch("tech_daily.pipeline.load_companies")
    def test_generate_daily_report_returns_report_object(self, mock_load_companies, mock_collect_entries) -> None:
        mock_load_companies.return_value = [Company(slug="openai", name="OpenAI", region="us", sources=[])]
        mock_collect_entries.return_value = (
            [
                RawEntry(
                    company_slug="openai",
                    company_name="OpenAI",
                    source_label="news",
                    title="OpenAI launches new agent APIs",
                    url="https://example.com/today",
                    published_at="Sat, 10 May 2026 08:00:00 GMT",
                )
            ],
            [],
        )
        with TemporaryDirectory() as temp_dir:
            report = generate_daily_report("2026-05-10", output_dir=Path(temp_dir))
            self.assertEqual(report.date, "2026-05-10")
            self.assertTrue((Path(temp_dir) / "index.html").exists())

    def test_filter_high_signal_entries_drops_noise(self) -> None:
        kept = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="OpenAI launches enterprise agent APIs",
            url="https://example.com/1",
        )
        noise = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="Register now for careers webinar",
            url="https://example.com/2",
        )
        filtered = filter_high_signal_entries([classify_entry(kept)])
        self.assertEqual(len(filtered), 1)

        noisy_filtered = filter_high_signal_entries([classify_entry(noise)])
        self.assertEqual(noisy_filtered, [])

    @patch("tech_daily.pipeline.collect_entries")
    @patch("tech_daily.pipeline.load_companies")
    def test_generate_daily_report_filters_non_matching_dates(self, mock_load_companies, mock_collect_entries) -> None:
        mock_load_companies.return_value = [Company(slug="openai", name="OpenAI", region="us", sources=[])]
        mock_collect_entries.return_value = (
            [
                RawEntry(
                    company_slug="openai",
                    company_name="OpenAI",
                    source_label="news",
                    title="OpenAI launches new agent APIs",
                    url="https://example.com/today",
                    published_at="Sat, 10 May 2026 08:00:00 GMT",
                ),
                RawEntry(
                    company_slug="openai",
                    company_name="OpenAI",
                    source_label="news",
                    title="OpenAI launches old agent APIs",
                    url="https://example.com/yesterday",
                    published_at="Fri, 09 May 2026 08:00:00 GMT",
                ),
            ],
            [
                SourceStatus(
                    company_slug="openai",
                    company_name="OpenAI",
                    source_label="news",
                    source_url="https://example.com/feed",
                    ok=True,
                    message="fetched:2",
                )
            ],
        )

        with TemporaryDirectory() as temp_dir:
            report = generate_daily_report("2026-05-10", output_dir=Path(temp_dir))
            self.assertEqual(report.total_entries, 1)
            self.assertEqual(report.company_reports[0].entries[0].raw.title, "OpenAI launches new agent APIs")

    @patch("tech_daily.pipeline.collect_entries")
    @patch("tech_daily.pipeline.load_companies")
    def test_generate_daily_report_excludes_entries_without_published_at(self, mock_load_companies, mock_collect_entries) -> None:
        mock_load_companies.return_value = [Company(slug="meta", name="Meta", region="us", sources=[])]
        mock_collect_entries.return_value = (
            [
                RawEntry(
                    company_slug="meta",
                    company_name="Meta",
                    source_label="Meta News",
                    title="Meta launches AI tooling",
                    url="https://example.com/meta",
                    published_at="",
                    requires_published_at=True,
                )
            ],
            [
                SourceStatus(
                    company_slug="meta",
                    company_name="Meta",
                    source_label="Meta News",
                    source_url="https://example.com/feed",
                    ok=True,
                    message="fetched:1;kept:1",
                    fetched_count=1,
                    kept_count=1,
                )
            ],
        )
        with TemporaryDirectory() as temp_dir:
            report = generate_daily_report("2026-05-10", output_dir=Path(temp_dir))
            self.assertEqual(report.total_entries, 0)
            self.assertEqual(report.source_statuses[0].date_matched_count, 0)


if __name__ == "__main__":
    unittest.main()
