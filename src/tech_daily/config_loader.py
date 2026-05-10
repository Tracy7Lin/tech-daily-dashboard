from __future__ import annotations

import json

from .models import Company, Source
from .paths import CONFIG_DIR


COMPANIES_FILE = CONFIG_DIR / "companies.json"


def load_companies() -> list[Company]:
    payload = json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))
    companies: list[Company] = []
    for item in payload:
        sources = [
            Source(
                kind=source["kind"],
                url=source["url"],
                label=source.get("label", ""),
                include_patterns=source.get("include_patterns", []),
                exclude_patterns=source.get("exclude_patterns", []),
                path_prefixes=source.get("path_prefixes", []),
                max_entries=source.get("max_entries", 20),
                fetch_article_details=source.get("fetch_article_details", False),
                detail_fetch_limit=source.get("detail_fetch_limit", 5),
                require_published_at=source.get("require_published_at", False),
            )
            for source in item.get("sources", [])
        ]
        companies.append(
            Company(
                slug=item["slug"],
                name=item["name"],
                region=item["region"],
                sources=sources,
            )
        )
    return companies
