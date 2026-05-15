from __future__ import annotations

from collections import Counter

from .models import CrossDayIntelBrief


def analyze_cross_day_intel(
    date_range: tuple[str, str],
    reports: list[dict],
    intel_briefs: list[dict],
    snapshots: list[dict],
) -> CrossDayIntelBrief:
    del intel_briefs

    theme_counts = Counter(theme for report in reports for theme in report.get("hottest_topics", []))
    company_counts = Counter(company for report in reports for company in report.get("active_companies", []))
    persistent_risks = Counter(
        issue.get("company_slug", "")
        for snapshot in snapshots
        for issue in snapshot.get("high_priority_runtime_issues", [])
        if issue.get("company_slug")
    )

    recoveries: list[str] = []
    for snapshot in snapshots:
        for issue in snapshot.get("recently_recovered_runtime_issues", []):
            slug = issue.get("company_slug", "")
            if slug and slug not in recoveries:
                recoveries.append(slug)

    steady_companies = [name for name, count in company_counts.items() if count >= 2]
    swing_companies = [name for name, count in company_counts.items() if count == 1]
    warming_themes = [name for name, count in theme_counts.items() if count >= 2]
    cooling_themes = [name for name, count in theme_counts.items() if count == 1]
    persistent_source_risks = [name for name, count in persistent_risks.items() if count >= 2]
    watchlist = list(dict.fromkeys(warming_themes + steady_companies + persistent_source_risks))[:5]

    return CrossDayIntelBrief(
        date_range=date_range,
        warming_themes=warming_themes[:3],
        cooling_themes=cooling_themes[:3],
        steady_companies=steady_companies[:4],
        swing_companies=swing_companies[:4],
        persistent_source_risks=persistent_source_risks[:4],
        recent_source_recoveries=recoveries[:4],
        watchlist=watchlist,
        next_day_focus=watchlist[:3],
        mode_used="hybrid",
    )
