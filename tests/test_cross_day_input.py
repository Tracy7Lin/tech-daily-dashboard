import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.cross_day_input import load_cross_day_inputs


class CrossDayInputTests(unittest.TestCase):
    def test_load_cross_day_inputs_reads_recent_reports_and_snapshots(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            data_dir = root / "data" / "health_snapshots"
            data_dir.mkdir(parents=True)

            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps({"date": date_text, "active_companies": ["OpenAI"]}),
                    encoding="utf-8",
                )
                (data_dir / f"{date_text}.json").write_text(
                    json.dumps(
                        {
                            "report_date": date_text,
                            "ops_status_analysis": {"operator_brief": f"brief-{date_text}"},
                        }
                    ),
                    encoding="utf-8",
                )

            payload = load_cross_day_inputs(site_dir, data_dir, end_date="2026-05-15", days=3)

        self.assertEqual(payload.date_range, ("2026-05-13", "2026-05-15"))
        self.assertEqual(len(payload.reports), 3)
        self.assertEqual(payload.snapshots[-1]["ops_status_analysis"]["operator_brief"], "brief-2026-05-15")

    def test_load_cross_day_inputs_tolerates_missing_daily_intel_briefs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            data_dir = root / "data" / "health_snapshots"
            data_dir.mkdir(parents=True)

            report_dir = site_dir / "2026-05-15"
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(
                json.dumps({"date": "2026-05-15", "active_companies": ["OpenAI"]}),
                encoding="utf-8",
            )
            (data_dir / "2026-05-15.json").write_text(
                json.dumps({"report_date": "2026-05-15"}),
                encoding="utf-8",
            )

            payload = load_cross_day_inputs(site_dir, data_dir, end_date="2026-05-15", days=1)

        self.assertEqual(len(payload.reports), 1)
        self.assertEqual(payload.intel_briefs, [])


if __name__ == "__main__":
    unittest.main()
