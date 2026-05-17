from __future__ import annotations


def trim_history(messages: list[dict] | None, limit: int = 6) -> list[dict]:
    if not messages:
        return []
    normalized = [message for message in messages if isinstance(message, dict)]
    return normalized[-limit:]


def resolve_follow_up_route(
    question: str,
    messages: list[dict] | None,
    companies: list[str],
    primary_theme: str,
) -> tuple[str, str] | None:
    history = trim_history(messages)
    if not history:
        return None

    normalized = (question or "").strip()
    lowered = normalized.lower()
    assistant_turns = [item for item in history if item.get("role") == "assistant"]
    last_assistant = assistant_turns[-1] if assistant_turns else {}
    last_question_type = last_assistant.get("question_type", "")
    last_theme = last_assistant.get("resolved_theme") or primary_theme
    last_company = last_assistant.get("resolved_company", "")

    company_match = next((company for company in companies if company and company.lower() in lowered), "")
    if company_match and any(token in normalized for token in ("那", "呢", "角色", "位置")):
        if last_question_type in {"dossier_summary", "theme_state", "timeline_focus", "theme_focus", "company_position"}:
            return "company_position", company_match
        return "company_focus", company_match

    if any(token in normalized for token in ("继续说时间线", "继续说", "接着说时间线")):
        return "timeline_focus", last_theme

    if any(token in normalized for token in ("为什么", "为何")):
        if last_question_type in {"theme_state", "dossier_summary"}:
            return last_question_type, last_theme
        if last_question_type == "company_position" and last_company:
            return "company_position", last_company
        if last_question_type == "timeline_focus":
            return "timeline_focus", last_theme

    if any(token in normalized for token in ("还有别的", "还有别的吗", "还有吗")):
        if last_question_type in {"company_position", "company_focus"} and last_theme:
            return "dossier_summary", last_theme
        if last_question_type in {"timeline_focus", "theme_state", "dossier_summary"} and last_theme:
            return last_question_type, last_theme

    if normalized in {"继续", "接着说", "展开说说"}:
        if last_question_type == "timeline_focus" and last_theme:
            return "timeline_focus", last_theme
        if last_question_type in {"dossier_summary", "theme_state", "theme_focus"} and last_theme:
            return "dossier_summary", last_theme
        if last_question_type == "company_position" and last_company:
            return "company_position", last_company
        if last_question_type == "company_focus" and last_company:
            return "company_focus", last_company

    if normalized in {"那呢", "那怎么样", "那怎么办"} and last_company:
        return "company_focus", last_company

    return None
