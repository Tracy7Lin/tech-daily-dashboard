import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.llm_client import LLMClient


class LLMClientTests(unittest.TestCase):
    def test_generate_json_parses_output_text_from_response_payload(self) -> None:
        captured = {}

        def transport(url, headers, body, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = body
            captured["timeout"] = timeout
            return {
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary_cn":"OpenAI 发布了模型与能力更新。"}',
                            }
                        ]
                    }
                ]
            }

        client = LLMClient(
            api_url="https://example.com/v1/responses",
            api_key="secret",
            model="gpt-test",
            timeout_seconds=9,
            transport=transport,
        )
        result = client.generate_json(
            instructions="instr",
            input_text="input",
            schema_name="summary_payload",
            schema={"type": "object"},
        )
        self.assertEqual(result["summary_cn"], "OpenAI 发布了模型与能力更新。")
        self.assertEqual(captured["url"], "https://example.com/v1/responses")
        self.assertEqual(captured["timeout"], 9)

    def test_generate_json_supports_chat_completions_base_url(self) -> None:
        captured = {}

        def transport(url, headers, body, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = body
            captured["timeout"] = timeout
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary_cn":"这次更新把能力推向更具体的用户场景。"}'
                        }
                    }
                ]
            }

        client = LLMClient(
            api_url="https://api.deepseek.com",
            api_key="secret",
            model="deepseek-v4-flash",
            timeout_seconds=11,
            transport=transport,
        )
        result = client.generate_json(
            instructions="instr",
            input_text="input",
            schema_name="summary_payload",
            schema={"type": "object"},
        )
        self.assertEqual(result["summary_cn"], "这次更新把能力推向更具体的用户场景。")
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertIn("messages", captured["body"])
        self.assertNotIn("input", captured["body"])

    def test_generate_json_expands_v1_base_url_to_responses_endpoint(self) -> None:
        captured = {}

        def transport(url, headers, body, timeout):
            captured["url"] = url
            return {
                "output_text": '{"ok": true}'
            }

        client = LLMClient(
            api_url="https://api.openai.com/v1",
            api_key="secret",
            model="gpt-test",
            timeout_seconds=9,
            transport=transport,
        )
        result = client.generate_json(
            instructions="instr",
            input_text="input",
            schema_name="healthcheck",
            schema={"type": "object"},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(captured["url"], "https://api.openai.com/v1/responses")


if __name__ == "__main__":
    unittest.main()
