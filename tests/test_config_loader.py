import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.config_loader import load_companies


class ConfigLoaderTests(unittest.TestCase):
    def test_load_companies_returns_default_watchlist(self) -> None:
        companies = load_companies()
        self.assertEqual(len(companies), 15)
        self.assertTrue(companies[0].slug)

    def test_tesla_and_tencent_sources_use_stable_official_entrypoints(self) -> None:
        companies = {company.slug: company for company in load_companies()}

        tesla_source = companies["tesla"].sources[0]
        self.assertEqual(tesla_source.label, "Tesla IR Press")
        self.assertEqual(tesla_source.url, "https://ir.tesla.com/press?view=all")
        self.assertIn("/press", tesla_source.path_prefixes)

        tencent_source = companies["tencent"].sources[0]
        self.assertEqual(tencent_source.url, "https://www.tencent.com/en-us/")
        self.assertIn("/en-us/articles/", tencent_source.path_prefixes)

    def test_bytedance_alibaba_and_huawei_sources_use_accessible_official_entrypoints(self) -> None:
        companies = {company.slug: company for company in load_companies()}

        bytedance_source = companies["bytedance"].sources[0]
        self.assertEqual(bytedance_source.label, "ByteDance Seed")
        self.assertEqual(bytedance_source.url, "https://seed.bytedance.com/en/blog")
        self.assertIn("/en/", bytedance_source.path_prefixes)

        alibaba_source = companies["alibaba"].sources[0]
        self.assertEqual(alibaba_source.url, "https://www.alibabagroup.com/en-US/news-and-resource")
        self.assertEqual(alibaba_source.path_prefixes, ["/en-US/document-"])

        huawei_source = companies["huawei"].sources[0]
        self.assertEqual(huawei_source.label, "Huawei Media Center")
        self.assertEqual(huawei_source.url, "https://www.huawei.com/en/media-center")
        self.assertIn("/en/news/", huawei_source.path_prefixes)


if __name__ == "__main__":
    unittest.main()
