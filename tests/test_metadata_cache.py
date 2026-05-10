import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.fetchers.article_page import ArticleMetadata
from tech_daily.metadata_cache import ArticleMetadataCache


class MetadataCacheTests(unittest.TestCase):
    def test_cache_round_trip_persists_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            cache = ArticleMetadataCache(Path(temp_dir) / "cache.json")
            cache.set(
                "https://example.com/a",
                ArticleMetadata(
                    title="Example title",
                    published_at="2026-05-10T10:00:00Z",
                    description="Example summary",
                ),
            )
            cache.save()

            reloaded = ArticleMetadataCache(Path(temp_dir) / "cache.json")
            metadata = reloaded.get("https://example.com/a")
            self.assertIsNotNone(metadata)
            assert metadata is not None
            self.assertEqual(metadata.title, "Example title")
            self.assertEqual(metadata.published_at, "2026-05-10T10:00:00Z")


if __name__ == "__main__":
    unittest.main()
