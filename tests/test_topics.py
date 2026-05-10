import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import EnrichedEntry, RawEntry
from tech_daily.topics import group_entries_by_topic, topic_id_for_entry


class TopicTests(unittest.TestCase):
    def test_group_entries_by_topic_clusters_shared_tags(self) -> None:
        entry = EnrichedEntry(
            raw=RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="news",
                title="Agent updates",
                url="https://example.com",
            ),
            tags=["ai", "developer"],
            category="technology",
            importance=3,
            summary_cn="summary",
            comparison_angle="ai、developer",
        )
        grouped = group_entries_by_topic([entry])
        self.assertIn("ai-agent", grouped)

    def test_topic_id_for_entry_maps_model_release(self) -> None:
        entry = EnrichedEntry(
            raw=RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="news",
                title="GPT-5.5 Instant",
                url="https://example.com",
            ),
            tags=["ai", "model"],
            category="technology",
            importance=4,
            summary_cn="summary",
            comparison_angle="ai、model",
        )
        self.assertEqual(topic_id_for_entry(entry), "model-release")

    def test_topic_id_for_entry_maps_customer_adoption(self) -> None:
        entry = EnrichedEntry(
            raw=RawEntry(
                company_slug="openai",
                company_name="OpenAI",
                source_label="news",
                title="Uber uses OpenAI",
                url="https://example.com",
            ),
            tags=["ai", "customer"],
            category="technology",
            importance=4,
            summary_cn="summary",
            comparison_angle="ai、customer",
        )
        self.assertEqual(topic_id_for_entry(entry), "customer-adoption")


if __name__ == "__main__":
    unittest.main()
