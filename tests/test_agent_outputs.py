import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.agent_outputs import write_agent_outputs
from tech_daily.models import DailyIntelBrief


class AgentOutputsTests(unittest.TestCase):
    def test_write_agent_outputs_persists_json_and_markdown(self) -> None:
        brief = DailyIntelBrief(
            report_date="2026-05-14",
            editorial_signal="内容判断",
            ops_signal="运维判断",
            top_content_themes=["安全与治理"],
            watchlist=["tesla"],
            source_risks=["tesla"],
            recoveries=["alibaba"],
            tomorrow_focus=["安全与治理"],
            mode_used="hybrid",
        )
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_agent_outputs(brief, output_dir)

            brief_json = json.loads((output_dir / "daily_intel_brief.json").read_text(encoding="utf-8"))
            brief_md = (output_dir / "agent-brief.md").read_text(encoding="utf-8")

        self.assertEqual(result["json_path"].name, "daily_intel_brief.json")
        self.assertEqual(brief_json["report_date"], "2026-05-14")
        self.assertIn("今日核心判断", brief_md)


if __name__ == "__main__":
    unittest.main()
