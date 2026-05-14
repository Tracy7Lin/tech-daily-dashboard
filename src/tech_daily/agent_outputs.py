from __future__ import annotations

import json
from pathlib import Path

from .models import DailyIntelBrief


def render_agent_markdown(brief: DailyIntelBrief) -> str:
    tomorrow_focus = "\n".join(f"- {item}" for item in brief.tomorrow_focus) or "- 暂无"
    return (
        f"# {brief.report_date} 情报判断\n\n"
        f"## 今日核心判断\n{brief.editorial_signal}\n\n"
        f"## 运维状态\n{brief.ops_signal}\n\n"
        f"## 明日关注点\n{tomorrow_focus}\n"
    )


def write_agent_outputs(brief: DailyIntelBrief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "daily_intel_brief.json"
    markdown_path = output_dir / "agent-brief.md"
    json_path.write_text(
        json.dumps(brief.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(render_agent_markdown(brief), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": markdown_path}
