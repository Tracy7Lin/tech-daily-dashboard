from __future__ import annotations

import json
from pathlib import Path

from .models import ThemeTrackingBrief


def render_theme_tracking_markdown(brief: ThemeTrackingBrief) -> str:
    companies = "\n".join(f"- {company}" for company in brief.participating_companies) or "- 暂无"
    focus = "\n".join(f"- {item}" for item in brief.next_day_theme_focus) or "- 暂无"
    return (
        f"# {brief.date_range[0]} 至 {brief.date_range[1]} 专题跟踪\n\n"
        f"## 主专题\n{brief.primary_theme or '暂无'}\n\n"
        f"## 为什么今天值得继续看\n{brief.theme_summary or '暂无'}\n\n"
        f"## 参与公司\n{companies}\n\n"
        f"## 明日关注点\n{focus}\n"
    )


def build_theme_tracking_page_block(brief: ThemeTrackingBrief) -> dict:
    return {
        "candidate_themes": brief.candidate_themes,
        "primary_theme": brief.primary_theme,
        "theme_summary": brief.theme_summary,
        "participating_companies": brief.participating_companies,
        "company_angles": brief.company_angles,
        "theme_evolution": brief.theme_evolution,
        "continue_tracking": brief.continue_tracking,
        "next_day_theme_focus": brief.next_day_theme_focus,
    }


def write_theme_tracking_outputs(brief: ThemeTrackingBrief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "theme_tracking_brief.json"
    markdown_path = output_dir / "theme-tracking-brief.md"
    json_path.write_text(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_theme_tracking_markdown(brief), encoding="utf-8")
    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "page_block": build_theme_tracking_page_block(brief),
    }
