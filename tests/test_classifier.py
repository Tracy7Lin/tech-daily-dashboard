import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.classifier import classify_entry
from tech_daily.models import RawEntry


class ClassifierTests(unittest.TestCase):
    def test_classify_entry_marks_ai_product_news(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="OpenAI launches new agent tooling",
            url="https://example.com",
            summary="New agent APIs for developers",
        )
        result = classify_entry(entry)
        self.assertIn("ai", result.tags)
        self.assertIn("product", result.tags)

    def test_classify_entry_marks_model_and_safety_keywords(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="GPT-5.5 improves trusted access for cyber teams",
            url="https://example.com",
            summary="New model safeguards and security workflows for enterprise users",
        )
        result = classify_entry(entry)
        self.assertIn("model", result.tags)
        self.assertIn("safety", result.tags)
        self.assertGreaterEqual(result.importance, 4)
        self.assertIn("OpenAI", result.summary_cn)
        self.assertIn("安全", result.summary_cn)

    def test_classify_entry_does_not_treat_system_card_as_hardware(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="GPT-5.5 Instant System Card",
            url="https://example.com",
            summary="Documentation for the GPT-5.5 Instant model and its safeguards.",
        )
        result = classify_entry(entry)
        self.assertNotIn("hardware", result.tags)
        self.assertIn("model", result.tags)

    def test_classify_entry_does_not_match_ai_inside_other_words(self) -> None:
        entry = RawEntry(
            company_slug="google",
            company_name="Google",
            source_label="Google Blog",
            title="Google Health Coach is becoming globally available",
            url="https://example.com/google-health-coach",
            summary="Personalized insights on workouts, sleep, recovery and wellbeing.",
        )
        result = classify_entry(entry)
        self.assertNotIn("ai", result.tags)
        self.assertNotIn("safety", result.tags)

    def test_classify_entry_matches_plural_and_inflected_keywords(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI launches new agents APIs for developers",
            url="https://example.com/openai-agents-apis",
            summary="The release expands developer platforms for enterprise teams.",
        )
        result = classify_entry(entry)
        self.assertIn("ai", result.tags)
        self.assertIn("product", result.tags)
        self.assertIn("developer", result.tags)

    def test_classify_entry_does_not_use_url_taxonomy_as_developer_signal(self) -> None:
        entry = RawEntry(
            company_slug="google",
            company_name="Google",
            source_label="Google Blog",
            title="Google Health Coach is becoming globally available",
            url="https://blog.google/products-and-platforms/products/google-health/google-health-coach/",
            summary="Google Health Coach, now available globally, provides personalized insights on workouts, sleep, recovery and wellbeing.",
        )
        result = classify_entry(entry)
        self.assertNotIn("developer", result.tags)


if __name__ == "__main__":
    unittest.main()
