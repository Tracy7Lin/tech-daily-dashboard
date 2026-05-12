import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.healthcheck import run_health_check
from tech_daily.models import Company, Source
from tech_daily.settings import Settings


class HealthCheckTests(unittest.TestCase):
    @patch("tech_daily.healthcheck.load_companies")
    def test_run_health_check_reports_llm_fallback_note(self, mock_load_companies) -> None:
        mock_load_companies.return_value = [
            Company(
                slug="openai",
                name="OpenAI",
                region="US",
                sources=[Source(kind="rss", url="https://example.com/rss", label="RSS")],
            )
        ]
        with TemporaryDirectory() as temp_dir:
            settings = Settings(
                site_output_dir=str(Path(temp_dir) / "site"),
                data_output_dir=str(Path(temp_dir) / "data"),
                summary_mode="hybrid",
                editorial_mode="hybrid",
                llm_api_url="https://api.deepseek.com",
                llm_api_key="",
                llm_model="deepseek-v4-flash",
            )
            result = run_health_check(settings=settings)

        self.assertFalse(result["llm_available"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["company_count"], 1)
        self.assertEqual(result["source_count"], 1)
        self.assertIn("hybrid mode will fall back to rule output until LLM credentials are complete", result["notes"])

    @patch("tech_daily.healthcheck.load_companies")
    def test_run_health_check_reports_ready_state(self, mock_load_companies) -> None:
        mock_load_companies.return_value = [
            Company(
                slug="google",
                name="Google",
                region="US",
                sources=[Source(kind="rss", url="https://example.com/rss", label="RSS")],
            )
        ]
        with TemporaryDirectory() as temp_dir:
            settings = Settings(
                site_output_dir=str(Path(temp_dir) / "site"),
                data_output_dir=str(Path(temp_dir) / "data"),
                summary_mode="rule",
                editorial_mode="rule",
                llm_api_url="",
                llm_api_key="",
                llm_model="",
            )
            result = run_health_check(settings=settings)

        self.assertTrue(result["ok"])
        self.assertTrue(result["output_dir_ready"])
        self.assertTrue(result["data_dir_ready"])
        self.assertEqual(result["notes"], [])

    @patch("tech_daily.healthcheck.load_companies")
    def test_run_health_check_includes_source_diagnostics_and_validation_issues(self, mock_load_companies) -> None:
        mock_load_companies.return_value = [
            Company(
                slug="meta",
                name="Meta",
                region="US",
                sources=[
                    Source(
                        kind="html",
                        url="https://example.com/news",
                        label="Newsroom",
                        require_published_at=True,
                        fetch_article_details=False,
                    )
                ],
            )
        ]
        with TemporaryDirectory() as temp_dir:
            settings = Settings(
                site_output_dir=str(Path(temp_dir) / "site"),
                data_output_dir=str(Path(temp_dir) / "data"),
                summary_mode="rule",
                editorial_mode="rule",
                llm_api_url="",
                llm_api_key="",
                llm_model="",
            )
            result = run_health_check(settings=settings)

        self.assertFalse(result["ok"])
        self.assertEqual(result["validation_issue_count"], 1)
        self.assertEqual(result["source_diagnostics"][0]["company_slug"], "meta")
        self.assertEqual(result["source_diagnostics"][0]["severity"], "warning")
        self.assertIn("published_at_requires_article_details", result["source_diagnostics"][0]["issues"])
        self.assertIn("enable article detail fetching", result["source_diagnostics"][0]["suggestion"])

    @patch("tech_daily.healthcheck.load_companies")
    def test_run_health_check_includes_latest_runtime_diagnostics(self, mock_load_companies) -> None:
        mock_load_companies.return_value = [
            Company(
                slug="tesla",
                name="Tesla",
                region="US",
                sources=[Source(kind="html", url="https://www.tesla.com/blog", label="Tesla Blog")],
            )
        ]
        with TemporaryDirectory() as temp_dir:
            site_dir = Path(temp_dir) / "site"
            report_dir = site_dir / "2026-05-13"
            report_dir.mkdir(parents=True)
            payload = {
                "date": "2026-05-13",
                "headline": "headline",
                "source_statuses": [
                    {
                        "company_slug": "tesla",
                        "company_name": "Tesla",
                        "source_label": "Tesla Blog",
                        "source_url": "https://www.tesla.com/blog",
                        "ok": False,
                        "message": "http_error:403;kept:0;date_matched:0;final_included:0",
                        "fetched_count": 0,
                        "kept_count": 0,
                        "date_matched_count": 0,
                        "final_included_count": 0,
                    }
                ],
            }
            (report_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
            settings = Settings(
                site_output_dir=str(site_dir),
                data_output_dir=str(Path(temp_dir) / "data"),
                summary_mode="rule",
                editorial_mode="rule",
                llm_api_url="",
                llm_api_key="",
                llm_model="",
            )
            result = run_health_check(settings=settings)

        self.assertEqual(result["latest_report_date"], "2026-05-13")
        self.assertEqual(result["recent_runtime_diagnostics"][0]["company_slug"], "tesla")
        self.assertEqual(result["recent_runtime_diagnostics"][0]["severity"], "error")
        self.assertIn("http_403_blocked", result["recent_runtime_diagnostics"][0]["issues"])


if __name__ == "__main__":
    unittest.main()
