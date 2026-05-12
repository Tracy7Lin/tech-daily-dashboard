from __future__ import annotations

from pathlib import Path

from .config_loader import load_companies
from .config_validation import build_source_diagnostics, validate_companies
from .llm_runtime import build_llm_client
from .settings import DEFAULT_SETTINGS, Settings


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
        "validation_issue_count": len(validation_issues),
        "validation_issues": validation_issues,
        "source_diagnostics": source_diagnostics,
        "notes": notes,
    }
