from __future__ import annotations

import json
from pathlib import Path

from .models import DailyReport


def load_report_snapshots(output_dir: Path) -> list[DailyReport]:
    reports: list[DailyReport] = []
    for report_path in sorted(output_dir.glob("*/report.json")):
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        reports.append(
            DailyReport(
                date=payload["date"],
                headline=payload["headline"],
                hottest_topics=payload.get("hottest_topics", []),
                total_entries=payload.get("total_entries", 0),
                companies_covered=payload.get("companies_covered", 0),
            )
        )
    reports.sort(key=lambda report: report.date, reverse=True)
    return reports
