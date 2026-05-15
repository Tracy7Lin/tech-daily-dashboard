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
        f"- {event.date} | {event.company} | {event.title}：{event.why_it_matters}"
        for event in brief.timeline_events
    ) or "- 暂无"
    focus = "\n".join(f"- {item}" for item in brief.next_day_focus) or "- 暂无"
    return (
        f"# {brief.date_range[0]} 至 {brief.date_range[1]} 主题档案\n\n"
        f"## 主专题\n{brief.primary_theme or '暂无'}\n\n"
        f"## 主题定义\n{brief.theme_definition or '暂无'}\n\n"
        f"## 当前阶段\n{brief.theme_state or '暂无'}\n\n"
        f"## 为什么值得看\n{brief.theme_summary or '暂无'}\n\n"
        f"## 参与公司与切入点\n{companies}\n\n"
        f"## 关键时间线\n{timeline}\n\n"
        f"## 是否继续跟踪\n{brief.tracking_decision or '暂无'}\n\n"
        f"## 明日关注点\n{focus}\n"
    )


def build_theme_dossier_page_block(brief: ThemeDossierBrief) -> dict:
    return {
        "primary_theme": brief.primary_theme,
        "theme_state": brief.theme_state,
        "theme_summary": brief.theme_summary,
        "tracking_decision": brief.tracking_decision,
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
