from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ResearchToolDescriptor:
    name: str
    purpose: str
    availability: str
    kind: str = "local"


def list_research_agent_tools() -> list[ResearchToolDescriptor]:
    return [
        ResearchToolDescriptor(
            name="daily_report_artifacts",
            purpose="读取当前日报、跨日观察、专题跟踪、主题档案与运行状态 JSON 产物。",
            availability="available",
        ),
        ResearchToolDescriptor(
            name="local_health_check",
            purpose="读取并解释当前 health snapshot 与运行状态诊断。",
            availability="available",
        ),
        ResearchToolDescriptor(
            name="report_generation",
            purpose="触发日报生成与更新本地产物。",
            availability="future",
        ),
        ResearchToolDescriptor(
            name="web_search",
            purpose="联网搜索外部信息，补充日报知识层之外的证据。",
            availability="future",
            kind="remote",
        ),
    ]


def render_research_tools_text() -> str:
    lines: list[str] = []
    for tool in list_research_agent_tools():
        payload = asdict(tool)
        lines.append(
            f"- {payload['name']} ({payload['kind']}, {payload['availability']}): {payload['purpose']}"
        )
    return "\n".join(lines)
