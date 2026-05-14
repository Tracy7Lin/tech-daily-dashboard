import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.agent_pipeline import run_agent_pipeline


class AgentPipelineTests(unittest.TestCase):
    def test_run_agent_pipeline_generates_brief_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_dir = root / "2026-05-14"
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(
                json.dumps(
                    {
                        "date": "2026-05-14",
                        "headline": "headline",
                        "hottest_topics": [],
                    }
                ),
                encoding="utf-8",
            )
            snapshot_path = root / "health_snapshot.json"
            snapshot_path.write_text(
                json.dumps({"ops_status_analysis": {"operator_brief": "ops"}}),
                encoding="utf-8",
            )

            result = run_agent_pipeline(report_dir / "report.json", snapshot_path)

            self.assertTrue(result["brief"])
            self.assertTrue(result["outputs"]["json_path"].exists())


if __name__ == "__main__":
    unittest.main()
