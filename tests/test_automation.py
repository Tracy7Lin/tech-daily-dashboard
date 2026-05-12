import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.automation import generate_today_report, resolve_report_date
from tech_daily.models import DailyReport


class AutomationTests(unittest.TestCase):
    def test_resolve_report_date_uses_shanghai_timezone(self) -> None:
        now = datetime(2026, 5, 11, 16, 30, tzinfo=timezone.utc)
        self.assertEqual(resolve_report_date(now=now), "2026-05-12")

    @patch("tech_daily.automation.generate_daily_report")
    def test_generate_today_report_uses_resolved_report_date(self, mock_generate_daily_report) -> None:
        mock_generate_daily_report.return_value = DailyReport(
            date="2026-05-12",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            report = generate_today_report(
                output_dir=output_dir,
                now=datetime(2026, 5, 11, 16, 30, tzinfo=timezone.utc),
            )

        self.assertEqual(report.date, "2026-05-12")
        mock_generate_daily_report.assert_called_once_with("2026-05-12", output_dir=output_dir)


if __name__ == "__main__":
    unittest.main()
