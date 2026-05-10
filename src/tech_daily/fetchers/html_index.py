from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
from dataclasses import replace
from urllib.parse import urljoin, urlparse

from ..metadata_cache import ArticleMetadataCache
from ..models import Company, RawEntry, Source, SourceStatus
from .article_page import parse_article_metadata
from .base import Fetcher
from .http import describe_fetch_error, fetch_text


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_anchor = False
        self._href = ""
        self._text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        self._in_anchor = True
        self._href = href
        self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._in_anchor:
            return
        text = " ".join(part.strip() for part in self._text_parts if part.strip()).strip()
        self.links.append((self._href, unescape(text)))
        self._in_anchor = False
        self._href = ""
        self._text_parts = []


def _matches_source_rules(url: str, text: str, source: Source) -> bool:
    blob = f"{url} {text}".lower()
    parsed = urlparse(url)

    if source.path_prefixes and not any(parsed.path.startswith(prefix) for prefix in source.path_prefixes):
        return False
    if source.include_patterns and not any(pattern.lower() in blob for pattern in source.include_patterns):
        return False
    if source.exclude_patterns and any(pattern.lower() in blob for pattern in source.exclude_patterns):
        return False
    return True


def parse_html_links(base_url: str, html_text: str, source: Source | None = None) -> list[tuple[str, str]]:
    parser = LinkCollector()
    parser.feed(html_text)

    base_host = urlparse(base_url).netloc
    links: list[tuple[str, str]] = []
    for href, text in parser.links:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != base_host:
            continue
        if not text or len(text) < 8:
            continue
        if source is not None and not _matches_source_rules(absolute, text, source):
            continue
        links.append((absolute, text))
    return links


class HtmlIndexFetcher(Fetcher):
    def __init__(self, metadata_cache: ArticleMetadataCache | None = None) -> None:
        self.metadata_cache = metadata_cache or ArticleMetadataCache()

    def _build_entry(self, company: Company, source: Source, url: str, title: str, fetch_details: bool) -> RawEntry:
        entry = RawEntry(
            company_slug=company.slug,
            company_name=company.name,
            source_label=source.label or source.kind,
            title=title,
            url=url,
            requires_published_at=source.require_published_at,
        )
        cached = self.metadata_cache.get(url)
        if cached is not None:
            return replace(
                entry,
                title=cached.title or entry.title,
                published_at=cached.published_at,
                summary=cached.description,
            )
        if not source.fetch_article_details or not fetch_details:
            return entry
        try:
            article_html = fetch_text(url, timeout=10)
            metadata = parse_article_metadata(article_html)
            self.metadata_cache.set(url, metadata)
            return replace(
                entry,
                title=metadata.title or entry.title,
                published_at=metadata.published_at,
                summary=metadata.description,
            )
        except Exception:
            return entry

    def fetch(self, company: Company, source: Source) -> tuple[list[RawEntry], SourceStatus]:
        try:
            html_text = fetch_text(source.url)
            links = parse_html_links(source.url, html_text, source=source)
            entries = [
                self._build_entry(company, source, url, title, index < source.detail_fetch_limit)
                for index, (url, title) in enumerate(links[: source.max_entries])
            ]
            self.metadata_cache.save()
            return entries, SourceStatus(
                company_slug=company.slug,
                company_name=company.name,
                source_label=source.label or source.kind,
                source_url=source.url,
                ok=True,
                message=f"fetched:{len(entries)}",
                fetched_count=len(entries),
                kept_count=len(entries),
            )
        except Exception as error:
            return [], SourceStatus(
                company_slug=company.slug,
                company_name=company.name,
                source_label=source.label or source.kind,
                source_url=source.url,
                ok=False,
                message=describe_fetch_error(error),
            )
