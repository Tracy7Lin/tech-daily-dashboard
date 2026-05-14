from __future__ import annotations

from .models import DailyIntelBrief


def analyze_daily_intel(report: dict, health_snapshot: dict) -> DailyIntelBrief:
    ops = health_snapshot.get("ops_status_analysis", {})
    themes = report.get("hottest_topics", [])[:3]
    source_risks = [item.get("company_slug", "") for item in ops.get("high_priority", [])[:3] if item.get("company_slug")]
    recoveries = [
        item.get("company_slug", "")
        for item in ops.get("recently_recovered", [])[:3]
        if item.get("company_slug")
    ]
    watchlist = list(dict.fromkeys(themes + source_risks))[:4]
    return DailyIntelBrief(
        report_date=report.get("date", ""),
        editorial_signal=report.get("headline", ""),
        ops_signal=ops.get("operator_brief", "当前无额外运维判断。"),
        top_content_themes=themes,
        watchlist=watchlist,
        source_risks=source_risks,
        recoveries=recoveries,
        tomorrow_focus=watchlist[:3],
        mode_used="hybrid",
    )
