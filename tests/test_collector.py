import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.collector import dedupe_entries, filter_source_entries
from tech_daily.models import RawEntry, Source


class CollectorTests(unittest.TestCase):
    def test_filter_source_entries_applies_include_exclude_patterns(self) -> None:
        source = Source(
            kind="rss",
            url="https://example.com/feed",
            include_patterns=["ai", "agent"],
            exclude_patterns=["jobs"],
        )
        entries = [
            RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="rss",
                title="New agent APIs for enterprise AI",
                url="https://example.com/news/agent",
            ),
            RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="rss",
                title="Open jobs in AI research",
                url="https://example.com/news/jobs",
            ),
        ]
        filtered = filter_source_entries(entries, source)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "New agent APIs for enterprise AI")

    def test_filter_source_entries_can_exclude_entertainment_paths(self) -> None:
        source = Source(
            kind="html",
            url="https://www.aboutamazon.com/news",
            include_patterns=["amazon", "ai"],
            exclude_patterns=["entertainment", "prime video"],
            path_prefixes=["/news/"],
        )
        entries = [
            RawEntry(
                company_slug="amazon",
                company_name="Amazon",
                source_label="html",
                title="How to watch Citadel on Prime Video",
                url="https://www.aboutamazon.com/news/entertainment/prime-video-citadel-season-2-watch",
            ),
            RawEntry(
                company_slug="amazon",
                company_name="Amazon",
                source_label="html",
                title="Amazon expands Alexa AI assistant",
                url="https://www.aboutamazon.com/news/devices/alexa-plus-international-launch",
            ),
        ]
        filtered = filter_source_entries(entries, source)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Amazon expands Alexa AI assistant")

    def test_dedupe_entries_removes_same_company_duplicate_urls(self) -> None:
        entries = [
            RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="rss",
                title="Launch",
                url="https://example.com/news/launch/",
            ),
            RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="html",
                title="Launch duplicate",
                url="https://example.com/news/launch",
            ),
            RawEntry(
                company_slug="google",
                company_name="Google",
                source_label="rss",
                title="Launch",
                url="https://example.com/news/launch",
            ),
        ]
        deduped = dedupe_entries(entries)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].company_slug, "openai")
        self.assertEqual(deduped[1].company_slug, "google")


if __name__ == "__main__":
    unittest.main()
