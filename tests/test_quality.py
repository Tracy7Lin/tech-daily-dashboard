import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.classifier import classify_entry
from tech_daily.models import RawEntry
from tech_daily.quality import filter_high_signal_entries, is_noise_entry, matches_report_date


class QualityTests(unittest.TestCase):
    def test_matches_report_date_accepts_matching_rss_date(self) -> None:
        self.assertTrue(matches_report_date("Sat, 10 May 2026 08:00:00 GMT", "2026-05-10"))
        self.assertFalse(matches_report_date("Fri, 09 May 2026 08:00:00 GMT", "2026-05-10"))
        self.assertTrue(matches_report_date("May 10, 2026", "2026-05-10"))
        self.assertFalse(matches_report_date("Feb 4, 2026", "2026-05-10"))

    def test_is_noise_entry_rejects_generic_category_pages(self) -> None:
        entry = classify_entry(
            RawEntry(
                company_slug="meta",
                company_name="Meta",
                source_label="news",
                title="Meta Quest",
                url="https://about.fb.com/news/category/technologies/oculus/",
            )
        )
        self.assertTrue(is_noise_entry(entry))

    def test_filter_high_signal_entries_keeps_specific_product_story(self) -> None:
        entry = classify_entry(
            RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="news",
                title="OpenAI launches enterprise agent APIs",
                url="https://example.com/news/agent-apis",
            )
        )
        filtered = filter_high_signal_entries([entry])
        self.assertEqual(len(filtered), 1)

    def test_filter_high_signal_entries_drops_html_entries_missing_required_date(self) -> None:
        entry = classify_entry(
            RawEntry(
                company_slug="meta",
                company_name="Meta",
                source_label="news",
                title="Meta launches AI tooling",
                url="https://about.fb.com/news/2026/05/meta-launches-ai-tooling/",
                requires_published_at=True,
            )
        )
        filtered = filter_high_signal_entries([entry])
        self.assertEqual(filtered, [])


if __name__ == "__main__":
    unittest.main()
