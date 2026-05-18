from __future__ import annotations

from .research_agent_input import ResearchAgentInputs


def build_research_context(question: str, question_type: str, entity: str, inputs: ResearchAgentInputs) -> dict:
    report = inputs.report or {}
    daily = inputs.daily_intel_brief or {}
    cross_day = inputs.cross_day_intel_brief or {}
    tracking = inputs.theme_tracking_brief or {}
    dossier = inputs.theme_dossier or {}
    health = inputs.health_snapshot or {}
    companies = [
        report_item.get("company_name", "")
        for report_item in report.get("company_reports", [])
        if report_item.get("company_name")
    ]
    if not companies:
        companies = list((dossier.get("company_positions") or {}).keys())

    primary_source = "report.json"
    if question_type in {"dossier_summary", "theme_state", "company_position", "timeline_focus"} and dossier:
        primary_source = "theme_dossier.json"
    elif question_type == "ops_status" and health:
        primary_source = "health_snapshot.json"
    elif question_type in {"theme_focus", "daily_summary"} and tracking:
        primary_source = "theme_tracking_brief.json"

    return {
        "question": question,
        "question_type": question_type,
        "entity": entity,
        "primary_source": primary_source,
        "report_date": inputs.report_date,
        "report": report,
        "daily_intel_brief": daily,
        "cross_day_intel_brief": cross_day,
        "theme_tracking_brief": tracking,
        "theme_dossier": dossier,
        "health_snapshot": health,
        "report_headline": report.get("headline", ""),
        "editorial_signal": daily.get("editorial_signal", ""),
        "primary_theme": dossier.get("primary_theme") or tracking.get("primary_theme", ""),
        "theme_state": dossier.get("theme_state", ""),
        "tracking_decision": dossier.get("tracking_decision", ""),
        "company_positions": dossier.get("company_positions", {}),
        "timeline_events": dossier.get("timeline_events", []),
        "warming_themes": cross_day.get("warming_themes", []),
        "operator_brief": (health.get("ops_status_analysis") or {}).get("operator_brief", "") or health.get("operator_brief", ""),
        "companies": companies,
    }
