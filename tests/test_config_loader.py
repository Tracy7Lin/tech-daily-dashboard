import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.config_loader import load_companies


class ConfigLoaderTests(unittest.TestCase):
    def test_load_companies_returns_default_watchlist(self) -> None:
        companies = load_companies()
        self.assertEqual(len(companies), 15)
        self.assertTrue(companies[0].slug)


if __name__ == "__main__":
    unittest.main()
