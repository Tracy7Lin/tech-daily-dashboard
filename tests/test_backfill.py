import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.backfill import build_backfill_dates, generate_backfill_reports
from tech_daily.models import DailyReport


class BackfillTests(unittest.TestCase):
    def test_build_backfill_dates_returns_ascending_range(self) -> None:
        dates = build_backfill_dates("2026-05-10", 3)
        self.assertEqual(dates, ["2026-05-08", "2026-05-09", "2026-05-10"])

    @patch("tech_daily.backfill.generate_daily_report")
    def test_generate_backfill_reports_runs_each_date(self, mock_generate_daily_report) -> None:
        mock_generate_daily_report.side_effect = [
            DailyReport(date="2026-05-08", headline="", hottest_topics=[], total_entries=0, companies_covered=0),
            DailyReport(date="2026-05-09", headline="", hottest_topics=[], total_entries=0, companies_covered=0),
        ]
        with TemporaryDirectory() as temp_dir:
            reports = generate_backfill_reports("2026-05-09", 2, output_dir=Path(temp_dir))
        self.assertEqual([report.date for report in reports], ["2026-05-08", "2026-05-09"])
        self.assertEqual(mock_generate_daily_report.call_count, 2)


if __name__ == "__main__":
    unittest.main()
