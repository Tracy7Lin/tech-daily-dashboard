import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.fetchers.article_page import ArticleMetadata
from tech_daily.fetchers.html_index import HtmlIndexFetcher
from tech_daily.metadata_cache import ArticleMetadataCache
from tech_daily.models import Company, Source


class HtmlIndexFetcherCacheTests(unittest.TestCase):
    @patch("tech_daily.fetchers.html_index.fetch_text")
    def test_fetcher_uses_cached_article_metadata(self, mock_fetch_text) -> None:
        with TemporaryDirectory() as temp_dir:
            cache = ArticleMetadataCache(Path(temp_dir) / "article-cache.json")
            cache.set(
                "https://example.com/news/post-a",
                ArticleMetadata(
                    title="Cached title",
                    published_at="2026-05-10T10:00:00Z",
                    description="Cached summary",
                ),
            )
            fetcher = HtmlIndexFetcher(metadata_cache=cache)
            company = Company(slug="meta", name="Meta", region="us")
            source = Source(
                kind="html",
                url="https://example.com/news",
                label="Meta News",
                path_prefixes=["/news/"],
                include_patterns=["meta"],
                fetch_article_details=True,
                detail_fetch_limit=1,
            )
            mock_fetch_text.return_value = """
            <html><body><a href="/news/post-a">Meta launches AI tooling</a></body></html>
            """

            entries, status = fetcher.fetch(company, source)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].title, "Cached title")
            self.assertEqual(entries[0].published_at, "2026-05-10T10:00:00Z")
            self.assertEqual(status.fetched_count, 1)
            self.assertEqual(mock_fetch_text.call_count, 1)

    @patch("tech_daily.fetchers.html_index.fetch_text")
    def test_fetcher_reads_cache_even_when_detail_fetch_limit_skips_network(self, mock_fetch_text) -> None:
        with TemporaryDirectory() as temp_dir:
            cache = ArticleMetadataCache(Path(temp_dir) / "article-cache.json")
            cache.set(
                "https://example.com/news/post-a",
                ArticleMetadata(
                    title="Cached title",
                    published_at="2026-05-10T10:00:00Z",
                    description="Cached summary",
                ),
            )
            fetcher = HtmlIndexFetcher(metadata_cache=cache)
            company = Company(slug="meta", name="Meta", region="us")
            source = Source(
                kind="html",
                url="https://example.com/news",
                label="Meta News",
                path_prefixes=["/news/"],
                include_patterns=["meta"],
                fetch_article_details=True,
                detail_fetch_limit=0,
            )
            mock_fetch_text.return_value = """
            <html><body><a href="/news/post-a">Meta launches AI tooling</a></body></html>
            """

            entries, _ = fetcher.fetch(company, source)
            self.assertEqual(entries[0].published_at, "2026-05-10T10:00:00Z")
            self.assertEqual(mock_fetch_text.call_count, 1)


if __name__ == "__main__":
    unittest.main()
