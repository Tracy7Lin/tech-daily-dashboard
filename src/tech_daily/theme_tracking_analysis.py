from __future__ import annotations

from collections import Counter

from .models import ThemeTrackingBrief


def analyze_theme_tracking(
    date_range: tuple[str, str],
    reports: list[dict],
    daily_briefs: list[dict],
    cross_day_briefs: list[dict],
) -> ThemeTrackingBrief:
    theme_counts = Counter()
    company_angles: dict[str, str] = {}
    companies_by_theme: dict[str, list[str]] = {}

    for report in reports:
        for theme in report.get("hottest_topics", []):
            theme_counts[theme] += 1
        for cluster in report.get("topic_clusters", []):
            title = cluster.get("title", "")
            if not title:
                continue
            companies_by_theme.setdefault(title, [])
            for entry in cluster.get("entries", []):
                company = entry.get("raw", {}).get("company_name", "")
                angle = entry.get("comparison_angle", "")
                if company and company not in companies_by_theme[title]:
                    companies_by_theme[title].append(company)
                if company and angle and company not in company_angles:
                    company_angles[company] = angle

    for brief in daily_briefs:
        for theme in brief.get("top_content_themes", []):
            theme_counts[theme] += 1
    for brief in cross_day_briefs:
        for theme in brief.get("warming_themes", []):
            theme_counts[theme] += 2

    candidate_themes = [theme for theme, _ in theme_counts.most_common(3)]
    primary_theme = candidate_themes[0] if candidate_themes else ""
    participating_companies = companies_by_theme.get(primary_theme, [])
    next_day_theme_focus = [primary_theme] if primary_theme else []
    summary_companies = "、".join(participating_companies[:3]) or "相关公司"
    theme_summary = (
        f"{primary_theme} 是最近几天最值得继续跟踪的专题，当前重点集中在 {summary_companies} 的持续参与。"
        if primary_theme
        else ""
    )
    if len(participating_companies) >= 2:
        theme_evolution = "这个专题最近几天持续出现，且参与公司开始形成差异化切入。"
    elif primary_theme:
        theme_evolution = "这个专题最近几天持续出现，但目前仍以单一公司动作为主。"
    else:
        theme_evolution = ""

    return ThemeTrackingBrief(
        date_range=date_range,
        candidate_themes=candidate_themes,
        primary_theme=primary_theme,
        theme_summary=theme_summary,
        participating_companies=participating_companies,
        company_angles={company: company_angles.get(company, "") for company in participating_companies},
        theme_evolution=theme_evolution,
        continue_tracking=bool(primary_theme and len(participating_companies) >= 1),
        next_day_theme_focus=next_day_theme_focus,
        mode_used="hybrid",
    )
