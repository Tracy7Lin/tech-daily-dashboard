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


if __name__ == "__main__":
    unittest.main()
