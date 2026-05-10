import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.archive import load_report_snapshots


class ArchiveTests(unittest.TestCase):
    def test_load_report_snapshots_returns_reports_sorted_desc(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "2026-05-09").mkdir()
            (root / "2026-05-10").mkdir()
            (root / "2026-05-09" / "report.json").write_text(
                json.dumps(
                    {
                        "date": "2026-05-09",
                        "headline": "older",
                        "hottest_topics": [],
                        "total_entries": 1,
                        "companies_covered": 1,
                    }
                ),
                encoding="utf-8",
            )
            (root / "2026-05-10" / "report.json").write_text(
                json.dumps(
                    {
                        "date": "2026-05-10",
                        "headline": "newer",
                        "hottest_topics": [],
                        "total_entries": 2,
                        "companies_covered": 1,
                    }
                ),
                encoding="utf-8",
            )
            reports = load_report_snapshots(root)
            self.assertEqual([report.date for report in reports], ["2026-05-10", "2026-05-09"])


if __name__ == "__main__":
    unittest.main()
