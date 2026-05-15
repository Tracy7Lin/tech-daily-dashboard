from __future__ import annotations

from pathlib import Path

from .theme_dossier_analysis import analyze_theme_dossier
from .theme_dossier_input import load_theme_dossier_inputs
from .theme_dossier_outputs import write_theme_dossier_outputs


def run_theme_dossier_pipeline(site_dir: Path, report_date: str, days: int = 3) -> dict:
    inputs = load_theme_dossier_inputs(site_dir, end_date=report_date, days=days)
    brief = analyze_theme_dossier(
        date_range=inputs.date_range,
        reports=inputs.reports,
        daily_briefs=inputs.daily_briefs,
        cross_day_briefs=inputs.cross_day_briefs,
        theme_tracking_briefs=inputs.theme_tracking_briefs,
    )
    outputs = write_theme_dossier_outputs(brief, site_dir / report_date)
    return {
        "brief": brief,
        "outputs": outputs,
        "json_path": outputs["json_path"],
        "markdown_path": outputs["markdown_path"],
        "page_block": outputs["page_block"],
    }
