import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import Company, RawEntry, Source
from tech_daily.normalize import normalize_entry


class NormalizeTests(unittest.TestCase):
    def test_normalize_entry_cleans_anthropic_title_prefix(self) -> None:
        company = Company(slug="anthropic", name="Anthropic", region="us")
        source = Source(kind="html", url="https://www.anthropic.com/news", label="Anthropic News")
        entry = RawEntry(
            company_slug="anthropic",
            company_name="Anthropic",
            source_label="news",
            title="Apr 24, 2026 Announcements Anthropic and NEC collaborate to build Japan’s largest AI engineering workforce",
            url="https://www.anthropic.com/news/anthropic-nec",
        )
        normalized = normalize_entry(company, source, entry)
        self.assertEqual(
            normalized.title,
            "Anthropic and NEC collaborate to build Japan’s largest AI engineering workforce",
        )

    def test_normalize_entry_cleans_repeated_whitespace(self) -> None:
        company = Company(slug="anthropic", name="Anthropic", region="us")
        source = Source(kind="html", url="https://www.anthropic.com/news", label="Anthropic News")
        entry = RawEntry(
            company_slug="anthropic",
            company_name="Anthropic",
            source_label="news",
            title="  Agents   for   financial services  ",
            url="https://www.anthropic.com/news/finance-agents",
            summary="  New   workflow    tooling ",
        )
        normalized = normalize_entry(company, source, entry)
        self.assertEqual(normalized.title, "Agents for financial services")
        self.assertEqual(normalized.summary, "New workflow tooling")

    def test_normalize_entry_does_not_infer_incomplete_date_from_url(self) -> None:
        company = Company(slug="meta", name="Meta", region="us")
        source = Source(kind="html", url="https://about.fb.com/news/", label="Meta News")
        entry = RawEntry(
            company_slug="meta",
            company_name="Meta",
            source_label="news",
            title="Meta Partners With Broadcom to Co-Develop Custom AI Silicon",
            url="https://about.fb.com/news/2026/04/meta-partners-with-broadcom-to-co-develop-custom-ai-silicon/",
        )
        normalized = normalize_entry(company, source, entry)
        self.assertEqual(normalized.published_at, "")

    def test_normalize_entry_infers_full_date_from_url(self) -> None:
        company = Company(slug="meta", name="Meta", region="us")
        source = Source(kind="html", url="https://about.fb.com/news/", label="Meta News")
        entry = RawEntry(
            company_slug="meta",
            company_name="Meta",
            source_label="news",
            title="Meta launches AI",
            url="https://about.fb.com/news/2026/05/10/meta-launches-ai/",
        )
        normalized = normalize_entry(company, source, entry)
        self.assertEqual(normalized.published_at, "2026-05-10")


if __name__ == "__main__":
    unittest.main()
