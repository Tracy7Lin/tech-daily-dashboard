from __future__ import annotations

from pathlib import Path

from .cross_day_analysis import analyze_cross_day_intel
from .cross_day_input import load_cross_day_inputs
from .cross_day_outputs import write_cross_day_outputs


def run_cross_day_pipeline(site_dir: Path, snapshot_history_dir: Path, report_date: str, days: int = 3) -> dict:
    inputs = load_cross_day_inputs(site_dir, snapshot_history_dir, end_date=report_date, days=days)
    brief = analyze_cross_day_intel(
        date_range=inputs.date_range,
        reports=inputs.reports,
        intel_briefs=inputs.intel_briefs,
        snapshots=inputs.snapshots,
    )
    outputs = write_cross_day_outputs(brief, site_dir / report_date)
    return {
        "brief": brief,
        "outputs": outputs,
        "json_path": outputs["json_path"],
        "markdown_path": outputs["markdown_path"],
        "page_block": outputs["page_block"],
    }
