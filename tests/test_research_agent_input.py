import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_input import load_research_agent_inputs


class ResearchAgentInputTests(unittest.TestCase):
    def test_load_research_agent_inputs_reads_daily_knowledge_files(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir) / "site"
            data_dir = Path(tmpdir) / "data"
            daily_dir = site_dir / "2026-05-18"
            daily_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)

            (daily_dir / "report.json").write_text('{"date":"2026-05-18","headline":"h"}', encoding="utf-8")
            (daily_dir / "daily_intel_brief.json").write_text('{"editorial_signal":"d"}', encoding="utf-8")
            (daily_dir / "cross_day_intel_brief.json").write_text('{"warming_themes":["安全与治理"]}', encoding="utf-8")
            (daily_dir / "theme_tracking_brief.json").write_text('{"primary_theme":"安全与治理"}', encoding="utf-8")
            (daily_dir / "theme_dossier.json").write_text(
                '{"primary_theme":"安全与治理","theme_state":"emerging"}',
                encoding="utf-8",
            )
            (data_dir / "health_snapshot.json").write_text('{"operator_brief":"ops"}', encoding="utf-8")

            inputs = load_research_agent_inputs(site_dir, data_dir, "2026-05-18")

        self.assertEqual(inputs.report["headline"], "h")
        self.assertEqual(inputs.daily_intel_brief["editorial_signal"], "d")
        self.assertEqual(inputs.cross_day_intel_brief["warming_themes"], ["安全与治理"])
        self.assertEqual(inputs.theme_tracking_brief["primary_theme"], "安全与治理")
        self.assertEqual(inputs.theme_dossier["theme_state"], "emerging")
        self.assertEqual(inputs.health_snapshot["operator_brief"], "ops")


if __name__ == "__main__":
    unittest.main()
