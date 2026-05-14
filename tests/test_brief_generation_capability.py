import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.capabilities.brief_generation import BriefGenerationCapability, BriefGenerationInput
from tech_daily.models import RawEntry


class BriefGenerationCapabilityTests(unittest.TestCase):
    def _build_entry(self) -> RawEntry:
        return RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI adds new admin controls",
            url="https://openai.com/news/example",
            summary="OpenAI introduced new admin controls for enterprise teams.",
            published_at="2026-05-14T08:00:00+08:00",
        )

    def test_generate_returns_structured_result(self) -> None:
        entry = self._build_entry()
        capability = BriefGenerationCapability(mode="rule")

        result = capability.generate(
            BriefGenerationInput(
                company=entry.company_name,
                title=entry.title,
                summary=entry.summary,
                tags=["developer", "enterprise"],
                category="product",
                url=entry.url,
                published_at=entry.published_at,
                raw_entry=entry,
            )
        )

        self.assertTrue(result.summary_cn)
        self.assertTrue(result.angle)
        self.assertEqual(result.confidence, "high")
        self.assertEqual(result.mode_used, "rule")


if __name__ == "__main__":
    unittest.main()
