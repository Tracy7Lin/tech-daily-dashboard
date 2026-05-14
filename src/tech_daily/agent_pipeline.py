from __future__ import annotations

from pathlib import Path

from .agent_analysis import analyze_daily_intel
from .agent_input import load_agent_inputs
from .agent_outputs import write_agent_outputs


def run_agent_pipeline(report_path: Path, snapshot_path: Path) -> dict:
    inputs = load_agent_inputs(report_path, snapshot_path)
    brief = analyze_daily_intel(inputs.report, inputs.health_snapshot)
    outputs = write_agent_outputs(brief, report_path.parent)
    return {
        "brief": brief,
        "outputs": outputs,
        "page_block": brief.to_dict(),
    }
