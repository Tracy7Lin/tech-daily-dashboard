import unittest
from unittest.mock import Mock

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import RawEntry
from tech_daily.summarizer import Summarizer, build_summary


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
        self.assertIn("OpenAI 围绕“launches GPT-5.5 Instant for ChatGPT”", summary)
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
        self.assertIn("真实业务场景", summary)

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

    def test_build_summary_strips_html_and_mentions_rollout_when_relevant(self) -> None:
        entry = RawEntry(
            company_slug="google",
            company_name="Google",
            source_label="Google Blog",
            title="Google Health Coach is becoming globally available",
            url="https://example.com",
            summary="<img src=\"hero.png\">Google Health Coach, now available globally, provides personalized insights on workouts, sleep and recovery.",
        )
        summary = build_summary(entry, ["product", "consumer"], "product")
        self.assertNotIn("<img", summary)
        self.assertIn("面向更大范围用户", summary)
        self.assertNotIn("rollout", summary)

    def test_build_summary_uses_customer_case_wording(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="Parloa builds service agents customers want to talk to",
            url="https://example.com",
            summary="Parloa leverages OpenAI models to deploy reliable real-time customer service agents for enterprises.",
        )
        summary = build_summary(entry, ["ai", "enterprise", "customer", "model"], "technology")
        self.assertIn("客户案例", summary)
        self.assertIn("真实业务场景", summary)

    def test_build_summary_does_not_treat_brand_title_performance_as_model_gain(self) -> None:
        entry = RawEntry(
            company_slug="google",
            company_name="Google",
            source_label="Google Blog",
            title="Pre-order Stephen Curry’s special edition Fitbit Air",
            url="https://example.com",
            summary="NBA champion and Google Performance Advisor, Stephen Curry, has partnered with Fitbit to debut a special edition band.",
        )
        summary = build_summary(entry, ["product"], "product")
        self.assertNotIn("模型能力、推理表现或工作流效果的提升", summary)
        self.assertIn("产品能力是否真正落地到用户或开发者场景", summary)

    def test_summarizer_hybrid_falls_back_to_rule_when_llm_unavailable(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI launches GPT-5.5 Instant for ChatGPT",
            url="https://example.com",
            summary="Smarter, clearer and more personalized responses for everyday use.",
        )
        rule = Mock()
        rule.summarize.return_value = "rule summary"
        llm = Mock()
        llm.is_available.return_value = False

        summarizer = Summarizer(mode="hybrid", fallback_enabled=True, rule_summarizer=rule, llm_summarizer=llm)
        result = summarizer.summarize(entry, ["ai", "model"], "product")
        self.assertEqual(result, "rule summary")
        rule.summarize.assert_called_once()

    def test_summarizer_hybrid_falls_back_to_rule_on_llm_error(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI launches GPT-5.5 Instant for ChatGPT",
            url="https://example.com",
            summary="Smarter, clearer and more personalized responses for everyday use.",
        )
        rule = Mock()
        rule.summarize.return_value = "rule summary"
        llm = Mock()
        llm.is_available.return_value = True
        llm.summarize.side_effect = RuntimeError("boom")

        summarizer = Summarizer(mode="hybrid", fallback_enabled=True, rule_summarizer=rule, llm_summarizer=llm)
        result = summarizer.summarize(entry, ["ai", "model"], "product")
        self.assertEqual(result, "rule summary")

    def test_summarizer_rule_mode_still_returns_text_when_delegating(self) -> None:
        entry = RawEntry(
            company_slug="openai",
            company_name="OpenAI",
            source_label="OpenAI News",
            title="OpenAI launches GPT-5.5 Instant for ChatGPT",
            url="https://example.com",
            summary="Smarter, clearer and more personalized responses for everyday use.",
        )
        summarizer = Summarizer(mode="rule")

        result = summarizer.summarize(entry, ["ai", "model"], "product")

        self.assertIsInstance(result, str)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
