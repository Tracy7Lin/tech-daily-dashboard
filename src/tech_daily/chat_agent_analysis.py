from __future__ import annotations

import re


def normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_chat_question(question: str, companies: list[str], primary_theme: str) -> tuple[str, str]:
    normalized = normalize_question(question)
    lowered = normalized.lower()

    if any(token in normalized for token in ("时间线", "演化", "关键事件")):
        return "timeline_focus", primary_theme

    if any(token in lowered for token in ("emerging", "active", "fragmenting", "cooling")) or "阶段" in normalized:
        return "theme_state", primary_theme

    if any(token in normalized for token in ("怎么理解", "值得跟踪", "值得继续跟踪", "主专题现在")):
        return "dossier_summary", primary_theme

    for company in companies:
        if company and company.lower() in lowered and any(token in normalized for token in ("位置", "角色", "专题里")):
            return "company_position", company
        if company and company.lower() in lowered:
            return "company_focus", company

    if any(token in normalized for token in ("信源", "抓取", "异常", "问题", "恢复", "运维")):
        return "ops_status", ""

    if primary_theme and primary_theme in normalized:
        return "theme_focus", primary_theme

    if any(token in normalized for token in ("主题", "专题")):
        return "theme_focus", primary_theme

    if any(token in normalized for token in ("今天", "关注", "主线", "值得看", "总结", "重点")):
        return "daily_summary", ""

    return "out_of_scope", ""
