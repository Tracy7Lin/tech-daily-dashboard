import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.theme_tracking_input import load_theme_tracking_inputs


class ThemeTrackingInputTests(unittest.TestCase):
    def test_load_theme_tracking_inputs_reads_reports_and_optional_agent_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"

            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps(
                        {
                            "date": date_text,
                            "hottest_topics": ["安全与治理"],
                            "active_companies": ["OpenAI"],
                        }
                    ),
                    encoding="utf-8",
                )
                (report_dir / "daily_intel_brief.json").write_text(
                    json.dumps({"report_date": date_text, "top_content_themes": ["安全与治理"]}),
                    encoding="utf-8",
                )
                (report_dir / "cross_day_intel_brief.json").write_text(
                    json.dumps({"date_range": ["2026-05-13", date_text], "warming_themes": ["安全与治理"]}),
                    encoding="utf-8",
                )

            payload = load_theme_tracking_inputs(site_dir, end_date="2026-05-15", days=3)

        self.assertEqual(payload.date_range, ("2026-05-13", "2026-05-15"))
        self.assertEqual(len(payload.reports), 3)
        self.assertEqual(payload.daily_briefs[-1]["report_date"], "2026-05-15")
        self.assertEqual(payload.cross_day_briefs[-1]["warming_themes"], ["安全与治理"])

    def test_load_theme_tracking_inputs_tolerates_missing_daily_and_cross_day_briefs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            report_dir = site_dir / "2026-05-15"
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(
                json.dumps({"date": "2026-05-15", "hottest_topics": ["安全与治理"]}),
                encoding="utf-8",
            )

            payload = load_theme_tracking_inputs(site_dir, end_date="2026-05-15", days=1)

        self.assertEqual(len(payload.reports), 1)
        self.assertEqual(payload.daily_briefs, [])
        self.assertEqual(payload.cross_day_briefs, [])


if __name__ == "__main__":
    unittest.main()
