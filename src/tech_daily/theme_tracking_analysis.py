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

    return ThemeTrackingBrief(
        date_range=date_range,
        candidate_themes=candidate_themes,
        primary_theme=primary_theme,
        theme_summary=f"{primary_theme} 是最近几天最值得继续跟踪的专题。" if primary_theme else "",
        participating_companies=participating_companies,
        company_angles={company: company_angles.get(company, "") for company in participating_companies},
        theme_evolution="该专题最近几天持续出现，值得继续观察。" if primary_theme else "",
        continue_tracking=bool(primary_theme and len(participating_companies) >= 1),
        next_day_theme_focus=next_day_theme_focus,
        mode_used="hybrid",
    )
