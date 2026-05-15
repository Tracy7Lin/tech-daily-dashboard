import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.theme_dossier_input import load_theme_dossier_inputs


class ThemeDossierInputTests(unittest.TestCase):
    def test_load_theme_dossier_inputs_reads_reports_and_optional_briefs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps({"date": date_text, "hottest_topics": ["安全与治理"], "topic_clusters": []}),
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
                (report_dir / "theme_tracking_brief.json").write_text(
                    json.dumps({"primary_theme": "安全与治理"}),
                    encoding="utf-8",
                )

            inputs = load_theme_dossier_inputs(site_dir, end_date="2026-05-15", days=3)

        self.assertEqual(inputs.date_range, ("2026-05-13", "2026-05-15"))
        self.assertEqual(len(inputs.reports), 3)
        self.assertEqual(len(inputs.theme_tracking_briefs), 3)


if __name__ == "__main__":
    unittest.main()
