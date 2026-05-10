from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from .models import EnrichedEntry, RawEntry

NOISE_TERMS = ("career", "jobs", "hiring", "register now", "webinar")
GENERIC_TITLES = {
    "entertainment",
    "sustainability",
    "company news",
    "innovation at amazon",
    "meta quest",
    "ai glasses",
}
GENERIC_PATH_FRAGMENTS = ("/tag/", "/tags/", "/category/", "/categories/")


def matches_report_date(published_at: str, date_str: str) -> bool:
    if not published_at:
        return True

    try:
        return parsedate_to_datetime(published_at).date().isoformat() == date_str
    except (TypeError, ValueError, IndexError, OverflowError):
        pass

    for parser in (datetime.fromisoformat,):
        try:
            return parser(published_at).date().isoformat() == date_str
        except ValueError:
            continue

    for pattern in ("%b %d, %Y", "%B %d, %Y", "%b. %d, %Y", "%B %d %Y"):
        try:
            return datetime.strptime(published_at, pattern).date().isoformat() == date_str
        except ValueError:
            continue
    return True


def _is_generic_path(url: str) -> bool:
    path = urlsplit(url).path.lower().rstrip("/")
    if not path:
        return True
    return any(fragment in path for fragment in GENERIC_PATH_FRAGMENTS)


def is_noise_entry(entry: EnrichedEntry) -> bool:
    title = " ".join(entry.raw.title.lower().split())
    text = f"{entry.raw.title} {entry.raw.summary}".lower()

    if entry.raw.requires_published_at and not entry.raw.published_at:
        return True
    if any(noise in text for noise in NOISE_TERMS):
        return True
    if title in GENERIC_TITLES:
        return True
    if _is_generic_path(entry.raw.url):
        return True
    if entry.importance <= 1 and entry.category == "general":
        return True
    return False


def filter_high_signal_entries(entries: Iterable[EnrichedEntry]) -> list[EnrichedEntry]:
    return [entry for entry in entries if not is_noise_entry(entry)]
