from __future__ import annotations

from .config_loader import load_companies
from .config_validation import build_source_diagnostics, validate_companies
from .settings import DEFAULT_SETTINGS, Settings


def run_dry_run(report_date: str, settings: Settings | None = None) -> dict:
    current_settings = settings or DEFAULT_SETTINGS
    companies = load_companies()
    validation_issues = validate_companies(companies)
    source_diagnostics = build_source_diagnostics(companies)

    return {
        "ok": not any(issue["severity"] == "error" for issue in validation_issues),
        "report_date": report_date,
        "company_count": len(companies),
        "source_count": sum(len(company.sources) for company in companies),
        "summary_mode": current_settings.summary_mode,
        "editorial_mode": current_settings.editorial_mode,
        "validation_issue_count": len(validation_issues),
        "validation_issues": validation_issues,
        "source_diagnostics": source_diagnostics,
        "notes": [issue["message"] for issue in validation_issues if issue["severity"] != "error"],
    }
