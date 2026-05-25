from __future__ import annotations

import json
import re
from typing import Any

from .research_agent_input import ResearchAgentInputs
from .research_agent_skill import load_research_agent_skill, preferred_sources_for_question


def _tokenize(text: str) -> list[str]:
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", (text or "").lower())
    return [token for token in normalized.split() if len(token) > 1]


def _payload_text(payload: Any) -> str:
    if not payload:
        return ""
    try:
        serialized = json.dumps(payload, ensure_ascii=False)
    except TypeError:
        serialized = str(payload)
    return serialized.lower()


def _score_source(
    source: str,
    payload: Any,
    *,
    question: str,
    question_type: str,
    entity: str,
    primary_theme: str,
    preferred_sources: list[str],
) -> int:
    if not payload:
        return 0
    score = 0
    payload_text = _payload_text(payload)
    if question_type != "out_of_scope" and source in preferred_sources:
        score += max(1, len(preferred_sources) - preferred_sources.index(source))
    lowered_question = question.lower()
    if entity and entity.lower() in lowered_question and entity.lower() in payload_text:
        score += 5
    if primary_theme and primary_theme.lower() in lowered_question and primary_theme.lower() in payload_text:
        score += 4
    for token in _tokenize(question):
        if token in payload_text:
            score += 2
    if question_type in {"dossier_summary", "theme_state", "company_position", "timeline_focus"} and source == "theme_dossier.json":
        score += 4
    if question_type == "ops_status" and source == "health_snapshot.json":
        score += 4
    if question_type == "daily_summary" and source in {"daily_intel_brief.json", "report.json"}:
        score += 3
    return score


def _determine_grounding_mode(question_type: str, matched_sources: list[str], entity: str, primary_theme: str) -> str:
    if question_type == "ops_status":
        return "grounded" if "health_snapshot.json" in matched_sources else "hybrid"
    if question_type in {"dossier_summary", "theme_state", "company_position", "timeline_focus"}:
        return "grounded" if "theme_dossier.json" in matched_sources else "hybrid"
    if question_type in {"company_focus", "theme_focus", "daily_summary"}:
        return "grounded" if matched_sources else "hybrid"
    if question_type == "out_of_scope":
        if matched_sources:
            return "hybrid"
        return "general"
    if entity or primary_theme:
        return "hybrid" if matched_sources else "general"
    return "general"


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
    primary_theme = dossier.get("primary_theme") or tracking.get("primary_theme", "")
    artifact_map = {
        "report.json": report,
        "daily_intel_brief.json": daily,
        "cross_day_intel_brief.json": cross_day,
        "theme_tracking_brief.json": tracking,
        "theme_dossier.json": dossier,
        "health_snapshot.json": health,
    }
    preferred_sources = preferred_sources_for_question(question_type)
    scored_sources = [
        (
            source,
            _score_source(
                source,
                payload,
                question=question,
                question_type=question_type,
                entity=entity,
                primary_theme=primary_theme,
                preferred_sources=preferred_sources,
            ),
        )
        for source, payload in artifact_map.items()
        if payload
    ]
    matched_sources = [source for source, score in scored_sources if score > 0]
    sorted_sources = [source for source, _ in sorted(scored_sources, key=lambda item: item[1], reverse=True)]
    selected_sources = sorted_sources[:4] if matched_sources else []
    selected_context = {source: artifact_map[source] for source in selected_sources}
    grounding_mode = _determine_grounding_mode(question_type, matched_sources, entity, primary_theme)
    if not selected_sources and grounding_mode != "general":
        selected_sources = [source for source in preferred_sources if artifact_map.get(source)][:3]
        selected_context = {source: artifact_map[source] for source in selected_sources}

    primary_source = selected_sources[0] if selected_sources else ""

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
        "matched_sources": matched_sources,
        "selected_context": selected_context,
        "grounding_mode": grounding_mode,
        "report": report,
        "daily_intel_brief": daily,
        "cross_day_intel_brief": cross_day,
        "theme_tracking_brief": tracking,
        "theme_dossier": dossier,
        "health_snapshot": health,
        "report_headline": report.get("headline", ""),
        "editorial_signal": daily.get("editorial_signal", ""),
        "primary_theme": primary_theme,
        "theme_state": dossier.get("theme_state", ""),
        "tracking_decision": dossier.get("tracking_decision", ""),
        "company_positions": dossier.get("company_positions", {}),
        "timeline_events": dossier.get("timeline_events", []),
        "warming_themes": cross_day.get("warming_themes", []),
        "operator_brief": (health.get("ops_status_analysis") or {}).get("operator_brief", "") or health.get("operator_brief", ""),
        "companies": companies,
    }
