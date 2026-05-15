from __future__ import annotations

from collections import Counter

from .models import ThemeDossierBrief, ThemeDossierTimelineEvent


def _resolve_primary_theme(reports: list[dict], theme_tracking_briefs: list[dict]) -> str:
    for brief in reversed(theme_tracking_briefs):
        primary_theme = brief.get("primary_theme", "")
        if primary_theme:
            return primary_theme
    theme_counts = Counter()
    for report in reports:
        for theme in report.get("hottest_topics", []):
            theme_counts[theme] += 1
    return theme_counts.most_common(1)[0][0] if theme_counts else ""


def _collect_theme_entries(reports: list[dict], primary_theme: str) -> list[dict]:
    events: list[dict] = []
    for report in reports:
        date_text = report.get("date", "")
        for cluster in report.get("topic_clusters", []):
            if cluster.get("title", "") != primary_theme:
                continue
            for entry in cluster.get("entries", []):
                raw = entry.get("raw", {})
                events.append(
                    {
                        "date": date_text,
                        "company": raw.get("company_name", ""),
                        "title": raw.get("title", ""),
                        "angle": entry.get("comparison_angle", ""),
                    }
                )
    return events


def _determine_theme_state(date_range: tuple[str, str], events: list[dict], company_positions: dict[str, str]) -> str:
    if not events:
        return ""
    unique_dates = {event["date"] for event in events if event["date"]}
    unique_companies = {event["company"] for event in events if event["company"]}
    unique_angles = {angle for angle in company_positions.values() if angle}

    if len(unique_dates) <= 1:
        return "emerging"
    if date_range[1] not in unique_dates:
        return "cooling"
    if len(unique_companies) >= 2 and len(unique_angles) >= 2:
        return "fragmenting"
    if len(unique_companies) >= 2 or len(unique_dates) >= 2:
        return "active"
    return "emerging"


def _select_timeline_events(events: list[dict]) -> list[ThemeDossierTimelineEvent]:
    if not events:
        return []
    ordered: list[dict] = []
    seen_keys = set()
    for event in events:
        key = (event["date"], event["company"], event["title"])
        if key in seen_keys:
            continue
        ordered.append(event)
        seen_keys.add(key)
    ordered = ordered[:6]

    return [
        ThemeDossierTimelineEvent(
            date=event["date"],
            company=event["company"],
            title=event["title"],
            why_it_matters=(
                f"{event['company']} 正在沿着 {event['angle']} 推进这一主题。"
                if event["company"] and event["angle"]
                else "这是最近几天推动该主题演化的代表事件。"
            ),
        )
        for event in ordered
    ]


def analyze_theme_dossier(
    date_range: tuple[str, str],
    reports: list[dict],
    daily_briefs: list[dict],
    cross_day_briefs: list[dict],
    theme_tracking_briefs: list[dict],
) -> ThemeDossierBrief:
    primary_theme = _resolve_primary_theme(reports, theme_tracking_briefs)
    if not primary_theme:
        return ThemeDossierBrief(date_range=date_range, mode_used="hybrid")

    events = _collect_theme_entries(reports, primary_theme)
    participating_companies = list(dict.fromkeys(event["company"] for event in events if event["company"]))
    company_positions = {}
    for event in events:
        company = event["company"]
        if company and company not in company_positions and event["angle"]:
            company_positions[company] = event["angle"]

    theme_state = _determine_theme_state(date_range, events, company_positions)
    timeline_events = _select_timeline_events(events)
    companies_text = "、".join(participating_companies[:3]) or "相关公司"
    theme_definition = f"{primary_theme} 主题聚焦于不同公司如何把这一方向推进到更具体的产品、平台或治理动作中。"
    theme_summary = f"{primary_theme} 仍是最近几天最值得继续看的主专题，当前重点集中在 {companies_text} 的持续参与。"
    tracking_decision = (
        f"建议继续跟踪 {primary_theme}，因为它已经从单点动作演化成最近几天持续出现的主线。"
        if theme_state in {"active", "fragmenting"}
        else f"{primary_theme} 仍值得继续观察，但目前更像刚冒头的主题。"
        if theme_state == "emerging"
        else f"{primary_theme} 的热度已有回落迹象，后续可降低优先级。"
    )
    next_day_focus = [primary_theme, *participating_companies[:2]]

    return ThemeDossierBrief(
        date_range=date_range,
        primary_theme=primary_theme,
        theme_definition=theme_definition,
        theme_state=theme_state,
        theme_summary=theme_summary,
        participating_companies=participating_companies,
        company_positions=company_positions,
        timeline_events=timeline_events,
        tracking_decision=tracking_decision,
        next_day_focus=next_day_focus,
        mode_used="hybrid",
    )
