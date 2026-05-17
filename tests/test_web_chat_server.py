import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.web_chat_server import handle_chat_request, runtime_health_payload


class WebChatServerTests(unittest.TestCase):
    def test_runtime_health_payload_reports_llm_availability(self) -> None:
        payload = runtime_health_payload(site_dir=Path("build/site"), llm_available=True, mode="hybrid")

        self.assertTrue(payload["ok"])
        self.assertTrue(payload["llm_available"])
        self.assertEqual(payload["mode"], "hybrid")
        self.assertIn("runtime_hint", payload)

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
                    "evidence_items": [{"source": "theme_dossier.json", "label": "专题档案", "detail": "当前主专题是安全与治理。", "reference": "theme_dossier.json · 专题档案"}],
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
        self.assertEqual(payload["evidence_items"][0]["source"], "theme_dossier.json")
        self.assertEqual(payload["evidence_items"][0]["reference"], "theme_dossier.json · 专题档案")

    def test_handle_chat_request_passes_message_history(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir)
            with patch("tech_daily.web_chat_server.run_chat_agent") as mock_run_chat_agent:
                mock_run_chat_agent.return_value = {
                    "answer": "Google 在这个专题里更偏向产品功能约束。",
                    "question_type": "company_position",
                    "sources_used": ["theme_dossier.json"],
                    "follow_up_suggestions": [],
                    "mode_used": "rule",
                }
                status_code, _payload = handle_chat_request(
                    site_dir,
                    {
                        "date": "2026-05-16",
                        "question": "那 Google 呢？",
                        "messages": [
                            {
                                "role": "assistant",
                                "question_type": "dossier_summary",
                                "resolved_theme": "安全与治理",
                                "resolved_company": "",
                            }
                        ],
                    },
                )

        self.assertEqual(status_code, 200)
        self.assertEqual(mock_run_chat_agent.call_args.kwargs["history"][0]["question_type"], "dossier_summary")


if __name__ == "__main__":
    unittest.main()
