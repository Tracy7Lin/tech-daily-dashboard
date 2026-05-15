import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import ThemeDossierBrief, ThemeDossierTimelineEvent
from tech_daily.theme_dossier_outputs import write_theme_dossier_outputs


class ThemeDossierOutputsTests(unittest.TestCase):
    def test_write_theme_dossier_outputs_persists_json_and_markdown(self) -> None:
        brief = ThemeDossierBrief(
            date_range=("2026-05-13", "2026-05-15"),
            primary_theme="安全与治理",
            theme_definition="安全与治理主题聚焦于让模型和产品在进入用户场景前就加入约束与控制。",
            theme_state="active",
            theme_summary="安全与治理仍是最近几天最值得继续跟踪的主专题。",
            participating_companies=["OpenAI", "Google"],
            company_positions={"OpenAI": "平台与安全控制", "Google": "产品功能约束"},
            timeline_events=[
                ThemeDossierTimelineEvent(
                    date="2026-05-15",
                    company="Google",
                    title="Google expands education safeguards",
                    why_it_matters="说明安全要求开始进入更具体的产品场景。",
                )
            ],
            tracking_decision="这个主题仍建议继续跟踪，因为它已经从单点动作转向持续主线。",
            next_day_focus=["安全与治理", "Google"],
            mode_used="hybrid",
        )

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_theme_dossier_outputs(brief, output_dir)
            payload = json.loads((output_dir / "theme_dossier.json").read_text(encoding="utf-8"))

        self.assertEqual(result["json_path"].name, "theme_dossier.json")
        self.assertEqual(result["markdown_path"].name, "theme-dossier.md")
        self.assertEqual(payload["theme_state"], "active")
        self.assertIn("page_block", result)


if __name__ == "__main__":
    unittest.main()
