from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AgentInputs:
    report: dict
    health_snapshot: dict


def load_agent_inputs(report_path: Path, snapshot_path: Path) -> AgentInputs:
    return AgentInputs(
        report=json.loads(report_path.read_text(encoding="utf-8")),
        health_snapshot=json.loads(snapshot_path.read_text(encoding="utf-8")),
    )
