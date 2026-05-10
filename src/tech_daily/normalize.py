from __future__ import annotations

import re
from dataclasses import replace
from urllib.parse import urlsplit

from .models import Company, RawEntry, Source

MONTH_PATTERN = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+\d{4}"
LEADING_DATE_PATTERNS = [
    re.compile(rf"^(Announcements|Product|Research|Policy)\s+({MONTH_PATTERN})\s+", re.IGNORECASE),
    re.compile(rf"^({MONTH_PATTERN})\s+(Announcements|Product|Research|Policy)\s+", re.IGNORECASE),
]
URL_DATE_PATTERN = re.compile(r"/(?P<year>20\d{2})/(?P<month>\d{2})/(?:(?P<day>\d{2})/)?")


def _clean_whitespace(text: str) -> str:
    return " ".join(text.split())


def _strip_leading_date_tokens(title: str) -> str:
    cleaned = _clean_whitespace(title)
    for pattern in LEADING_DATE_PATTERNS:
        updated = pattern.sub("", cleaned)
        if updated != cleaned:
            return updated.strip(" -:")
    return cleaned


def _infer_published_at_from_url(url: str) -> str:
    match = URL_DATE_PATTERN.search(urlsplit(url).path)
    if not match or not match.group("day"):
        return ""
    year = match.group("year")
    month = match.group("month")
    day = match.group("day")
    return f"{year}-{month}-{day}"


def normalize_entry(company: Company, source: Source, entry: RawEntry) -> RawEntry:
    title = _strip_leading_date_tokens(entry.title)
    published_at = entry.published_at.strip() or _infer_published_at_from_url(entry.url)

    if company.slug == "anthropic":
        title = title.replace("Announcements ", "").replace("Product ", "").strip()

    return replace(
        entry,
        title=title,
        summary=_clean_whitespace(entry.summary),
        content=_clean_whitespace(entry.content),
        published_at=published_at,
        source_label=source.label or entry.source_label,
    )
