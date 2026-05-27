from __future__ import annotations

import json
import re
from typing import Any

from .llm_client import LLMClient, LLMClientError
from .research_agent_input import ResearchAgentInputs
from .research_agent_skill import load_research_agent_skill, preferred_sources_for_understanding
from .research_agent_tools import list_research_agent_tools, render_research_tools_text


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


def _build_evidence_block(source: str, kind: str, block_id: str, text: str) -> dict[str, str]:
    return {
        "source": source,
        "kind": kind,
        "block_id": block_id,
        "text": text.strip(),
    }


def _iter_report_blocks(report: dict[str, Any]) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    headline = report.get("headline", "")
    if headline:
        blocks.append(_build_evidence_block("report.json", "headline", "report-headline", headline))
    for company_report in report.get("company_reports", []) or []:
        company_name = company_report.get("company_name", "")
        entries = company_report.get("entries", []) or []
        if company_name:
            blocks.append(
                _build_evidence_block(
                    "report.json",
                    "company_summary",
                    f"company-{company_name.lower()}",
                    f"{company_name} 当日动态数量 {len(entries)}。",
                )
            )
        for index, entry in enumerate(entries[:3]):
            title = ((entry.get("raw") or {}).get("title") or "").strip()
            summary = (entry.get("summary_cn") or "").strip()
            comparison = (entry.get("comparison_angle") or "").strip()
            text = " ".join(part for part in [company_name, title, summary, comparison] if part).strip()
            if text:
                blocks.append(
                    _build_evidence_block(
                        "report.json",
                        "entry",
                        f"entry-{company_name.lower()}-{index}",
                        text,
                    )
                )
    return blocks


