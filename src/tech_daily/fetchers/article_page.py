from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser


VISIBLE_DATE_PATTERN = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}\b"
)
ISO_FIELD_PATTERNS = [
    re.compile(r'"article:published_time"\s*content="([^"]+)"', re.IGNORECASE),
    re.compile(r'"datePublished"\s*:\s*"([^"]+)"', re.IGNORECASE),
    re.compile(r'"publishedOn"\s*:\s*"([^"]+)"', re.IGNORECASE),
    re.compile(r'"dateModified"\s*:\s*"([^"]+)"', re.IGNORECASE),
]


@dataclass(frozen=True)
class ArticleMetadata:
    title: str = ""
    published_at: str = ""
    description: str = ""


class ArticleMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.published_at = ""
        self.description = ""
        self.title = ""
        self._in_time = False
        self._in_h1 = False
        self._time_parts: list[str] = []
        self._h1_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag == "meta":
            key = (attrs_map.get("property") or attrs_map.get("name") or "").lower()
            content = (attrs_map.get("content") or "").strip()
            if key in {"article:published_time", "og:published_time", "pubdate"} and content and not self.published_at:
                self.published_at = content
            if key in {"description", "og:description"} and content and not self.description:
                self.description = content
            if key in {"og:title", "twitter:title"} and content and not self.title:
                self.title = content
        if tag == "time":
            self._in_time = True
            self._time_parts = []
            datetime_value = (attrs_map.get("datetime") or "").strip()
            if datetime_value and not self.published_at:
                self.published_at = datetime_value
        if tag == "h1":
            self._in_h1 = True
            self._h1_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_time:
            self._time_parts.append(data)
        if self._in_h1:
            self._h1_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "time":
            if not self.published_at:
                self.published_at = " ".join(part.strip() for part in self._time_parts if part.strip())
            self._in_time = False
            self._time_parts = []
        if tag == "h1":
            if not self.title:
                self.title = " ".join(part.strip() for part in self._h1_parts if part.strip())
            self._in_h1 = False
            self._h1_parts = []


def _fallback_published_at(html_text: str) -> str:
    for pattern in ISO_FIELD_PATTERNS:
        match = pattern.search(html_text)
        if match:
            return match.group(1).strip()

    match = VISIBLE_DATE_PATTERN.search(html_text)
    if match:
        return match.group(0).strip()
    return ""


def parse_article_metadata(html_text: str) -> ArticleMetadata:
    parser = ArticleMetadataParser()
    parser.feed(html_text)
    published_at = parser.published_at.strip() or _fallback_published_at(html_text)
    description = parser.description.strip()
    title = parser.title.strip()
    return ArticleMetadata(title=title, published_at=published_at, description=description)
