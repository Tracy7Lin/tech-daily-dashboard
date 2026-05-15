import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.theme_dossier_pipeline import run_theme_dossier_pipeline


class ThemeDossierPipelineTests(unittest.TestCase):
    def test_run_theme_dossier_pipeline_writes_artifacts(self) -> None:
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
                            "topic_clusters": [
                                {
                                    "title": "安全与治理",
                                    "entries": [
                                        {
                                            "raw": {
                                                "company_name": "OpenAI",
                                                "title": f"Safety update {date_text}",
                                            },
                                            "comparison_angle": "平台与安全控制",
                                        }
                                    ],
                                }
                            ],
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
                (report_dir / "theme_tracking_brief.json").write_text(
                    json.dumps({"primary_theme": "安全与治理", "participating_companies": ["OpenAI"]}),
                    encoding="utf-8",
                )

            result = run_theme_dossier_pipeline(site_dir, report_date="2026-05-15", days=3)

        self.assertEqual(result["json_path"].name, "theme_dossier.json")
        self.assertEqual(result["markdown_path"].name, "theme-dossier.md")
        self.assertIn("page_block", result)


if __name__ == "__main__":
    unittest.main()
