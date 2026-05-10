import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import Company, Source


class ModelTests(unittest.TestCase):
    def test_company_contains_multiple_sources(self) -> None:
        company = Company(
            slug="openai",
            name="OpenAI",
            region="us",
            sources=[Source(kind="rss", url="https://openai.com/news/rss.xml", include_patterns=["ai"], detail_fetch_limit=2, require_published_at=False)],
        )
        self.assertEqual(company.slug, "openai")
        self.assertEqual(company.sources[0].kind, "rss")
        self.assertEqual(company.sources[0].include_patterns, ["ai"])
        self.assertEqual(company.sources[0].detail_fetch_limit, 2)
        self.assertFalse(company.sources[0].require_published_at)


if __name__ == "__main__":
    unittest.main()
