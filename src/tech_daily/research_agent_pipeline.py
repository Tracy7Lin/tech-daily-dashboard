from __future__ import annotations

from pathlib import Path

from .llm_client import LLMClient
from .research_agent_context_builder import build_research_context
from .research_agent_input import load_research_agent_inputs
from .research_agent_response import ResearchAgentResponder
from .settings import DEFAULT_SETTINGS
from .research_agent_tool_runner import run_research_agent_tool
from .research_agent_understanding import resolve_runtime_question_understanding


def _build_responder() -> ResearchAgentResponder:
    client = _build_client()
    return ResearchAgentResponder(mode=DEFAULT_SETTINGS.research_mode, client=client)


def _build_client() -> LLMClient:
    return LLMClient(
        api_url=DEFAULT_SETTINGS.llm_api_url,
        api_key=DEFAULT_SETTINGS.llm_api_key,
        model=DEFAULT_SETTINGS.llm_model,
        timeout_seconds=DEFAULT_SETTINGS.llm_timeout_seconds,
    )


def run_research_agent(
    site_dir: Path,
    data_dir: Path,
    report_date: str,
    question: str,
    history: list[dict] | None = None,
) -> dict:
    inputs = load_research_agent_inputs(site_dir, data_dir, report_date)
    responder = _build_responder()
    companies = [
        report_item.get("company_name", "")
        for report_item in (inputs.report or {}).get("company_reports", [])
        if report_item.get("company_name")
    ] or list((inputs.theme_dossier or {}).get("company_positions", {}).keys())
    primary_theme = (inputs.theme_dossier or {}).get("primary_theme", "") or (inputs.theme_tracking_brief or {}).get("primary_theme", "")
    understanding = resolve_runtime_question_understanding(
        question,
        companies,
        primary_theme,
        mode=DEFAULT_SETTINGS.research_mode,
        client=responder.client if isinstance(responder.client, LLMClient) else None,
        history=history,
    )
    tool_result = {}
    if understanding.requested_tool:
        tool_result = run_research_agent_tool(
            understanding.requested_tool,
            report_date=report_date,
            site_dir=site_dir,
            data_dir=data_dir,
        )
    context = build_research_context(
        question,
        understanding.question_type,
        understanding.entity,
        inputs,
        explanation_dimension=understanding.explanation_dimension,
        question_scope=understanding.question_scope,
        needs_general_knowledge=understanding.needs_general_knowledge,
        tool_result=tool_result,
        selector_client=responder.client if isinstance(responder.client, LLMClient) else None,
    )
    context["question_understanding"] = {
        "question_type": understanding.question_type,
        "entity": understanding.entity,
        "explanation_dimension": understanding.explanation_dimension,
        "resolved_theme": understanding.resolved_theme,
        "resolved_company": understanding.resolved_company,
        "question_scope": understanding.question_scope,
        "needs_general_knowledge": understanding.needs_general_knowledge,
        "confidence": understanding.confidence,
        "requested_tool": understanding.requested_tool,
        "assumption_used": understanding.assumption_used,
    }
    response = responder.answer(context, history=history)
    response.setdefault("question_type", understanding.question_type)
    response.setdefault("question_scope", understanding.question_scope)
    return response
