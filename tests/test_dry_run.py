import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.dry_run import run_dry_run
from tech_daily.models import Company, Source
from tech_daily.settings import Settings


class DryRunTests(unittest.TestCase):
    @patch("tech_daily.dry_run.load_companies")
    def test_run_dry_run_returns_planned_report_date_and_validation_count(self, mock_load_companies) -> None:
        mock_load_companies.return_value = [
            Company(
                slug="amazon",
                name="Amazon",
                region="US",
                sources=[Source(kind="rss", url="https://example.com/rss", label="RSS")],
            )
        ]
        with TemporaryDirectory() as temp_dir:
            settings = Settings(
                site_output_dir=str(Path(temp_dir) / "site"),
                data_output_dir=str(Path(temp_dir) / "data"),
            )
            result = run_dry_run("2026-05-12", settings=settings)

        self.assertTrue(result["ok"])
        self.assertEqual(result["report_date"], "2026-05-12")
        self.assertEqual(result["company_count"], 1)
        self.assertEqual(result["validation_issue_count"], 0)
        self.assertEqual(result["source_diagnostic_count"], 1)


if __name__ == "__main__":
    unittest.main()
