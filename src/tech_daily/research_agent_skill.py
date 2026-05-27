from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_research_agent_skill() -> dict[str, str]:
    skill_dir = _repo_root() / "agent_skills" / "research-agent-question-orchestration"
    skill_path = skill_dir / "SKILL.md"
    knowledge_path = skill_dir / "references" / "knowledge-sources.md"
    patterns_path = skill_dir / "references" / "question-patterns.md"
    rag_path = skill_dir / "subflows" / "rag-and-boundaries.md"
    return {
        "skill_path": str(skill_path),
        "skill_text": skill_path.read_text(encoding="utf-8") if skill_path.exists() else "",
        "knowledge_sources_text": knowledge_path.read_text(encoding="utf-8") if knowledge_path.exists() else "",
        "question_patterns_text": patterns_path.read_text(encoding="utf-8") if patterns_path.exists() else "",
        "rag_and_boundaries_text": rag_path.read_text(encoding="utf-8") if rag_path.exists() else "",
    }


def preferred_sources_for_understanding(
    *,
    question_scope: str,
    explanation_dimension: str,
    needs_general_knowledge: bool = False,
    requested_tool: str = "",
) -> list[str]:
    if requested_tool == "local_health_check":
        return [
            "health_snapshot.json",
            "report.json",
        ]
    if requested_tool == "report_generation":
        return [
            "daily_intel_brief.json",
            "report.json",
            "theme_tracking_brief.json",
        ]
    if needs_general_knowledge and question_scope == "general":
        return []
    if question_scope == "theme":
        if explanation_dimension == "evolution":
            return [
                "theme_dossier.json",
                "cross_day_intel_brief.json",
                "theme_tracking_brief.json",
                "daily_intel_brief.json",
                "report.json",
            ]
        return [
            "theme_dossier.json",
            "theme_tracking_brief.json",
            "cross_day_intel_brief.json",
            "daily_intel_brief.json",
            "report.json",
        ]
    if question_scope == "company":
        return [
            "theme_dossier.json",
            "theme_tracking_brief.json",
            "report.json",
            "cross_day_intel_brief.json",
            "daily_intel_brief.json",
        ]
    if question_scope == "ops":
        return [
            "health_snapshot.json",
            "report.json",
        ]
    if question_scope == "report":
        return [
            "daily_intel_brief.json",
            "report.json",
            "theme_tracking_brief.json",
        ]
    return [
        "theme_dossier.json",
        "theme_tracking_brief.json",
        "cross_day_intel_brief.json",
        "daily_intel_brief.json",
        "report.json",
    ]


def preferred_sources_for_question(question_type: str) -> list[str]:
    if question_type == "general_explainer":
        return preferred_sources_for_understanding(
            question_scope="general",
            explanation_dimension="explanation",
            needs_general_knowledge=True,
        )
    if question_type in {"dossier_summary", "theme_state", "theme_focus"}:
        return preferred_sources_for_understanding(
            question_scope="theme",
            explanation_dimension="judgment",
        )
    if question_type == "timeline_focus":
        return preferred_sources_for_understanding(
            question_scope="theme",
            explanation_dimension="evolution",
        )
    if question_type in {"company_position", "company_focus"}:
        return preferred_sources_for_understanding(
            question_scope="company",
            explanation_dimension="comparison",
        )
    if question_type == "ops_status":
        return preferred_sources_for_understanding(
            question_scope="ops",
            explanation_dimension="evidence",
        )
    if question_type == "daily_summary":
        return preferred_sources_for_understanding(
            question_scope="report",
            explanation_dimension="judgment",
        )
    return preferred_sources_for_understanding(
        question_scope="report",
        explanation_dimension="judgment",
    )
