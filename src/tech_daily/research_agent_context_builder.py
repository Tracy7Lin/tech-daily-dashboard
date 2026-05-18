from __future__ import annotations

from .research_agent_input import ResearchAgentInputs
from .research_agent_skill import load_research_agent_skill, preferred_sources_for_question


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

    skill = load_research_agent_skill()
    artifact_map = {
        "report.json": report,
        "daily_intel_brief.json": daily,
        "cross_day_intel_brief.json": cross_day,
        "theme_tracking_brief.json": tracking,
        "theme_dossier.json": dossier,
        "health_snapshot.json": health,
    }
    preferred_sources = preferred_sources_for_question(question_type)
    selected_sources = [source for source in preferred_sources if artifact_map.get(source)]
    if not selected_sources:
        selected_sources = [source for source, payload in artifact_map.items() if payload][:3]
    primary_source = selected_sources[0] if selected_sources else "report.json"
    selected_context = {
        source: artifact_map[source]
        for source in selected_sources[:4]
    }

    return {
        "question": question,
        "question_type": question_type,
        "entity": entity,
        "primary_source": primary_source,
        "report_date": inputs.report_date,
        "research_skill_path": skill["skill_path"],
        "research_skill_text": skill["skill_text"],
        "knowledge_sources_text": skill["knowledge_sources_text"],
        "question_patterns_text": skill["question_patterns_text"],
        "preferred_sources": preferred_sources,
        "selected_sources": selected_sources,
        "selected_context": selected_context,
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
