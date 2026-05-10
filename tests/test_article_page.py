import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.fetchers.article_page import parse_article_metadata


class ArticlePageTests(unittest.TestCase):
    def test_parse_article_metadata_prefers_meta_tags(self) -> None:
        html = """
        <html><head>
          <meta property="article:published_time" content="2026-05-10T08:30:00Z" />
          <meta name="description" content="Meta launches new AI tooling for developers." />
          <meta property="og:title" content="Meta launches AI tooling" />
        </head><body></body></html>
        """
        metadata = parse_article_metadata(html)
        self.assertEqual(metadata.published_at, "2026-05-10T08:30:00Z")
        self.assertEqual(metadata.description, "Meta launches new AI tooling for developers.")
        self.assertEqual(metadata.title, "Meta launches AI tooling")

    def test_parse_article_metadata_falls_back_to_json_or_visible_date(self) -> None:
        html = """
        <html><body>
          <article>
            <h1>Agents for financial services</h1>
            <div class="body-3 agate">May 5, 2026</div>
            <script>{"publishedOn":"2026-05-05T16:00:00.000Z"}</script>
          </article>
        </body></html>
        """
        metadata = parse_article_metadata(html)
        self.assertEqual(metadata.title, "Agents for financial services")
        self.assertEqual(metadata.published_at, "2026-05-05T16:00:00.000Z")


if __name__ == "__main__":
    unittest.main()
