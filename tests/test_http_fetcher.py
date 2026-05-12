import unittest
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.fetchers.http import fetch_text


class _FakeHeaders:
    @staticmethod
    def get_content_charset():
        return "utf-8"


class _FakeResponse:
    headers = _FakeHeaders()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @staticmethod
    def read():
        return b"ok"


class HttpFetcherTests(unittest.TestCase):
    @patch("tech_daily.fetchers.http.urlopen")
    def test_fetch_text_uses_browser_like_headers(self, mock_urlopen) -> None:
        captured = {}

        def _fake_urlopen(request, timeout=20):
            captured["headers"] = dict(request.header_items())
            return _FakeResponse()

        mock_urlopen.side_effect = _fake_urlopen
        text = fetch_text("https://example.com/news")

        self.assertEqual(text, "ok")
        self.assertIn("User-agent", captured["headers"])
        self.assertIn("Accept", captured["headers"])
        self.assertIn("Accept-language", captured["headers"])


if __name__ == "__main__":
    unittest.main()
