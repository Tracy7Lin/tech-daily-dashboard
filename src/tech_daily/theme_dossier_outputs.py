from __future__ import annotations

import json
from pathlib import Path

from .models import ThemeDossierBrief


def render_theme_dossier_markdown(brief: ThemeDossierBrief) -> str:
    companies = "\n".join(
        f"- {company}: {brief.company_positions.get(company, '持续参与该主题')}"
        for company in brief.participating_companies
    ) or "- 暂无"
    timeline = "\n".join(
        f"- **{event.date} | {event.company} | {event.title}**\n  - 为什么重要：{event.why_it_matters}"
        for event in brief.timeline_events
    ) or "- 暂无"
    focus = "\n".join(f"- {item}" for item in brief.next_day_focus) or "- 暂无"
    return (
        f"# {brief.date_range[0]} 至 {brief.date_range[1]} 主题档案\n\n"
        f"## 核心结论\n当前主专题是 **{brief.primary_theme or '暂无'}**，目前处于 **{brief.theme_state or '暂无'}** 阶段。"
        f"{brief.theme_summary or '暂无'}\n\n"
        f"## 主题定义\n{brief.theme_definition or '暂无'}\n\n"
        f"## 公司位置观察\n{companies}\n\n"
        f"## 关键时间线\n{timeline}\n\n"
        f"## 跟踪决策\n{brief.tracking_decision or '暂无'}\n\n"
        f"## 下一步研究提示\n{focus}\n"
    )


def build_theme_dossier_page_block(brief: ThemeDossierBrief) -> dict:
    lead_positions = [
        f"{company}：{brief.company_positions.get(company, '持续参与该主题')}"
        for company in brief.participating_companies[:3]
    ]
    timeline_highlight = ""
    if brief.timeline_events:
        lead_event = brief.timeline_events[-1]
        timeline_highlight = f"{lead_event.date} · {lead_event.company} · {lead_event.title}"
    return {
        "primary_theme": brief.primary_theme,
        "theme_state": brief.theme_state,
        "theme_definition": brief.theme_definition,
        "theme_summary": brief.theme_summary,
        "tracking_decision": brief.tracking_decision,
        "lead_positions": lead_positions,
        "timeline_highlight": timeline_highlight,
        "next_day_focus": brief.next_day_focus,
    }


def write_theme_dossier_outputs(brief: ThemeDossierBrief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "theme_dossier.json"
    markdown_path = output_dir / "theme-dossier.md"
    json_path.write_text(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_theme_dossier_markdown(brief), encoding="utf-8")
    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "page_block": build_theme_dossier_page_block(brief),
    }
