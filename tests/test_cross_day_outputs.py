import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.cross_day_outputs import write_cross_day_outputs
from tech_daily.models import CrossDayIntelBrief


class CrossDayOutputsTests(unittest.TestCase):
    def test_write_cross_day_outputs_persists_json_and_markdown(self) -> None:
        brief = CrossDayIntelBrief(
            date_range=("2026-05-13", "2026-05-15"),
            warming_themes=["安全与治理"],
            cooling_themes=["客户落地案例"],
            steady_companies=["OpenAI"],
            swing_companies=["Anthropic"],
            persistent_source_risks=["tesla"],
            recent_source_recoveries=["alibaba"],
            watchlist=["安全与治理", "tesla"],
            next_day_focus=["安全与治理"],
            mode_used="hybrid",
        )

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_cross_day_outputs(brief, output_dir)
            brief_json = json.loads((output_dir / "cross_day_intel_brief.json").read_text(encoding="utf-8"))
            brief_md = (output_dir / "cross-day-brief.md").read_text(encoding="utf-8")

        self.assertEqual(result["json_path"].name, "cross_day_intel_brief.json")
        self.assertEqual(brief_json["steady_companies"], ["OpenAI"])
        self.assertIn("最近几天主线", brief_md)


if __name__ == "__main__":
    unittest.main()