def _iter_brief_blocks(source: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for key in [
        "editorial_signal",
        "ops_signal",
        "theme_summary",
        "theme_evolution",
        "tracking_decision",
        "theme_definition",
        "timeline_highlight",
        "operator_brief",
    ]:
        value = payload.get(key, "")
        if isinstance(value, str) and value.strip():
            blocks.append(_build_evidence_block(source, key, key.replace("_", "-"), value))
    for key in [
        "warming_themes",
        "steady_companies",
        "swing_companies",
        "persistent_source_risks",
        "recent_source_recoveries",
        "next_day_focus",
        "next_day_theme_focus",
        "watchlist",
        "participating_companies",
        "candidate_themes",
        "lead_positions",
    ]:
        value = payload.get(key, [])
        if value:
            joined = "、".join(str(item) for item in value if item)
            if joined:
                blocks.append(_build_evidence_block(source, key, key.replace("_", "-"), joined))
    company_positions = payload.get("company_positions") or {}
    if isinstance(company_positions, dict):
        for company, position in company_positions.items():
            text = f"{company}：{position}".strip()
            if position:
                blocks.append(_build_evidence_block(source, "company_position", f"company-position-{company.lower()}", text))
    timeline_events = payload.get("timeline_events") or []
    for index, event in enumerate(timeline_events[:6]):
        company = event.get("company", "")
        title = event.get("title", "")
        why = event.get("why_it_matters", "")
        date = event.get("date", "")
        text = " ".join(part for part in [date, company, title, why] if part).strip()
        if text:
            blocks.append(_build_evidence_block(source, "timeline_event", f"timeline-{index}", text))
    return blocks


def _iter_health_blocks(payload: dict[str, Any]) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    operator_brief = (payload.get("ops_status_analysis") or {}).get("operator_brief", "") or payload.get("operator_brief", "")
    if operator_brief:
        blocks.append(_build_evidence_block("health_snapshot.json", "operator_brief", "operator-brief", operator_brief))
    for key in ["recent_runtime_diagnostics", "high_priority_runtime_issues", "recently_recovered_runtime_issues"]:
        for index, item in enumerate(payload.get(key, []) or []):
            company = item.get("company_slug", "") or item.get("company", "")
            issues = "、".join(item.get("issues", []) or [])
            latest = item.get("latest_report_date", "")
            text = " ".join(part for part in [company, issues, latest] if part).strip()
            if text:
                blocks.append(_build_evidence_block("health_snapshot.json", key, f"{key}-{index}", text))
    return blocks


def _artifact_blocks(source: str, payload: Any) -> list[dict[str, str]]:
    if not payload:
        return []
    if source == "report.json" and isinstance(payload, dict):
        return _iter_report_blocks(payload)
    if source == "health_snapshot.json" and isinstance(payload, dict):
        return _iter_health_blocks(payload)
    if isinstance(payload, dict):
        return _iter_brief_blocks(source, payload)
    return [_build_evidence_block(source, "raw", "raw", _payload_text(payload))]


def _score_source(
    block: dict[str, str],
    *,
    question: str,
    question_type: str,
    question_scope: str,
    explanation_dimension: str,
    needs_general_knowledge: bool,
    entity: str,
    primary_theme: str,
    preferred_sources: list[str],
) -> int:
    payload_text = block.get("text", "").lower()
    if not payload_text:
        return 0
    score = 0
    source = block["source"]
    if question_scope != "general" and source in preferred_sources:
        score += max(1, len(preferred_sources) - preferred_sources.index(source))
    lowered_question = question.lower()
    if entity and entity.lower() in lowered_question and entity.lower() in payload_text:
        score += 5
    if primary_theme and primary_theme.lower() in lowered_question and primary_theme.lower() in payload_text:
        score += 4
    for token in _tokenize(question):
        if token in payload_text:
            score += 2
    if question_scope == "theme" and source == "theme_dossier.json":
        score += 4
    if question_scope == "theme" and explanation_dimension == "evolution" and block.get("kind") == "timeline_event":
        score += 6
    if question_scope == "company" and block.get("kind") == "company_position":
        score += 6
    if block.get("kind") == "tool_result":
        score += 7
    if question_scope == "theme" and explanation_dimension == "judgment" and block.get("kind") in {"theme_state", "theme_summary", "tracking_decision"}:
        score += 4
    if question_scope == "ops" and source == "health_snapshot.json":
        score += 4
    if question_scope == "report" and source in {"daily_intel_brief.json", "report.json"}:
        score += 3
    if needs_general_knowledge and question_scope == "general" and source == "theme_dossier.json":
        score += 1
    return score


def _determine_grounding_mode(
    *,
    question_scope: str,
    needs_general_knowledge: bool,
    matched_sources: list[str],
    entity: str,
    primary_theme: str,
) -> str:
    if question_scope == "ops":
        return "grounded" if "health_snapshot.json" in matched_sources else "hybrid"
    if question_scope == "theme":
        return "grounded" if "theme_dossier.json" in matched_sources else "hybrid"
    if question_scope in {"company", "report"}:
        return "grounded" if matched_sources else "hybrid"
    if needs_general_knowledge:
        return "hybrid" if matched_sources else "general"
    if entity or primary_theme:
        return "hybrid" if matched_sources else "general"
    return "general"


def _llm_select_blocks(
    *,
    client: LLMClient | None,
    question: str,
    question_scope: str,
    explanation_dimension: str,
    needs_general_knowledge: bool,
    primary_theme: str,
    entity: str,
    candidate_blocks: list[dict[str, str]],
) -> list[str]:
    if client is None or not client.is_available() or not candidate_blocks:
        return []
    try:
        payload = client.generate_json(
            instructions=(
                "你负责为科技日报研究助理挑选最相关的 RAG 证据块。"
                "请从候选块里选择最少但足够回答问题的 block_id。"
                "优先选择高信息密度、和问题最直接相关的块；一般不超过 4 个。"
            ),
            input_text=(
                f"用户问题：{question}\n"
                f"问题范围：{question_scope}\n"
                f"解释维度：{explanation_dimension}\n"
                f"是否需要通用知识补充：{needs_general_knowledge}\n"
                f"当前主专题：{primary_theme}\n"
                f"目标公司：{entity}\n"
                "候选证据块：\n"
                + "\n".join(
                    f"- {block['block_id']} | {block['source']} | {block['kind']} | {block['text']}"
                    for block in candidate_blocks
                )
            ),
            schema_name="rag_block_selection",
            schema={
                "type": "object",
                "properties": {
                    "selected_block_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["selected_block_ids"],
                "additionalProperties": False,
            },
        )
    except (LLMClientError, KeyError, TypeError, ValueError):
        return []
    selected_ids = [str(item).strip() for item in payload.get("selected_block_ids", []) if str(item).strip()]
    allowed = {block["block_id"] for block in candidate_blocks}
    return [block_id for block_id in selected_ids if block_id in allowed]


def _legacy_scope_defaults(question_type: str) -> tuple[str, str, bool]:
    if question_type in {"dossier_summary", "theme_state", "theme_focus"}:
        return "theme", "judgment", False
    if question_type == "timeline_focus":
        return "theme", "evolution", False
    if question_type in {"company_position", "company_focus"}:
        return "company", "comparison", False
    if question_type == "ops_status":
        return "ops", "evidence", False
    if question_type == "daily_summary":
        return "report", "judgment", False
    if question_type in {"general_explainer", "out_of_scope"}:
        return "general", "explanation", True
    return "report", "judgment", False


def build_research_context(
    question: str,
    question_type: str,
    entity: str,
    inputs: ResearchAgentInputs,
    *,
    explanation_dimension: str = "judgment",
    question_scope: str = "report",
    needs_general_knowledge: bool = False,
    tool_result: dict | None = None,
    selector_client: LLMClient | None = None,
) -> dict:
    if (question_scope, explanation_dimension, needs_general_knowledge) == ("report", "judgment", False):
        question_scope, explanation_dimension, needs_general_knowledge = _legacy_scope_defaults(question_type)

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
    available_tools = list_research_agent_tools()
    primary_theme = dossier.get("primary_theme") or tracking.get("primary_theme", "")
    preferred_sources = preferred_sources_for_understanding(
        question_scope=question_scope,
        explanation_dimension=explanation_dimension,
        needs_general_knowledge=needs_general_knowledge,
        requested_tool=(tool_result or {}).get("tool_name", ""),
    )
    artifact_map = {
        "report.json": report,
        "daily_intel_brief.json": daily,
        "cross_day_intel_brief.json": cross_day,
        "theme_tracking_brief.json": tracking,
        "theme_dossier.json": dossier,
        "health_snapshot.json": health,
    }
    all_blocks = [
        block
        for source, payload in artifact_map.items()
        for block in _artifact_blocks(source, payload)
        if block.get("text")
    ]
    if tool_result:
        tool_summary = (tool_result.get("summary") or "").strip()
        if tool_summary:
            all_blocks.append(
                _build_evidence_block(
                    f"{tool_result.get('tool_name', 'tool')}.tool",
                    "tool_result",
                    f"tool-{tool_result.get('tool_name', 'tool')}",
                    tool_summary,
                )
            )
    scored_blocks = [
        (
            block,
            _score_source(
                block,
                question=question,
                question_type=question_type,
                question_scope=question_scope,
                explanation_dimension=explanation_dimension,
                needs_general_knowledge=needs_general_knowledge,
                entity=entity,
                primary_theme=primary_theme,
                preferred_sources=preferred_sources,
            ),
        )
        for block in all_blocks
    ]
    matched_sources = list(dict.fromkeys(block["source"] for block, score in scored_blocks if score > 0))
    ranked_blocks = [block for block, score in sorted(scored_blocks, key=lambda item: item[1], reverse=True) if score > 0]
    candidate_blocks = ranked_blocks[:12]
    selected_blocks: list[dict[str, str]] = []
    selected_sources: list[str] = []
    selected_block_ids = _llm_select_blocks(
        client=selector_client,
        question=question,
        question_scope=question_scope,
        explanation_dimension=explanation_dimension,
        needs_general_knowledge=needs_general_knowledge,
        primary_theme=primary_theme,
        entity=entity,
        candidate_blocks=candidate_blocks,
    )
    if selected_block_ids:
        selected_lookup = {block["block_id"]: block for block in candidate_blocks}
        for block_id in selected_block_ids[:6]:
            block = selected_lookup.get(block_id)
            if not block:
                continue
            selected_blocks.append(block)
            if block["source"] not in selected_sources:
                selected_sources.append(block["source"])
    else:
        per_source_counts: dict[str, int] = {}
        for block in ranked_blocks:
            source = block["source"]
            if per_source_counts.get(source, 0) >= 2:
                continue
            if len(selected_blocks) >= 6:
                break
            selected_blocks.append(block)
            per_source_counts[source] = per_source_counts.get(source, 0) + 1
            if source not in selected_sources:
                selected_sources.append(source)
            if len(selected_sources) >= 4 and len(selected_blocks) >= 4:
                break
    selected_context: dict[str, list[dict[str, str]]] = {}
    for block in selected_blocks:
        selected_context.setdefault(block["source"], []).append(block)
    grounding_mode = _determine_grounding_mode(
        question_scope=question_scope,
        needs_general_knowledge=needs_general_knowledge,
        matched_sources=matched_sources,
        entity=entity,
        primary_theme=primary_theme,
    )
    if not selected_sources and grounding_mode != "general":
        for source in [source for source in preferred_sources if artifact_map.get(source)][:3]:
            source_blocks = _artifact_blocks(source, artifact_map[source])[:2]
            if not source_blocks:
                continue
            selected_sources.append(source)
            selected_context[source] = source_blocks
            selected_blocks.extend(source_blocks)

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
        "rag_and_boundaries_text": skill.get("rag_and_boundaries_text", ""),
        "available_tools": available_tools,
        "available_tools_text": render_research_tools_text(),
        "tool_result": tool_result or {},
        "preferred_sources": preferred_sources,
        "selected_sources": selected_sources,
        "selected_blocks": selected_blocks,
        "matched_sources": matched_sources,
        "selected_context": selected_context,
        "grounding_mode": grounding_mode,
        "question_scope": question_scope,
        "explanation_dimension": explanation_dimension,
        "needs_general_knowledge": needs_general_knowledge,
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
