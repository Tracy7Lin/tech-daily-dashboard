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


if __name__ == "__main__":
    unittest.main()
