from __future__ import annotations

import json
from pathlib import Path

from .models import CrossDayIntelBrief


def render_cross_day_markdown(brief: CrossDayIntelBrief) -> str:
    warming = "\n".join(f"- {item}" for item in brief.warming_themes) or "- 暂无明显升温主题"
    next_focus = "\n".join(f"- {item}" for item in brief.next_day_focus) or "- 暂无额外观察项"
    return (
        f"# {brief.date_range[0]} 至 {brief.date_range[1]} 跨日观察\n\n"
        f"## 最近几天主线\n{warming}\n\n"
        f"## 明日观察清单\n{next_focus}\n"
    )


def build_cross_day_page_block(brief: CrossDayIntelBrief) -> dict:
    return {
        "title": "跨日观察",
        "date_range": list(brief.date_range),
        "warming_themes": brief.warming_themes,
        "steady_companies": brief.steady_companies,
        "persistent_source_risks": brief.persistent_source_risks,
        "recent_source_recoveries": brief.recent_source_recoveries,
        "next_day_focus": brief.next_day_focus,
    }


def write_cross_day_outputs(brief: CrossDayIntelBrief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cross_day_intel_brief.json"
    markdown_path = output_dir / "cross-day-brief.md"
    json_path.write_text(
        json.dumps(brief.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_cross_day_markdown(brief), encoding="utf-8")
    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
        "page_block": build_cross_day_page_block(brief),
    }
