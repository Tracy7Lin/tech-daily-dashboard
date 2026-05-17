from __future__ import annotations

from pathlib import Path

from .llm_runtime import build_llm_client
from .settings import DEFAULT_SETTINGS
from .theme_dossier_analysis import analyze_theme_dossier
from .theme_dossier_enhancer import ThemeDossierEnhancer
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
    enhancer = ThemeDossierEnhancer(
        mode=DEFAULT_SETTINGS.editorial_mode,
        client=build_llm_client(DEFAULT_SETTINGS),
    )
    brief = enhancer.enhance(brief)
    outputs = write_theme_dossier_outputs(brief, site_dir / report_date)
    return {
        "brief": brief,
        "outputs": outputs,
        "json_path": outputs["json_path"],
        "markdown_path": outputs["markdown_path"],
        "page_block": outputs["page_block"],
    }
