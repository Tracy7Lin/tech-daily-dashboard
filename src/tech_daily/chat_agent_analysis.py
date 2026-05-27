from __future__ import annotations

import re
from dataclasses import asdict
from dataclasses import dataclass


def normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class ChatQuestionUnderstanding:
    question_type: str
    entity: str
    explanation_dimension: str
    resolved_theme: str
    resolved_company: str
    question_scope: str = "report"
    needs_general_knowledge: bool = False
    confidence: str = "medium"
    requested_tool: str = ""
    assumption_used: str = ""


def serialize_question_understanding(understanding: ChatQuestionUnderstanding) -> dict:
    return asdict(understanding)


def understand_chat_question(question: str, companies: list[str], primary_theme: str) -> ChatQuestionUnderstanding:
    normalized = normalize_question(question)
    lowered = normalized.lower()

    if any(token in normalized for token in ("健康检查", "health-check", "运行检查", "检查信源", "诊断一下")):
        return ChatQuestionUnderstanding(
            question_type="ops_status",
            entity="",
            explanation_dimension="evidence",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="tool",
            requested_tool="local_health_check",
            confidence="high",
        )

    if any(token in normalized for token in ("重新生成日报", "刷新日报", "重新跑日报", "重新生成今天", "重新生成这期")):
        return ChatQuestionUnderstanding(
            question_type="daily_summary",
            entity="",
            explanation_dimension="judgment",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="tool",
            requested_tool="report_generation",
            confidence="high",
        )

    if any(token in normalized for token in ("时间线", "演化", "关键事件")):
        return ChatQuestionUnderstanding(
            question_type="timeline_focus",
            entity=primary_theme,
            explanation_dimension="evolution",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="theme",
            confidence="high",
        )

    if any(token in lowered for token in ("emerging", "active", "fragmenting", "cooling")) or "阶段" in normalized:
        return ChatQuestionUnderstanding(
            question_type="theme_state",
            entity=primary_theme,
            explanation_dimension="judgment",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="theme",
            confidence="high",
        )

    if any(token in normalized for token in ("怎么理解", "值得跟踪", "值得继续跟踪", "值得继续看", "主专题现在")):
        return ChatQuestionUnderstanding(
            question_type="dossier_summary",
            entity=primary_theme,
            explanation_dimension="judgment",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="theme",
            confidence="medium",
        )

    if any(token in normalized for token in ("什么是", "是什么", "通常适合", "适合用在", "原理", "区别", "如何理解")):
        return ChatQuestionUnderstanding(
            question_type="general_explainer",
            entity="",
            explanation_dimension="explanation",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="general",
            needs_general_knowledge=True,
            confidence="low",
        )

    for company in companies:
        if company and company.lower() in lowered and any(token in normalized for token in ("位置", "角色", "专题里")):
            return ChatQuestionUnderstanding(
                question_type="company_position",
                entity=company,
                explanation_dimension="comparison",
                resolved_theme=primary_theme,
                resolved_company=company,
                question_scope="company",
                confidence="high",
            )
        if company and company.lower() in lowered:
            return ChatQuestionUnderstanding(
                question_type="company_focus",
                entity=company,
                explanation_dimension="judgment",
                resolved_theme=primary_theme,
                resolved_company=company,
                question_scope="company",
                confidence="medium",
            )

    if any(token in normalized for token in ("信源", "抓取", "异常", "问题", "恢复", "运维")):
        return ChatQuestionUnderstanding(
            question_type="ops_status",
            entity="",
            explanation_dimension="evidence",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="ops",
            confidence="high",
        )

    if primary_theme and primary_theme in normalized:
        return ChatQuestionUnderstanding(
            question_type="theme_focus",
            entity=primary_theme,
            explanation_dimension="judgment",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="theme",
            confidence="medium",
        )

    if any(token in normalized for token in ("主题", "专题")):
        return ChatQuestionUnderstanding(
            question_type="theme_focus",
            entity=primary_theme,
            explanation_dimension="judgment",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="theme",
            confidence="low",
            assumption_used="defaulted_to_primary_theme",
        )

    if any(token in normalized for token in ("今天", "关注", "主线", "值得看", "总结", "重点")):
        return ChatQuestionUnderstanding(
            question_type="daily_summary",
            entity="",
            explanation_dimension="judgment",
            resolved_theme=primary_theme,
            resolved_company="",
            question_scope="report",
            confidence="medium",
        )

    return ChatQuestionUnderstanding(
        question_type="out_of_scope",
        entity="",
        explanation_dimension="judgment",
        resolved_theme=primary_theme,
        resolved_company="",
        question_scope="general",
        needs_general_knowledge=True,
        confidence="low",
    )


def classify_chat_question(question: str, companies: list[str], primary_theme: str) -> tuple[str, str]:
    understanding = understand_chat_question(question, companies, primary_theme)
    return understanding.question_type, understanding.entity
