from __future__ import annotations

from dataclasses import replace
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit

from .fetchers.base import Fetcher
from .fetchers.html_index import HtmlIndexFetcher
from .fetchers.rss import RssFetcher
from .models import Company, RawEntry, Source, SourceStatus
from .normalize import normalize_entry


FETCHERS: dict[str, Fetcher] = {
    "rss": RssFetcher(),
    "atom": RssFetcher(),
    "html": HtmlIndexFetcher(),
}


def _canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


def _matches_source_rules(entry: RawEntry, source: Source) -> bool:
    blob = f"{entry.title} {entry.summary} {entry.url}".lower()
    path = urlsplit(entry.url).path

    if source.path_prefixes and not any(path.startswith(prefix) for prefix in source.path_prefixes):
        return False
    if source.include_patterns and not any(pattern.lower() in blob for pattern in source.include_patterns):
        return False
    if source.exclude_patterns and any(pattern.lower() in blob for pattern in source.exclude_patterns):
        return False
    return True


def filter_source_entries(entries: Iterable[RawEntry], source: Source) -> list[RawEntry]:
    return [entry for entry in entries if _matches_source_rules(entry, source)]


def dedupe_entries(entries: Iterable[RawEntry]) -> list[RawEntry]:
    seen_keys: set[tuple[str, str]] = set()
    deduped: list[RawEntry] = []
    for entry in entries:
        url_key = _canonicalize_url(entry.url)
        title_key = " ".join(entry.title.lower().split())
        key = (entry.company_slug, url_key or title_key)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(entry)
    return deduped


def collect_entries(companies: Iterable[Company]) -> tuple[list[RawEntry], list[SourceStatus]]:
    entries: list[RawEntry] = []
    statuses: list[SourceStatus] = []
    for company in companies:
        for source in company.sources:
            fetcher = FETCHERS.get(source.kind)
            if fetcher is None:
                statuses.append(
                    SourceStatus(
                        company_slug=company.slug,
                        company_name=company.name,
                        source_label=source.label or source.kind,
                        source_url=source.url,
                        ok=False,
                        message=f"unsupported_source_kind:{source.kind}",
                    )
                )
                continue
            source_entries, status = fetcher.fetch(company, source)
            normalized_entries = [normalize_entry(company, source, entry) for entry in source_entries]
            kept_entries = filter_source_entries(normalized_entries, source)
            entries.extend(kept_entries)
            statuses.append(
                replace(
                    status,
                    message=f"{status.message};kept:{len(kept_entries)}",
                    fetched_count=len(normalized_entries),
                    kept_count=len(kept_entries),
                )
            )
    return dedupe_entries(entries), statuses
