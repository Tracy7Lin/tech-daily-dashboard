import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import RawEntry
from tech_daily.summarizer import build_summary


class SummarizerTests(unittest.TestCase):
    def test_build_summary_reads_like_chinese_brief(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="OpenAI launches GPT-5.5 Instant for ChatGPT",
            url="https://example.com",
            summary="Smarter, clearer and more personalized responses for everyday use.",
        )
        summary = build_summary(entry, ["ai", "model", "consumer"], "product")
        self.assertIn("OpenAI 围绕“launches GPT-5.5 Instant for ChatGPT”发布了一项产品相关的更新", summary)
        self.assertIn("模型能力升级", summary)
        self.assertIn("重点在于", summary)

    def test_build_summary_uses_customer_focus_when_relevant(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="Uber uses OpenAI to help people earn smarter and book faster",
            url="https://example.com",
            summary="The deployment focuses on real business workflows and customer-facing speed.",
        )
        summary = build_summary(entry, ["ai", "customer"], "technology")
        self.assertIn("客户落地与采用进展", summary)
        self.assertIn("真实业务与工作流", summary)

    def test_build_summary_prioritizes_safety_over_model_when_both_exist(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="news",
            title="Trusted access with GPT-5.5",
            url="https://example.com",
            summary="New safeguards and security workflows for enterprise users.",
        )
        summary = build_summary(entry, ["ai", "model", "safety"], "technology")
        self.assertIn("安全、治理与可信使用", summary)


if __name__ == "__main__":
    unittest.main()
