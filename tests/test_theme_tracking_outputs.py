import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import ThemeTrackingBrief
from tech_daily.theme_tracking_outputs import write_theme_tracking_outputs


class ThemeTrackingOutputsTests(unittest.TestCase):
    def test_write_theme_tracking_outputs_persists_json_and_markdown(self) -> None:
        brief = ThemeTrackingBrief(
            date_range=("2026-05-13", "2026-05-15"),
            candidate_themes=["安全与治理", "模型与能力发布"],
            primary_theme="安全与治理",
            theme_summary="安全与治理仍是最近几天最值得继续跟踪的专题。",
            participating_companies=["OpenAI", "Google"],
            company_angles={"OpenAI": "平台与安全机制前置", "Google": "产品功能落地"},
            theme_evolution="专题正在从单点更新演化为多家公司持续参与。",
            continue_tracking=True,
            next_day_theme_focus=["安全与治理", "Google"],
            mode_used="hybrid",
        )

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_theme_tracking_outputs(brief, output_dir)
            brief_json = json.loads((output_dir / "theme_tracking_brief.json").read_text(encoding="utf-8"))
            brief_md = (output_dir / "theme-tracking-brief.md").read_text(encoding="utf-8")

        self.assertEqual(result["json_path"].name, "theme_tracking_brief.json")
        self.assertEqual(brief_json["primary_theme"], "安全与治理")
        self.assertIn("主专题", brief_md)


if __name__ == "__main__":
    unittest.main()
