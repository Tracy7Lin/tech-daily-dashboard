import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.fetchers.html_index import parse_html_links
from tech_daily.models import Source


class HtmlFetcherTests(unittest.TestCase):
    def test_parse_html_links_applies_source_rules(self) -> None:
        html = """
        <html><body>
          <a href="/news/product-launch">AI product launch for enterprise</a>
          <a href="/careers/open-role">AI engineer hiring now</a>
          <a href="https://external.example.com/news/x">external link</a>
        </body></html>
        """
        source = Source(
            kind="html",
            url="https://example.com/news",
            include_patterns=["ai", "product"],
            exclude_patterns=["hiring", "careers"],
            path_prefixes=["/news/"],
        )
        links = parse_html_links("https://example.com/news", html, source=source)
        self.assertEqual(links, [("https://example.com/news/product-launch", "AI product launch for enterprise")])


if __name__ == "__main__":
    unittest.main()
