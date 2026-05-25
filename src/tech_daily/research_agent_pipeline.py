from __future__ import annotations

from pathlib import Path

from .chat_agent_analysis import understand_chat_question
from .llm_client import LLMClient
from .research_agent_context_builder import build_research_context
from .research_agent_input import load_research_agent_inputs
from .research_agent_response import ResearchAgentResponder
from .settings import DEFAULT_SETTINGS


def _build_responder() -> ResearchAgentResponder:
    client = LLMClient(
        api_url=DEFAULT_SETTINGS.llm_api_url,
        api_key=DEFAULT_SETTINGS.llm_api_key,
        model=DEFAULT_SETTINGS.llm_model,
        timeout_seconds=DEFAULT_SETTINGS.llm_timeout_seconds,
    )
    return ResearchAgentResponder(mode=DEFAULT_SETTINGS.research_mode, client=client)


def run_research_agent(
    site_dir: Path,
    data_dir: Path,
    report_date: str,
    question: str,
    history: list[dict] | None = None,
) -> dict:
    inputs = load_research_agent_inputs(site_dir, data_dir, report_date)
    companies = [
        report_item.get("company_name", "")
        for report_item in (inputs.report or {}).get("company_reports", [])
        if report_item.get("company_name")
    ] or list((inputs.theme_dossier or {}).get("company_positions", {}).keys())
    primary_theme = (inputs.theme_dossier or {}).get("primary_theme", "") or (inputs.theme_tracking_brief or {}).get("primary_theme", "")
    understanding = understand_chat_question(question, companies, primary_theme)
    context = build_research_context(question, understanding.question_type, understanding.entity, inputs)
    context["question_understanding"] = {
        "question_type": understanding.question_type,
        "entity": understanding.entity,
        "explanation_dimension": understanding.explanation_dimension,
        "resolved_theme": understanding.resolved_theme,
        "resolved_company": understanding.resolved_company,
        "assumption_used": understanding.assumption_used,
    }
    response = _build_responder().answer(context, history=history)
    response.setdefault("question_type", understanding.question_type)
    return response
