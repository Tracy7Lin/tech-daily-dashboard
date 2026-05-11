import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.settings import load_settings


class SettingsTests(unittest.TestCase):
    def test_load_settings_reads_llm_generation_modes_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TECH_DAILY_SUMMARY_MODE": "llm",
                "TECH_DAILY_EDITORIAL_MODE": "hybrid",
                "TECH_DAILY_LLM_MODEL": "gpt-test",
                "TECH_DAILY_LLM_API_URL": "https://example.com/v1/responses",
                "TECH_DAILY_LLM_API_KEY": "secret",
                "TECH_DAILY_LLM_TIMEOUT_SECONDS": "12",
            },
            clear=False,
        ):
            settings = load_settings()
        self.assertEqual(settings.summary_mode, "llm")
        self.assertEqual(settings.editorial_mode, "hybrid")
        self.assertEqual(settings.llm_model, "gpt-test")
        self.assertEqual(settings.llm_timeout_seconds, 12)

    def test_load_settings_normalizes_invalid_modes_to_hybrid(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TECH_DAILY_SUMMARY_MODE": "unexpected",
                "TECH_DAILY_EDITORIAL_MODE": "broken",
            },
            clear=False,
        ):
            settings = load_settings()
        self.assertEqual(settings.summary_mode, "hybrid")
        self.assertEqual(settings.editorial_mode, "hybrid")

    def test_load_settings_reads_defaults_from_dotenv_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "TECH_DAILY_SUMMARY_MODE=hybrid",
                        "TECH_DAILY_EDITORIAL_MODE=llm",
                        "TECH_DAILY_LLM_MODEL=deepseekv4",
                        "TECH_DAILY_LLM_API_URL=https://example.com/v1/responses",
                        "TECH_DAILY_LLM_API_KEY=dotenv-secret",
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                settings = load_settings(env_path=env_path)

        self.assertEqual(settings.editorial_mode, "llm")
        self.assertEqual(settings.llm_model, "deepseekv4")
        self.assertEqual(settings.llm_api_key, "dotenv-secret")

    def test_load_settings_prefers_environment_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "TECH_DAILY_LLM_MODEL=deepseekv4",
                        "TECH_DAILY_LLM_API_KEY=dotenv-secret",
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "TECH_DAILY_LLM_MODEL": "env-override-model",
                    "TECH_DAILY_LLM_API_KEY": "env-secret",
                },
                clear=True,
            ):
                settings = load_settings(env_path=env_path)

        self.assertEqual(settings.llm_model, "env-override-model")
        self.assertEqual(settings.llm_api_key, "env-secret")


if __name__ == "__main__":
    unittest.main()
