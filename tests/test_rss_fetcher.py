import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.fetchers.rss import parse_rss_entries


class RssFetcherTests(unittest.TestCase):
    def test_parse_rss_entries_extracts_title_and_link(self) -> None:
        xml_text = (
            "<rss><channel><item><title>Launch</title>"
            "<link>https://example.com/a</link>"
            "<description>summary</description></item></channel></rss>"
        )
        entries = parse_rss_entries(xml_text)
        self.assertEqual(entries[0].title, "Launch")
        self.assertEqual(entries[0].url, "https://example.com/a")


if __name__ == "__main__":
    unittest.main()
