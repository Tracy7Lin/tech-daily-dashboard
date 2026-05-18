from __future__ import annotations


def build_evidence_item(source: str, label: str, detail: str) -> dict:
    reference = {
        "theme_dossier.json": "theme-dossier",
        "theme_tracking_brief.json": "theme-tracking",
        "cross_day_intel_brief.json": "cross-day-brief",
        "health_snapshot.json": "health-snapshot",
        "report.json": "daily-report",
    }.get(source, "knowledge-layer")
    return {
        "source": source,
        "label": label,
        "detail": detail,
        "reference": reference,
    }


def build_theme_state_answer(*, primary_theme: str, theme_state: str, summary: str, tracking_decision: str) -> str:
    return f"{primary_theme or '这个主题'} 当前处于 {theme_state or '观察期'}。{summary} {tracking_decision}".strip()


def build_company_position_answer(*, primary_theme: str, company: str, position: str, tracking_decision: str) -> str:
    resolved_position = position or "持续参与但位置尚未完全稳定"
    return f"{company} 在 {primary_theme or '当前主专题'} 里目前更偏向 {resolved_position}。{tracking_decision}".strip()


def build_timeline_focus_answer(*, company: str, title: str, why_it_matters: str) -> str:
    return f"最近几天最关键的时间线信号来自 {company or '相关公司'} 的“{title or '代表事件'}”。{timeline_explanation(why_it_matters)}".strip()


def timeline_explanation(detail: str) -> str:
    if not detail:
        return ""
    detail = detail.strip()
    if detail.endswith(("。", "！", "？")):
        return detail
    return f"{detail}。"


def follow_up_suggestions_for(
    question_type: str,
    primary_theme: str,
    company_positions: dict | None = None,
    company: str = "",
) -> list[str]:
    company_positions = company_positions or {}
    if question_type == "company_position" and company:
        return [
            f"{company} 为什么会处在这个位置？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            f"{primary_theme or '这个专题'} 值得继续跟踪吗？",
        ]
    if question_type == "theme_state":
        return [
            "为什么不是 active？",
            "最近几天关键时间线说明了什么？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
        ]
    if question_type == "timeline_focus":
        return [
            f"{primary_theme or '这个主专题'} 现在怎么理解？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
            "这个专题值得继续看吗？",
        ]
    if question_type == "dossier_summary":
        return [
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
        ]
    return [
        "这个主专题现在怎么理解？",
        "最近几天关键时间线说明了什么？",
        "现在哪些信源还有问题？",
    ]


def finalize_answer_payload(
    *,
    answer: str,
    question_type: str,
    resolved_theme: str,
    resolved_company: str,
    sources_used: list[str],
    evidence_items: list[dict],
    follow_up_suggestions: list[str],
    mode_used: str,
) -> dict:
    evidence_points = [item["detail"] for item in evidence_items if item.get("detail")]
    return {
        "answer": answer.strip(),
        "question_type": question_type,
        "resolved_theme": resolved_theme,
        "resolved_company": resolved_company,
        "sources_used": sources_used,
        "evidence_items": evidence_items,
        "evidence_points": evidence_points,
        "follow_up_suggestions": follow_up_suggestions,
        "mode_used": mode_used,
    }
