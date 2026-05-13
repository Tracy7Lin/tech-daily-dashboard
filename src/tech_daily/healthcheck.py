from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .config_loader import load_companies
from .config_validation import build_source_diagnostics, validate_companies
from .llm_runtime import build_llm_client
from .settings import DEFAULT_SETTINGS, Settings


def _build_runtime_diagnostic(status: dict) -> dict:
    issues: list[str] = []
    severity = "ok"
    suggestion = ""
    message = status.get("message", "")
    fetched_count = status.get("fetched_count", 0)
    kept_count = status.get("kept_count", 0)

    if "http_error:403" in message:
        issues.append("http_403_blocked")
        severity = "error"
        suggestion = "this source may block generic requests; consider fetcher-specific headers or an alternate official source"
    elif "http_error:500" in message:
        issues.append("http_500_source_error")
        severity = "error"
        suggestion = "the official endpoint may be unstable; verify the URL or switch to a more stable official page"
    elif fetched_count == 0:
        issues.append("zero_fetched_entries")
        severity = "warning"
        suggestion = "review source url, path prefixes, and article link extraction rules"
    elif kept_count == 0:
        issues.append("zero_kept_entries")
        severity = "warning"
        suggestion = "review include/exclude patterns because fetched entries are being filtered out"

    return {
        "company_slug": status.get("company_slug", ""),
        "company_name": status.get("company_name", ""),
        "source_label": status.get("source_label", ""),
        "severity": severity,
        "issues": issues,
        "suggestion": suggestion,
        "message": message,
    }


def _load_latest_runtime_diagnostics(output_dir: Path) -> tuple[str, list[dict]]:
    report_paths = sorted(output_dir.glob("*/report.json"))
    if not report_paths:
        return "", []

    latest_path = max(report_paths, key=lambda path: path.parent.name)
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    diagnostics = [_build_runtime_diagnostic(status) for status in payload.get("source_statuses", [])]
    diagnostics = [item for item in diagnostics if item["severity"] != "ok"]
    return payload.get("date", latest_path.parent.name), diagnostics


def _load_runtime_history_summary(output_dir: Path, *, limit: int = 7) -> list[dict]:
    report_paths = sorted(output_dir.glob("*/report.json"), reverse=True)
    if not report_paths:
        return []

    grouped: dict[str, dict] = {}
    for report_path in report_paths[:limit]:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        report_date = payload.get("date", report_path.parent.name)
        for status in payload.get("source_statuses", []):
            diagnostic = _build_runtime_diagnostic(status)
            if diagnostic["severity"] == "ok":
                continue
            key = diagnostic["company_slug"]
            current = grouped.setdefault(
                key,
                {
                    "company_slug": diagnostic["company_slug"],
                    "company_name": diagnostic["company_name"],
                    "source_label": diagnostic["source_label"],
                    "severity": diagnostic["severity"],
                    "occurrence_count": 0,
                    "latest_report_date": report_date,
                    "issues": Counter(),
                    "suggestion": diagnostic.get("suggestion", ""),
                },
            )
            current["occurrence_count"] += 1
            current["issues"].update(diagnostic["issues"])
            if diagnostic["severity"] == "error":
                current["severity"] = "error"
            if report_date >= current["latest_report_date"]:
                current["latest_report_date"] = report_date
                current["source_label"] = diagnostic["source_label"]
                current["suggestion"] = diagnostic.get("suggestion", "") or current["suggestion"]

    summaries = []
    for item in grouped.values():
        summaries.append(
            {
                "company_slug": item["company_slug"],
                "company_name": item["company_name"],
                "source_label": item["source_label"],
                "severity": item["severity"],
                "occurrence_count": item["occurrence_count"],
                "latest_report_date": item["latest_report_date"],
                "issues": [issue for issue, _ in item["issues"].most_common()],
                "suggestion": item["suggestion"],
            }
        )
    return sorted(
        summaries,
        key=lambda item: (
            item["severity"] != "error",
            -item["occurrence_count"],
            item["company_slug"],
        ),
    )


def _build_high_priority_runtime_issues(runtime_history_summary: list[dict]) -> list[dict]:
    items = []
    for summary in runtime_history_summary:
        if summary["severity"] == "error" and summary["occurrence_count"] >= 2:
            items.append(summary)
            continue
        if "zero_fetched_entries" in summary["issues"] and summary["occurrence_count"] >= 2:
            items.append(summary)
    return sorted(
        items,
        key=lambda item: (
            item["severity"] != "error",
            -item["occurrence_count"],
            item["company_slug"],
        ),
    )


def run_health_check(settings: Settings | None = None) -> dict:
    current_settings = settings or DEFAULT_SETTINGS
    companies = load_companies()
    source_count = sum(len(company.sources) for company in companies)
    validation_issues = validate_companies(companies)
    source_diagnostics = build_source_diagnostics(companies)

    output_dir = Path(current_settings.site_output_dir)
    data_dir = Path(current_settings.data_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    latest_report_date, recent_runtime_diagnostics = _load_latest_runtime_diagnostics(output_dir)
    runtime_history_summary = _load_runtime_history_summary(output_dir)
    high_priority_runtime_issues = _build_high_priority_runtime_issues(runtime_history_summary)

    llm_available = build_llm_client(current_settings).is_available()
    notes: list[str] = []

    if (current_settings.summary_mode in {"llm", "hybrid"} or current_settings.editorial_mode in {"llm", "hybrid"}) and not llm_available:
        notes.append("hybrid mode will fall back to rule output until LLM credentials are complete")

    ok = bool(
        companies
        and source_count
        and output_dir.exists()
        and data_dir.exists()
        and not notes
        and not validation_issues
    )

    return {
        "ok": ok,
        "company_count": len(companies),
        "source_count": source_count,
        "summary_mode": current_settings.summary_mode,
        "editorial_mode": current_settings.editorial_mode,
        "llm_available": llm_available,
        "output_dir": str(output_dir),
        "data_dir": str(data_dir),
        "output_dir_ready": output_dir.exists(),
        "data_dir_ready": data_dir.exists(),
        "latest_report_date": latest_report_date,
        "recent_runtime_diagnostics": recent_runtime_diagnostics,
        "runtime_history_summary": runtime_history_summary,
        "high_priority_runtime_issues": high_priority_runtime_issues,
        "validation_issue_count": len(validation_issues),
        "validation_issues": validation_issues,
        "source_diagnostics": source_diagnostics,
        "notes": notes,
    }
