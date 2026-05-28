from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import DailyReport
from .settings import DEFAULT_SETTINGS


@dataclass(frozen=True)
class ChatAgentInputs:
    report_date: str
    report: dict
    daily_brief: dict
    cross_day_brief: dict
    theme_tracking_brief: dict
    theme_dossier_brief: dict
    health_snapshot: dict


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_chat_agent_inputs(site_dir: Path, report_date: str, data_dir: Path | None = None) -> ChatAgentInputs:
    daily_dir = site_dir / report_date
    resolved_data_dir = data_dir or Path(DEFAULT_SETTINGS.data_output_dir)
    return ChatAgentInputs(
        report_date=report_date,
        report=_read_json(daily_dir / "report.json"),
        daily_brief=_read_json(daily_dir / "daily_intel_brief.json"),
        cross_day_brief=_read_json(daily_dir / "cross_day_intel_brief.json"),
        theme_tracking_brief=_read_json(daily_dir / "theme_tracking_brief.json"),
        theme_dossier_brief=_read_json(daily_dir / "theme_dossier.json"),
        health_snapshot=_read_json(resolved_data_dir / "health_snapshot.json"),
    )


def build_chat_agent_inputs_from_report(report: DailyReport) -> ChatAgentInputs:
    return ChatAgentInputs(
        report_date=report.date,
        report=report.to_dict(),
        daily_brief=report.agent_brief or {},
        cross_day_brief=report.cross_day_brief or {},
        theme_tracking_brief=report.theme_tracking_brief or {},
        theme_dossier_brief=report.theme_dossier_brief or {},
        health_snapshot={},
    )
