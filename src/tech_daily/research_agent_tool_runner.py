from __future__ import annotations

from pathlib import Path

from .automation import generate_today_report, resolve_report_date
from .healthcheck import run_health_check
from .pipeline import generate_daily_report
from .settings import DEFAULT_SETTINGS


def run_research_agent_tool(
    tool_name: str,
    *,
    report_date: str,
    site_dir: Path,
    data_dir: Path,
) -> dict:
    if tool_name == "local_health_check":
        result = run_health_check()
        return {
            "tool_name": tool_name,
            "status": "ok",
            "summary": result.get("ops_status_analysis", {}).get("operator_brief", "") or "健康检查已完成。",
            "payload": {
                "latest_report_date": result.get("latest_report_date", ""),
                "high_priority_runtime_issues": result.get("high_priority_runtime_issues", []),
                "recently_recovered_runtime_issues": result.get("recently_recovered_runtime_issues", []),
                "notes": result.get("notes", []),
            },
        }
    if tool_name == "report_generation":
        target_output = site_dir or Path(DEFAULT_SETTINGS.site_output_dir)
        if report_date == resolve_report_date():
            report = generate_today_report(output_dir=target_output)
        else:
            report = generate_daily_report(report_date, output_dir=target_output)
        return {
            "tool_name": tool_name,
            "status": "ok",
            "summary": f"日报已重新生成：{report.date}，共保留 {report.total_entries} 条有效动态。",
            "payload": {
                "report_date": report.date,
                "headline": report.headline,
                "total_entries": report.total_entries,
                "companies_covered": report.companies_covered,
                "active_companies": report.active_companies,
            },
        }
    return {
        "tool_name": tool_name,
        "status": "unsupported",
        "summary": f"当前研究助理还不能执行工具：{tool_name}",
        "payload": {},
    }
