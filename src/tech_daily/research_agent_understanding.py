from __future__ import annotations

from dataclasses import asdict

from .chat_agent_analysis import ChatQuestionUnderstanding, understand_chat_question
from .llm_client import LLMClient, LLMClientError


def _normalized_dimension(value: str) -> str:
    allowed = {"judgment", "comparison", "evolution", "evidence", "explanation"}
    return value if value in allowed else "judgment"


def _normalized_scope(value: str) -> str:
    allowed = {"report", "theme", "company", "ops", "general", "tool"}
    return value if value in allowed else "report"


def _normalized_tool(value: str) -> str:
    allowed = {"local_health_check", "report_generation", "web_search", ""}
    return value if value in allowed else ""


def _fallback_question_type(
    *,
    question_scope: str,
    explanation_dimension: str,
    resolved_company: str,
    resolved_theme: str,
    requested_tool: str,
    needs_general_knowledge: bool,
    fallback: ChatQuestionUnderstanding,
) -> str:
    if requested_tool:
        return fallback.question_type if fallback.requested_tool else "tool_request"
    if question_scope == "company":
        return "company_position" if explanation_dimension == "comparison" else "company_focus"
    if question_scope == "theme":
        if explanation_dimension == "evolution":
            return "timeline_focus"
        if fallback.question_type == "theme_state" or "state" in fallback.question_type:
            return "theme_state"
        return "dossier_summary" if resolved_theme else fallback.question_type
    if question_scope == "ops":
        return "ops_status"
    if needs_general_knowledge or question_scope == "general":
        return "general_explainer"
    if question_scope == "report":
        return "daily_summary"
    return fallback.question_type


def _build_understanding_from_payload(
    payload: dict,
    *,
    fallback: ChatQuestionUnderstanding,
    companies: list[str],
    primary_theme: str,
) -> ChatQuestionUnderstanding:
    resolved_company = ""
    entity = (payload.get("entity") or "").strip()
    target_company = (payload.get("target_company") or "").strip()
    for company in companies:
        if company.lower() in {entity.lower(), target_company.lower()}:
            resolved_company = company
            break
    resolved_theme = (payload.get("target_theme") or "").strip() or primary_theme
    requested_tool = _normalized_tool((payload.get("requested_tool") or "").strip())
    question_scope = _normalized_scope((payload.get("question_scope") or "").strip())
    explanation_dimension = _normalized_dimension((payload.get("explanation_dimension") or "").strip())
    needs_general_knowledge = bool(payload.get("needs_general_knowledge", False))
    explicit_question_type = (payload.get("question_type") or "").strip()
    if requested_tool and question_scope != "tool":
        question_scope = "tool"
    if question_scope == "company" and not resolved_company:
        return fallback
    if question_scope == "theme" and not resolved_theme:
        return fallback
    question_type = explicit_question_type or _fallback_question_type(
        question_scope=question_scope,
        explanation_dimension=explanation_dimension,
        resolved_company=resolved_company,
        resolved_theme=resolved_theme,
        requested_tool=requested_tool,
        needs_general_knowledge=needs_general_knowledge,
        fallback=fallback,
    )
    return ChatQuestionUnderstanding(
        question_type=question_type,
        entity=resolved_company or entity or fallback.entity,
        explanation_dimension=explanation_dimension,
        resolved_theme=resolved_theme,
        resolved_company=resolved_company,
        question_scope=question_scope,
        needs_general_knowledge=needs_general_knowledge,
        confidence=(payload.get("confidence") or fallback.confidence or "medium").strip(),
        requested_tool=requested_tool,
        assumption_used=(payload.get("assumption_used") or "").strip(),
    )


def resolve_runtime_question_understanding(
    question: str,
    companies: list[str],
    primary_theme: str,
    *,
    mode: str,
    client: LLMClient | None,
    history: list[dict] | None = None,
) -> ChatQuestionUnderstanding:
    fallback = understand_chat_question(question, companies, primary_theme)
    if mode == "rule" or client is None or not client.is_available():
        return fallback
    try:
        payload = client.generate_json(
            instructions=(
                "你负责理解科技日报研究助理收到的用户问题。"
                "请基于当前问题与会话语境，输出一个粗粒度理解对象。"
                "不要过度依赖固定标签；重点判断问题更偏日报、主题、公司、运维、通用知识还是工具请求。"
            ),
            input_text=(
                f"用户问题：{question}\n"
                f"最近会话：{history or []}\n"
                f"当前主专题：{primary_theme}\n"
                f"已知公司：{companies}\n"
                f"规则 fallback：{asdict(fallback)}\n"
            ),
            schema_name="runtime_question_understanding",
            schema={
                "type": "object",
                "properties": {
                    "question_type": {"type": "string"},
                    "question_scope": {"type": "string"},
                    "explanation_dimension": {"type": "string"},
                    "entity": {"type": "string"},
                    "target_company": {"type": "string"},
                    "target_theme": {"type": "string"},
                    "needs_general_knowledge": {"type": "boolean"},
                    "requested_tool": {"type": "string"},
                    "confidence": {"type": "string"},
                    "assumption_used": {"type": "string"},
                },
                "required": [
                    "question_scope",
                    "explanation_dimension",
                    "needs_general_knowledge",
                    "requested_tool",
                    "confidence",
                ],
                "additionalProperties": False,
            },
        )
    except (LLMClientError, KeyError, TypeError, ValueError):
        return fallback
    return _build_understanding_from_payload(
        payload,
        fallback=fallback,
        companies=companies,
        primary_theme=primary_theme,
    )
