from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(slots=True)
class ThemeDossierInputs:
    date_range: tuple[str, str]
    reports: list[dict]
    daily_briefs: list[dict]
    cross_day_briefs: list[dict]
    theme_tracking_briefs: list[dict]


def load_theme_dossier_inputs(site_dir: Path, end_date: str, days: int) -> ThemeDossierInputs:
    end_day = date.fromisoformat(end_date)
    dates = [(end_day - timedelta(days=offset)).isoformat() for offset in reversed(range(days))]
    reports: list[dict] = []
    daily_briefs: list[dict] = []
    cross_day_briefs: list[dict] = []
    theme_tracking_briefs: list[dict] = []

    for date_text in dates:
        report_dir = site_dir / date_text
        report_path = report_dir / "report.json"
        if report_path.exists():
            reports.append(json.loads(report_path.read_text(encoding="utf-8")))
        daily_path = report_dir / "daily_intel_brief.json"
        if daily_path.exists():
            daily_briefs.append(json.loads(daily_path.read_text(encoding="utf-8")))
        cross_day_path = report_dir / "cross_day_intel_brief.json"
        if cross_day_path.exists():
            cross_day_briefs.append(json.loads(cross_day_path.read_text(encoding="utf-8")))
        theme_tracking_path = report_dir / "theme_tracking_brief.json"
        if theme_tracking_path.exists():
            theme_tracking_briefs.append(json.loads(theme_tracking_path.read_text(encoding="utf-8")))

    return ThemeDossierInputs(
        date_range=(dates[0], dates[-1]),
        reports=reports,
        daily_briefs=daily_briefs,
        cross_day_briefs=cross_day_briefs,
        theme_tracking_briefs=theme_tracking_briefs,
    )
