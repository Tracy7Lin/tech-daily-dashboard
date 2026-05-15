from __future__ import annotations

from pathlib import Path

from .theme_tracking_analysis import analyze_theme_tracking
from .theme_tracking_input import load_theme_tracking_inputs
from .theme_tracking_outputs import write_theme_tracking_outputs


def run_theme_tracking_pipeline(site_dir: Path, report_date: str, days: int = 3) -> dict:
    inputs = load_theme_tracking_inputs(site_dir, end_date=report_date, days=days)
    brief = analyze_theme_tracking(
        date_range=inputs.date_range,
        reports=inputs.reports,
        daily_briefs=inputs.daily_briefs,
        cross_day_briefs=inputs.cross_day_briefs,
    )
    outputs = write_theme_tracking_outputs(brief, site_dir / report_date)
    return {
        "brief": brief,
        "outputs": outputs,
        "json_path": outputs["json_path"],
        "markdown_path": outputs["markdown_path"],
        "page_block": outputs["page_block"],
    }
