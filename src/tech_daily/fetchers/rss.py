from __future__ import annotations

import xml.etree.ElementTree as ET

from ..models import Company, RawEntry, Source, SourceStatus
from .base import Fetcher
from .http import describe_fetch_error, fetch_text

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_rss_entries(
    xml_text: str,
    company_slug: str = "",
    company_name: str = "",
    source_label: str = "",
) -> list[RawEntry]:
    root = ET.fromstring(xml_text)
    entries: list[RawEntry] = []

    for item in root.findall(".//item"):
        entries.append(
            RawEntry(
                company_slug=company_slug,
                company_name=company_name,
                source_label=source_label,
                title=(item.findtext("title") or "").strip(),
                url=(item.findtext("link") or "").strip(),
                summary=(item.findtext("description") or "").strip(),
                published_at=(item.findtext("pubDate") or "").strip(),
                requires_published_at=False,
            )
        )

    if entries:
        return [entry for entry in entries if entry.title and entry.url]

    for item in root.findall(".//atom:entry", ATOM_NS):
        link = item.find("atom:link", ATOM_NS)
        entries.append(
            RawEntry(
                company_slug=company_slug,
                company_name=company_name,
                source_label=source_label,
                title=(item.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip(),
                url=(link.attrib.get("href", "") if link is not None else "").strip(),
                summary=(item.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip(),
                published_at=(item.findtext("atom:updated", default="", namespaces=ATOM_NS) or "").strip(),
                requires_published_at=False,
            )
        )
    return [entry for entry in entries if entry.title and entry.url]


class RssFetcher(Fetcher):
    def fetch(self, company: Company, source: Source) -> tuple[list[RawEntry], SourceStatus]:
        try:
            payload = fetch_text(source.url)
            entries = parse_rss_entries(payload, company.slug, company.name, source.label or source.kind)
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
