from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .pipeline import generate_daily_report


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def resolve_report_date(now: datetime | None = None) -> str:
    current = now or datetime.now(tz=SHANGHAI_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=SHANGHAI_TZ)
    else:
        current = current.astimezone(SHANGHAI_TZ)
    return current.strftime("%Y-%m-%d")


def generate_today_report(output_dir: Path | None = None, now: datetime | None = None):
    return generate_daily_report(resolve_report_date(now=now), output_dir=output_dir)
