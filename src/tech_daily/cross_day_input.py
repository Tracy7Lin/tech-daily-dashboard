from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(slots=True)
class CrossDayInputs:
    date_range: tuple[str, str]
    reports: list[dict]
    intel_briefs: list[dict]
    snapshots: list[dict]


def load_cross_day_inputs(site_dir: Path, snapshot_history_dir: Path, end_date: str, days: int) -> CrossDayInputs:
    end_day = date.fromisoformat(end_date)
    dates = [(end_day - timedelta(days=offset)).isoformat() for offset in reversed(range(days))]

    reports: list[dict] = []
    intel_briefs: list[dict] = []
    snapshots: list[dict] = []
    for date_text in dates:
        report_path = site_dir / date_text / "report.json"
        if report_path.exists():
            reports.append(json.loads(report_path.read_text(encoding="utf-8")))

        intel_path = site_dir / date_text / "daily_intel_brief.json"
        if intel_path.exists():
            intel_briefs.append(json.loads(intel_path.read_text(encoding="utf-8")))

        snapshot_path = snapshot_history_dir / f"{date_text}.json"
        if snapshot_path.exists():
            snapshots.append(json.loads(snapshot_path.read_text(encoding="utf-8")))

    return CrossDayInputs(
        date_range=(dates[0], dates[-1]),
        reports=reports,
        intel_briefs=intel_briefs,
        snapshots=snapshots,
    )
