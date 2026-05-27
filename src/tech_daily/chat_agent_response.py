from __future__ import annotations

from dataclasses import replace

from .chat_agent_analysis import ChatQuestionUnderstanding, classify_chat_question, understand_chat_question
from .chat_agent_input import ChatAgentInputs
from .chat_agent_memory import resolve_follow_up_route
from .llm_client import LLMClient
from .research_agent_context_builder import build_research_context
from .research_agent_input import ResearchAgentInputs, build_research_agent_inputs_from_chat_inputs
from .research_agent_response import ResearchAgentResponder as RuntimeResearchAgentResponder
from .research_assistant_policy import legacy_scope_defaults


def _select_placeholder_status(statuses: list[dict]) -> dict | None:
    if not statuses:
        return None
    statuses = sorted(
        statuses,
        key=lambda status: (
            0 if not status.get("ok", True) else 1,
            status.get("final_included_count", 0),
            status.get("date_matched_count", 0),
            status.get("kept_count", 0),
            status.get("fetched_count", 0),
        ),
    )
    return statuses[0]


def _is_stable_no_news_status(status: dict) -> bool:
    return (
        status.get("ok", False)
        and status.get("fetched_count", 0) > 0
        and status.get("kept_count", 0) > 0
        and status.get("date_matched_count", 0) == 0
        and status.get("final_included_count", 0) == 0
    )


def _is_stable_filtered_status(status: dict) -> bool:
    return (
        status.get("ok", False)
        and status.get("date_matched_count", 0) > 0
        and status.get("final_included_count", 0) == 0
    )


def _placeholder_reason(status: dict) -> str:
    company_name = status.get("company_name", "")
    source_label = status.get("source_label", "")
    message = status.get("message", "")
    lowered = message.lower()

    if "http_error:403" in lowered and company_name.lower() == "tesla":
        return "Tesla 官方新闻入口当前持续拒绝抓取请求，先保留占位，后续再评估更稳的官方接入方式。"
    if status.get("fetched_count", 0) == 0 and company_name.lower() == "xiaomi":
        return "Xiaomi Global Discover 当前以动态渲染为主，静态抓取器尚未拿到稳定文章链接，先保留占位。"
    if not status.get("ok", True):
        return f"{company_name or source_label} 当前抓取异常，建议优先检查官方入口是否可访问。"
    if status.get("fetched_count", 0) == 0:
        return f"{company_name or source_label} 当前没有抓到稳定条目，先保留占位，后续再继续调优信源。"
    return f"{company_name or source_label} 今天没有形成可发布动态，建议结合源状态继续观察。"


def _build_company_answer(company_name: str, entries: list[dict], statuses: list[dict]) -> str:
    latest_title = entries[0].get("raw", {}).get("title", "") if entries else ""
    if entries:
        return f"{company_name} 最近几天仍有动作，当前最值得看的更新是“{latest_title}”。"
    status = _select_placeholder_status(statuses)
    if status is None:
        return f"{company_name} 今天没有保留下可发布的动态。"
    if _is_stable_no_news_status(status):
        return f"{company_name} 官方信源抓取正常，但今天没有落在日报日期范围内的有效动态。"
    if _is_stable_filtered_status(status):
        return f"{company_name} 官方信源抓取正常，也抓到了同日内容，但今天没有保留下可发布条目。"
    return f"{company_name} 信源暂未稳定。{_placeholder_reason(status)}"


def build_chat_context(inputs: ChatAgentInputs) -> dict:
    company_reports = inputs.report.get("company_reports", [])
    source_statuses = inputs.report.get("source_statuses", [])
    statuses_by_company = {}
    for status in source_statuses:
        statuses_by_company.setdefault(status.get("company_slug", ""), []).append(status)
    company_answers = {}
    company_names = []
    for report in company_reports:
        company_slug = report.get("company_slug", "")
        company_name = report.get("company_name", "")
        if not company_name:
            continue
        company_names.append(company_name)
        entries = report.get("entries", [])
        company_answers[company_name.lower()] = _build_company_answer(
            company_name,
            entries,
            statuses_by_company.get(company_slug, []),
        )

    primary_theme = inputs.theme_tracking_brief.get("primary_theme", "")
    theme_dossier = {
        "primary_theme": inputs.theme_dossier_brief.get("primary_theme", ""),
        "theme_definition": inputs.theme_dossier_brief.get("theme_definition", ""),
        "theme_state": inputs.theme_dossier_brief.get("theme_state", ""),
        "theme_summary": inputs.theme_dossier_brief.get("theme_summary", ""),
        "company_positions": inputs.theme_dossier_brief.get("company_positions", {}),
        "timeline_events": inputs.theme_dossier_brief.get("timeline_events", []),
        "tracking_decision": inputs.theme_dossier_brief.get("tracking_decision", ""),
        "next_day_focus": inputs.theme_dossier_brief.get("next_day_focus", []),
    }

    return {
        "report_date": inputs.report_date,
        "daily_summary": {
            "answer": inputs.daily_brief.get("editorial_signal")
            or inputs.report.get("headline")
            or "今天暂时没有足够高价值的内容被保留下来。",
        },
        "theme_tracking": {
            "primary_theme": primary_theme,
            "answer": f"{inputs.theme_tracking_brief.get('theme_summary', '')} {inputs.theme_tracking_brief.get('theme_evolution', '')}".strip(),
            "participating_companies": inputs.theme_tracking_brief.get("participating_companies", []),
        },
        "theme_dossier": theme_dossier,
        "ops_status": {
            "answer": inputs.health_snapshot.get("ops_status_analysis", {}).get("operator_brief", "") or "当前没有额外运维提示。",
            "high_priority": [issue.get("company_slug", "") for issue in inputs.health_snapshot.get("high_priority_runtime_issues", [])],
        },
        "company_answers": company_answers,
        "companies": company_names,
        "quick_questions": [
            "今天最值得关注什么？",
            "这个主专题现在怎么理解？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            "现在哪些信源还有问题？",
        ],
        "follow_up_suggestions": [
            "OpenAI 最近几天在做什么？",
            "这个主专题现在怎么理解？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            "现在哪些信源还有问题？",
        ],
        "runtime_chat": {
            "endpoint": "/api/chat",
            "stream_endpoint": "/api/chat-stream",
            "health_endpoint": "/api/health",
            "serve_hint": "使用 python run_dashboard.py serve --port 8080 启动实时问答服务。",
        },
        "mode_used": "rule",
        "_research_inputs": build_research_agent_inputs_from_chat_inputs(inputs),
    }


