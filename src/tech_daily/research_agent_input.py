from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResearchAgentInputs:
    report_date: str
    report: dict
    daily_intel_brief: dict
    cross_day_intel_brief: dict
    theme_tracking_brief: dict
    theme_dossier: dict
    health_snapshot: dict


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_research_agent_inputs(site_dir: Path, data_dir: Path, report_date: str) -> ResearchAgentInputs:
    daily_dir = site_dir / report_date
    return ResearchAgentInputs(
        report_date=report_date,
        report=_load_json(daily_dir / "report.json"),
        daily_intel_brief=_load_json(daily_dir / "daily_intel_brief.json"),
        cross_day_intel_brief=_load_json(daily_dir / "cross_day_intel_brief.json"),
        theme_tracking_brief=_load_json(daily_dir / "theme_tracking_brief.json"),
        theme_dossier=_load_json(daily_dir / "theme_dossier.json"),
        health_snapshot=_load_json(data_dir / "health_snapshot.json"),
    )
