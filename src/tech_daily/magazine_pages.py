from __future__ import annotations

from .models import DailyReport


def build_magazine_pages(report: DailyReport) -> dict:
    tracking = report.theme_tracking_brief or {}
    dossier = report.theme_dossier_brief or {}
    primary_theme = tracking.get("primary_theme") or dossier.get("primary_theme") or (report.hottest_topics[0] if report.hottest_topics else "暂无主专题")
    cover_summary = (
        tracking.get("theme_summary")
        or dossier.get("theme_summary")
        or report.headline
    )
    recent_issues = [
        {
            "href": f"./{report.date}/index.html",
            "label": report.date,
            "headline": report.headline,
        }
    ]
    return {
        "cover": {
            "primary_theme": primary_theme,
            "cover_summary": cover_summary,
            "daily_href": f"./{report.date}/index.html",
            "topic_href": f"./{report.date}/topic.html",
            "dossier_href": f"./{report.date}/dossier.html",
            "recent_issues": recent_issues,
            "editorial_line": report.headline,
            "theme_state": dossier.get("theme_state", ""),
            "participating_companies": tracking.get("participating_companies", []),
            "next_focus": tracking.get("next_day_theme_focus") or dossier.get("next_day_focus", []),
        },
        "topic_page": {
            "title": primary_theme,
            "summary": tracking.get("theme_summary") or report.headline,
        },
        "dossier_page": {
            "title": primary_theme,
            "summary": dossier.get("theme_summary") or tracking.get("theme_summary") or report.headline,
        },
    }
