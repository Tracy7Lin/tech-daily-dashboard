import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.web_chat_server import handle_chat_request


class WebChatServerTests(unittest.TestCase):
    def test_handle_chat_request_requires_date_and_question(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir)
            status_code, payload = handle_chat_request(site_dir, {"date": "", "question": ""})

        self.assertEqual(status_code, 400)
        self.assertIn("error", payload)

    def test_handle_chat_request_returns_chat_answer_payload(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir)
            with patch("tech_daily.web_chat_server.run_chat_agent") as mock_run_chat_agent:
                mock_run_chat_agent.return_value = {
                    "answer": "今天最值得关注的是安全与治理。",
                    "question_type": "daily_summary",
                    "sources_used": ["report.json"],
                    "follow_up_suggestions": ["这个主专题现在怎么理解？"],
                    "mode_used": "llm",
                }
                status_code, payload = handle_chat_request(
                    site_dir,
                    {"date": "2026-05-16", "question": "今天最值得关注什么？"},
                )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload["question_type"], "daily_summary")
        self.assertEqual(payload["mode_used"], "llm")
        self.assertIn("安全与治理", payload["answer"])


if __name__ == "__main__":
    unittest.main()
