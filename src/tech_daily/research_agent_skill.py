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


def preferred_sources_for_question(question_type: str) -> list[str]:
    if question_type == "general_explainer":
        return []
    if question_type in {"dossier_summary", "theme_state", "company_position", "timeline_focus"}:
        return [
            "theme_dossier.json",
            "theme_tracking_brief.json",
            "cross_day_intel_brief.json",
            "daily_intel_brief.json",
            "report.json",
        ]
    if question_type in {"theme_focus", "comparison", "next_step"}:
        return [
            "theme_tracking_brief.json",
            "cross_day_intel_brief.json",
            "theme_dossier.json",
            "daily_intel_brief.json",
            "report.json",
        ]
    if question_type == "ops_status":
        return [
            "health_snapshot.json",
            "report.json",
        ]
    if question_type == "daily_summary":
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
