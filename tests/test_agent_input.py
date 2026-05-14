import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.agent_input import load_agent_inputs


class AgentInputTests(unittest.TestCase):
    def test_load_agent_inputs_reads_report_and_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_dir = root / "site" / "2026-05-14"
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(
                json.dumps({"date": "2026-05-14", "headline": "headline"}),
                encoding="utf-8",
            )
            snapshot_dir = root / "data"
            snapshot_dir.mkdir(parents=True)
            (snapshot_dir / "health_snapshot.json").write_text(
                json.dumps({"ops_status_analysis": {"operator_brief": "brief"}}),
                encoding="utf-8",
            )

            payload = load_agent_inputs(
                report_dir / "report.json",
                snapshot_dir / "health_snapshot.json",
            )

        self.assertEqual(payload.report["date"], "2026-05-14")
        self.assertEqual(payload.health_snapshot["ops_status_analysis"]["operator_brief"], "brief")


if __name__ == "__main__":
    unittest.main()
