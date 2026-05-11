import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.llm_summarizer import LLMSummarizer
from tech_daily.models import RawEntry


class _StubClient:
    def __init__(self, payload):
        self.payload = payload

    def is_available(self) -> bool:
        return True

    def generate_json(self, **kwargs):
        return self.payload


class LLMSummarizerTests(unittest.TestCase):
    def test_summarize_removes_title_repetition_and_meta_phrasing(self) -> None:
        summarizer = LLMSummarizer(
            _StubClient(
                {
                    "summary_cn": (
                        "OpenAI launches GPT-5.5 Instant for ChatGPT。"
                        "根据提供信息，OpenAI launches GPT-5.5 Instant for ChatGPT。"
                        "这次更新把更清晰、更个性化的回复直接推向日常使用场景，值得关注的是它开始影响普通用户的实际体验。"
                    )
                }
            )
        )
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI launches GPT-5.5 Instant for ChatGPT",
            url="https://example.com",
            summary="Smarter, clearer and more personalized responses for everyday use.",
        )

        summary = summarizer.summarize(entry, ["ai", "model", "consumer"], "product")
        self.assertNotIn("根据提供信息", summary)
        self.assertEqual(summary.count("OpenAI launches GPT-5.5 Instant for ChatGPT"), 0)
        self.assertIn("值得关注", summary)

    def test_summarize_rejects_empty_or_low_signal_output(self) -> None:
        summarizer = LLMSummarizer(_StubClient({"summary_cn": "可以看出，这是一次更新。"}))
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI launches GPT-5.5 Instant for ChatGPT",
            url="https://example.com",
            summary="Smarter, clearer and more personalized responses for everyday use.",
        )

        with self.assertRaises(ValueError):
            summarizer.summarize(entry, ["ai", "model", "consumer"], "product")

    def test_summarize_rejects_speculative_claims(self) -> None:
        summarizer = LLMSummarizer(
            _StubClient(
                {
                    "summary_cn": "谷歌将AI升级后的Google Finance服务扩展到欧洲，支持全本地语言。此举可能重塑欧洲用户的投资决策方式。"
                }
            )
        )
        entry = RawEntry(
            company_slug="google",
            company_name="Google",
            source_label="Google Blog",
            title="The new AI-powered Google Finance is expanding to Europe.",
            url="https://example.com",
            summary="AI-powered Google Finance expands in Europe with local language support.",
        )

        with self.assertRaises(ValueError):
            summarizer.summarize(entry, ["ai", "product"], "product")


if __name__ == "__main__":
    unittest.main()
