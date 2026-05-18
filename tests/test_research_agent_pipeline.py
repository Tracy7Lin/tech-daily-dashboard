import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_pipeline import run_research_agent


class ResearchAgentPipelineTests(unittest.TestCase):
    def test_run_research_agent_returns_runtime_answer(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir) / "site"
            data_dir = Path(tmpdir) / "data"
            daily_dir = site_dir / "2026-05-18"
            daily_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            for name, payload in {
                "report.json": '{"date":"2026-05-18","headline":"h"}',
                "daily_intel_brief.json": '{"editorial_signal":"d"}',
                "cross_day_intel_brief.json": '{"warming_themes":["安全与治理"]}',
                "theme_tracking_brief.json": '{"primary_theme":"安全与治理"}',
                "theme_dossier.json": '{"primary_theme":"安全与治理","theme_state":"emerging","tracking_decision":"继续跟踪"}',
            }.items():
                (daily_dir / name).write_text(payload, encoding="utf-8")
            (data_dir / "health_snapshot.json").write_text('{"operator_brief":"ops"}', encoding="utf-8")

            with patch("tech_daily.research_agent_pipeline._build_responder") as mock_builder:
                mock_builder.return_value.answer.return_value = {
                    "answer": "安全与治理仍处萌芽阶段。",
                    "mode_used": "llm",
                    "question_type": "theme_state",
                    "evidence_items": [],
                }
                result = run_research_agent(site_dir, data_dir, "2026-05-18", "为什么现在是 emerging？")

        self.assertEqual(result["mode_used"], "llm")
        self.assertEqual(result["question_type"], "theme_state")


if __name__ == "__main__":
    unittest.main()
