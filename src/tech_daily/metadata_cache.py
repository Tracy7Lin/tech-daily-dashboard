from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .fetchers.article_page import ArticleMetadata
from .paths import DATA_DIR


ARTICLE_METADATA_CACHE_FILE = DATA_DIR / "article_metadata_cache.json"


class ArticleMetadataCache:
    def __init__(self, cache_file: Path | None = None) -> None:
        self.cache_file = cache_file or ARTICLE_METADATA_CACHE_FILE
        self._data: dict[str, ArticleMetadata] | None = None

    def _ensure_loaded(self) -> None:
        if self._data is not None:
            return
        if not self.cache_file.exists():
            self._data = {}
            return
        payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
        self._data = {
            url: ArticleMetadata(**metadata)
            for url, metadata in payload.items()
        }

    def get(self, url: str) -> ArticleMetadata | None:
        self._ensure_loaded()
        assert self._data is not None
        return self._data.get(url)

    def set(self, url: str, metadata: ArticleMetadata) -> None:
        self._ensure_loaded()
        assert self._data is not None
        self._data[url] = metadata

    def save(self) -> None:
        self._ensure_loaded()
        assert self._data is not None
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {url: asdict(metadata) for url, metadata in self._data.items()}
        self.cache_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
