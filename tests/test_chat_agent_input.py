"""Tests for preview/fallback chat input compatibility helpers."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.chat_agent_input import build_chat_agent_inputs_from_report, load_chat_agent_inputs
from tech_daily.models import DailyReport


class ChatAgentInputTests(unittest.TestCase):
    def test_load_chat_agent_inputs_reads_daily_artifacts_and_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            site_dir = Path(temp_dir) / "site"
            daily_dir = site_dir / "2026-05-15"
            daily_dir.mkdir(parents=True)
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir(parents=True)

            (daily_dir / "report.json").write_text(json.dumps({"headline": "headline"}), encoding="utf-8")
            (daily_dir / "daily_intel_brief.json").write_text(
                json.dumps({"editorial_signal": "signal"}, ensure_ascii=False), encoding="utf-8"
            )
            (daily_dir / "cross_day_intel_brief.json").write_text(
                json.dumps({"warming_themes": ["安全与治理"]}, ensure_ascii=False), encoding="utf-8"
            )
            (daily_dir / "theme_tracking_brief.json").write_text(
                json.dumps({"primary_theme": "安全与治理"}, ensure_ascii=False), encoding="utf-8"
            )
            (daily_dir / "theme_dossier.json").write_text(
                json.dumps({"primary_theme": "安全与治理", "theme_state": "emerging"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (data_dir / "health_snapshot.json").write_text(
                json.dumps({"ops_status_analysis": {"operator_brief": "tesla still blocked"}}, ensure_ascii=False),
                encoding="utf-8",
            )

            inputs = load_chat_agent_inputs(site_dir, "2026-05-15", data_dir=data_dir)

        self.assertEqual(inputs.report["headline"], "headline")
        self.assertEqual(inputs.daily_brief["editorial_signal"], "signal")
        self.assertEqual(inputs.cross_day_brief["warming_themes"], ["安全与治理"])
        self.assertEqual(inputs.theme_tracking_brief["primary_theme"], "安全与治理")
        self.assertEqual(inputs.theme_dossier_brief["theme_state"], "emerging")
        self.assertEqual(inputs.health_snapshot["ops_status_analysis"]["operator_brief"], "tesla still blocked")

    def test_build_chat_agent_inputs_from_report_uses_embedded_briefs(self) -> None:
        report = DailyReport(
            date="2026-05-15",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=1,
            companies_covered=1,
            company_reports=[],
            source_statuses=[],
            agent_brief={"editorial_signal": "signal"},
            cross_day_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={"primary_theme": "安全与治理"},
            theme_dossier_brief={"theme_state": "emerging"},
        )

        inputs = build_chat_agent_inputs_from_report(report)

        self.assertEqual(inputs.report_date, "2026-05-15")
        self.assertEqual(inputs.report["headline"], "headline")
        self.assertEqual(inputs.daily_brief["editorial_signal"], "signal")
        self.assertEqual(inputs.cross_day_brief["warming_themes"], ["安全与治理"])
        self.assertEqual(inputs.theme_tracking_brief["primary_theme"], "安全与治理")
        self.assertEqual(inputs.theme_dossier_brief["theme_state"], "emerging")
        self.assertEqual(inputs.health_snapshot, {})


if __name__ == "__main__":
    unittest.main()
