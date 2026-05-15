from __future__ import annotations

import re


def normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_chat_question(question: str, companies: list[str], primary_theme: str) -> tuple[str, str]:
    normalized = normalize_question(question)
    lowered = normalized.lower()

    for company in companies:
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