def _build_runtime_context(
    question: str,
    context: dict,
    understanding: ChatQuestionUnderstanding,
) -> dict:
    inputs: ResearchAgentInputs = context["_research_inputs"]
    runtime_context = build_research_context(
        question,
        understanding.question_type,
        understanding.entity,
        inputs,
        explanation_dimension=understanding.explanation_dimension,
        question_scope=understanding.question_scope,
        needs_general_knowledge=understanding.needs_general_knowledge,
    )
    runtime_context["question_understanding"] = {
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
    return runtime_context


def _understanding_from_route(
    question: str,
    context: dict,
    route: tuple[str, str] | None,
) -> ChatQuestionUnderstanding:
    base = understand_chat_question(
        question,
        context.get("companies", []),
        context.get("theme_tracking", {}).get("primary_theme", ""),
    )
    if not route:
        return base
    question_type, entity = route
    scope, dimension = legacy_scope_defaults(question_type)
    resolved_company = entity if scope == "company" else ""
    resolved_theme = (
        context.get("theme_dossier", {}).get("primary_theme", "")
        or context.get("theme_tracking", {}).get("primary_theme", "")
    )
    if scope != "theme":
        resolved_theme = base.resolved_theme or resolved_theme
    return replace(
        base,
        question_type=question_type,
        entity=entity,
        explanation_dimension=dimension,
        resolved_theme=resolved_theme,
        resolved_company=resolved_company,
        question_scope=scope,
        needs_general_knowledge=(scope == "general"),
    )


def answer_chat_question(question: str, context: dict, route: tuple[str, str] | None = None) -> dict:
    understanding = _understanding_from_route(question, context, route)
    runtime_context = _build_runtime_context(question, context, understanding)
    responder = RuntimeResearchAgentResponder(mode="rule", client=None)
    return responder.answer(runtime_context)


def build_chat_response_bank(context: dict, responder: "ChatAgentResponder") -> dict:
    primary_theme = context.get("theme_tracking", {}).get("primary_theme", "")
    company_bank = {}
    for company in context.get("companies", []):
        company_bank[company.lower()] = responder.answer(f"{company} 最近几天在做什么？", context)

    return {
        "daily_summary": responder.answer("今天最值得关注什么？", context),
        "theme_focus": responder.answer(
            f"为什么今天的主专题是{primary_theme or '这个主题'}？",
            context,
        ),
        "dossier_summary": responder.answer("这个主专题现在怎么理解？", context),
        "theme_state": responder.answer("为什么现在是 emerging？", context),
        "timeline_focus": responder.answer("最近几天关键时间线说明了什么？", context),
        "ops_status": responder.answer("现在哪些信源还有问题？", context),
        "company_focus": company_bank,
        "company_position_answers": {
            company.lower(): responder.answer(f"{company} 在这个专题里处于什么位置？", context)
            for company in context.get("companies", [])
        },
        "out_of_scope": responder.answer("我还可以问别的吗？", context),
    }


class ChatAgentResponder:
    def __init__(self, mode: str = "rule", client: LLMClient | None = None) -> None:
        self.mode = mode
        self.client = client

    def answer(self, question: str, context: dict, history: list[dict] | None = None) -> dict:
        route = resolve_follow_up_route(
            question,
            history,
            context.get("companies", []),
            context.get("theme_tracking", {}).get("primary_theme", ""),
        )
        understanding = _understanding_from_route(question, context, route)
        runtime_context = _build_runtime_context(question, context, understanding)
        runtime_responder = RuntimeResearchAgentResponder(mode=self.mode, client=self.client)
        return runtime_responder.answer(runtime_context, history=history)

