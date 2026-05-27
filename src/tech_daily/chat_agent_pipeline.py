from __future__ import annotations

from pathlib import Path

from .chat_agent_analysis import understand_chat_question
from .models import DailyReport
from .research_agent_context_builder import build_research_context
from .research_agent_input import build_research_agent_inputs_from_report
from .research_agent_response import ResearchAgentResponder
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


def _answer_preview_question(
    question: str,
    *,
    responder,
    report: DailyReport,
    companies: list[str],
    primary_theme: str,
) -> dict:
    inputs = build_research_agent_inputs_from_report(report)
    understanding = understand_chat_question(question, companies, primary_theme)
    context = build_research_context(
        question,
        understanding.question_type,
        understanding.entity,
        inputs,
        explanation_dimension=understanding.explanation_dimension,
        question_scope=understanding.question_scope,
        needs_general_knowledge=understanding.needs_general_knowledge,
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
        "requested_tool": "",
        "assumption_used": understanding.assumption_used,
    }
    return responder.answer(context)


def build_embedded_chat_context(report: DailyReport) -> dict:
    primary_theme = (report.theme_dossier_brief or {}).get("primary_theme", "") or (report.theme_tracking_brief or {}).get("primary_theme", "")
    companies = [
        item.get("company_name", "")
        for item in (report.to_dict() or {}).get("company_reports", [])
        if item.get("company_name")
    ] or list((report.theme_dossier_brief or {}).get("company_positions", {}).keys())
    responder = ResearchAgentResponder(mode="rule", client=None)

    quick_questions = [
        "今天最值得关注什么？",
        "这个主专题现在怎么理解？",
        "为什么现在是 emerging？",
        "最近几天关键时间线说明了什么？",
        "现在哪些信源还有问题？",
    ]
    response_bank = {
        "daily_summary": _answer_preview_question(
            "今天最值得关注什么？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
        "theme_focus": _answer_preview_question(
            f"为什么今天的主专题是{primary_theme or '这个主题'}？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
        "dossier_summary": _answer_preview_question(
            "这个主专题现在怎么理解？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
        "theme_state": _answer_preview_question(
            "为什么现在是 emerging？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
        "timeline_focus": _answer_preview_question(
            "最近几天关键时间线说明了什么？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
        "ops_status": _answer_preview_question(
            "现在哪些信源还有问题？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
        "company_focus": {},
        "company_position_answers": {},
        "out_of_scope": _answer_preview_question(
            "我还可以问别的吗？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        ),
    }
    for company in companies:
        key = company.lower()
        response_bank["company_focus"][key] = _answer_preview_question(
            f"{company} 最近几天在做什么？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        )
        response_bank["company_position_answers"][key] = _answer_preview_question(
            f"{company} 在这个专题里处于什么位置？",
            responder=responder,
            report=report,
            companies=companies,
            primary_theme=primary_theme,
        )

    return {
        "report_date": report.date,
        "companies": companies,
        "quick_questions": quick_questions,
        "follow_up_suggestions": response_bank["dossier_summary"].get("follow_up_suggestions", []),
        "theme_tracking": {
            "primary_theme": primary_theme,
        },
        "theme_dossier": report.theme_dossier_brief or {},
        "runtime_chat": {
            "endpoint": "/api/chat",
            "stream_endpoint": "/api/chat-stream",
            "health_endpoint": "/api/health",
            "serve_hint": "使用 python run_dashboard.py serve --port 8080 启动实时问答服务。",
            "mode": "runtime-first",
        },
        "response_bank": response_bank,
        "mode_used": "preview",
    }
