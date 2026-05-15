import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.cross_day_pipeline import run_cross_day_pipeline


class CrossDayPipelineTests(unittest.TestCase):
    def test_run_cross_day_pipeline_writes_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            snapshot_dir = root / "data" / "health_snapshots"
            snapshot_dir.mkdir(parents=True)

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
                (snapshot_dir / f"{date_text}.json").write_text(
                    json.dumps({"report_date": date_text, "high_priority_runtime_issues": []}),
                    encoding="utf-8",
                )

            result = run_cross_day_pipeline(site_dir, snapshot_dir, report_date="2026-05-15", days=3)

        self.assertEqual(result["json_path"].name, "cross_day_intel_brief.json")
        self.assertIn("page_block", result)


if __name__ == "__main__":
    unittest.main()
