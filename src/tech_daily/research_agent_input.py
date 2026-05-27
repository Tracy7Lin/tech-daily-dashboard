from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_agent_input import ChatAgentInputs
    from .models import DailyReport


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


def build_research_agent_inputs_from_report(report: "DailyReport") -> ResearchAgentInputs:
    health_snapshot = {
        "ops_status_analysis": {
            "operator_brief": (report.agent_brief or {}).get("ops_signal", ""),
        },
        "high_priority_runtime_issues": [],
        "recently_recovered_runtime_issues": [],
    }
    return ResearchAgentInputs(
        report_date=report.date,
        report=report.to_dict(),
        daily_intel_brief=report.agent_brief or {},
        cross_day_intel_brief=report.cross_day_brief or {},
        theme_tracking_brief=report.theme_tracking_brief or {},
        theme_dossier=report.theme_dossier_brief or {},
        health_snapshot=health_snapshot,
    )


def build_research_agent_inputs_from_chat_inputs(inputs: "ChatAgentInputs") -> ResearchAgentInputs:
    return ResearchAgentInputs(
        report_date=inputs.report_date,
        report=inputs.report or {},
        daily_intel_brief=inputs.daily_brief or {},
        cross_day_intel_brief=inputs.cross_day_brief or {},
        theme_tracking_brief=inputs.theme_tracking_brief or {},
        theme_dossier=inputs.theme_dossier_brief or {},
        health_snapshot=inputs.health_snapshot or {},
    )
