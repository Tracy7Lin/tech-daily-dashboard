from __future__ import annotations

from pathlib import Path

from .chat_agent_response import ChatAgentResponder, build_chat_response_bank
from .chat_agent_input import ChatAgentInputs, load_chat_agent_inputs
from .chat_agent_response import build_chat_context
from .llm_client import LLMClient
from .models import DailyReport
from .settings import DEFAULT_SETTINGS


def run_chat_agent(site_dir: Path, report_date: str, question: str, data_dir: Path | None = None) -> dict:
    inputs = load_chat_agent_inputs(site_dir, report_date, data_dir=data_dir)
    context = build_chat_context(inputs)
    responder = _build_responder()
    return responder.answer(question, context)


def _build_responder() -> ChatAgentResponder:
    client = LLMClient(
        api_url=DEFAULT_SETTINGS.llm_api_url,
        api_key=DEFAULT_SETTINGS.llm_api_key,
        model=DEFAULT_SETTINGS.llm_model,
        timeout_seconds=DEFAULT_SETTINGS.llm_timeout_seconds,
    )
    return ChatAgentResponder(mode=DEFAULT_SETTINGS.editorial_mode, client=client)


def build_embedded_chat_context(report: DailyReport) -> dict:
    inputs = ChatAgentInputs(
        report_date=report.date,
        report=report.to_dict(),
        daily_brief=report.agent_brief,
        cross_day_brief=report.cross_day_brief,
        theme_tracking_brief=report.theme_tracking_brief,
        theme_dossier_brief=report.theme_dossier_brief,
        health_snapshot={
            "ops_status_analysis": {"operator_brief": report.agent_brief.get("ops_signal", "")},
            "high_priority_runtime_issues": [],
        },
    )
    context = build_chat_context(inputs)
    responder = ChatAgentResponder(mode="rule", client=None)
    response_bank = build_chat_response_bank(context, responder)
    return {
        **context,
        "response_bank": response_bank,
    }
