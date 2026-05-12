import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.config_validation import validate_companies
from tech_daily.models import Company, Source


class ConfigValidationTests(unittest.TestCase):
    def test_validate_companies_reports_duplicate_slug_and_missing_source_url(self) -> None:
        companies = [
            Company(
                slug="openai",
                name="OpenAI",
                region="US",
                sources=[Source(kind="rss", url="", label="RSS")],
            ),
            Company(
                slug="openai",
                name="OpenAI Duplicate",
                region="US",
                sources=[Source(kind="rss", url="https://example.com/rss", label="RSS")],
            ),
        ]
        issues = validate_companies(companies)
        codes = {issue["code"] for issue in issues}
        self.assertIn("duplicate_company_slug", codes)
        self.assertIn("missing_source_url", codes)

    def test_validate_companies_reports_unsupported_source_kind(self) -> None:
        companies = [
            Company(
                slug="apple",
                name="Apple",
                region="US",
                sources=[Source(kind="json", url="https://example.com/feed", label="Feed")],
            )
        ]
        issues = validate_companies(companies)
        self.assertEqual(issues[0]["code"], "unsupported_source_kind")


if __name__ == "__main__":
    unittest.main()
