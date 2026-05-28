"""Preview/fallback chat pipeline for embedded static pages.

This module intentionally sits below the runtime research assistant. It builds
the static response bank used when the local runtime chat service is not
available, and should be treated as a compatibility layer rather than a second
agent mainline.
"""

from __future__ import annotations

from pathlib import Path

from .chat_agent_input import build_chat_agent_inputs_from_report
from .models import DailyReport
from .chat_agent_response import ChatAgentResponder, build_chat_context, build_chat_response_bank
from .settings import DEFAULT_SETTINGS


def run_chat_agent(
    site_dir: Path,
    report_date: str,
    question: str,
    data_dir: Path | None = None,
    history: list[dict] | None = None,
) -> dict:
    from .research_agent_pipeline import run_research_agent

    return run_research_agent(
        site_dir=site_dir,
        data_dir=data_dir or Path(DEFAULT_SETTINGS.data_output_dir),
        report_date=report_date,
        question=question,
        history=history,
    )


def build_embedded_chat_context(report: DailyReport) -> dict:
    inputs = build_chat_agent_inputs_from_report(report)
    context = build_chat_context(inputs)
    responder = ChatAgentResponder(mode="rule", client=None)
    response_bank = build_chat_response_bank(context, responder)
    context.update(
        {
            "follow_up_suggestions": response_bank["dossier_summary"].get("follow_up_suggestions", []),
            "runtime_chat": {
                **context.get("runtime_chat", {}),
                "mode": "runtime-first",
            },
            "response_bank": response_bank,
            "mode_used": "preview",
        }
    )
    context.pop("_research_inputs", None)
    return context
