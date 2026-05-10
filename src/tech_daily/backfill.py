from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from .models import DailyReport
from .pipeline import generate_daily_report


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def build_backfill_dates(end_date: str, days: int) -> list[str]:
    if days <= 0:
        return []
    end = _parse_date(end_date)
    return [
        (end - timedelta(days=offset)).isoformat()
        for offset in reversed(range(days))
    ]


def generate_backfill_reports(end_date: str, days: int, output_dir: Path | None = None) -> list[DailyReport]:
    reports: list[DailyReport] = []
    for report_date in build_backfill_dates(end_date, days):
        reports.append(generate_daily_report(report_date, output_dir=output_dir))
    return reports
