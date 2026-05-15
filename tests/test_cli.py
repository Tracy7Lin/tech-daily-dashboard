import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.cli import build_parser, main
from tech_daily.models import DailyReport


class CliTests(unittest.TestCase):
    def test_build_parser_supports_generate_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["generate", "--date", "2026-05-10"])
        self.assertEqual(args.command, "generate")
        self.assertEqual(args.date, "2026-05-10")

    def test_build_parser_supports_generate_today_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["generate-today"])
        self.assertEqual(args.command, "generate-today")

    def test_build_parser_supports_health_check_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["health-check"])
        self.assertEqual(args.command, "health-check")

    def test_build_parser_supports_dry_run_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["dry-run", "--date", "2026-05-12"])
        self.assertEqual(args.command, "dry-run")
        self.assertEqual(args.date, "2026-05-12")

    def test_build_parser_supports_dry_run_today_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["dry-run", "--today"])
        self.assertEqual(args.command, "dry-run")
        self.assertTrue(args.today)

    def test_build_parser_supports_backfill_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["backfill", "--end-date", "2026-05-10", "--days", "7"])
        self.assertEqual(args.command, "backfill")
        self.assertEqual(args.end_date, "2026-05-10")
        self.assertEqual(args.days, 7)

    def test_build_parser_supports_chat_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["chat", "--date", "2026-05-15", "--question", "今天最值得关注什么？"])
        self.assertEqual(args.command, "chat")
        self.assertEqual(args.date, "2026-05-15")
        self.assertEqual(args.question, "今天最值得关注什么？")

    @patch("tech_daily.cli.generate_today_report")
    def test_main_prints_generation_summary_for_generate_today(self, mock_generate_today_report) -> None:
        mock_generate_today_report.return_value = DailyReport(
            date="2026-05-12",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=3,
            companies_covered=2,
            active_companies=["OpenAI", "Google"],
        )
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["generate-today"])

        self.assertEqual(exit_code, 0)
        self.assertIn("2026-05-12", output.getvalue())
        self.assertIn("total_entries=3", output.getvalue())
        self.assertIn("companies_covered=2", output.getvalue())

    @patch("tech_daily.cli.run_health_check")
    def test_main_prints_health_check_summary(self, mock_run_health_check) -> None:
        mock_run_health_check.return_value = {
            "ok": True,
            "company_count": 15,
            "source_count": 22,
            "llm_available": True,
            "summary_mode": "hybrid",
            "editorial_mode": "hybrid",
            "latest_report_date": "2026-05-13",
            "output_dir": "build/site",
            "snapshot_path": "build/data/health_snapshot.json",
            "ops_status_analysis": {
                "operator_brief": "当前优先处理 tesla；最近已恢复 alibaba。"
            },
            "notes": [],
            "runtime_history_summary": [
                {
                    "severity": "warning",
                    "company_slug": "xiaomi",
                    "source_label": "Xiaomi News",
                    "occurrence_count": 2,
                    "latest_report_date": "2026-05-13",
                    "issues": ["zero_fetched_entries"],
                }
            ],
            "high_priority_runtime_issues": [
                {
                    "severity": "error",
                    "company_slug": "tesla",
                    "source_label": "Tesla IR Press",
                    "occurrence_count": 3,
                    "latest_report_date": "2026-05-13",
                    "issues": ["http_403_blocked"],
                }
            ],
            "recently_recovered_runtime_issues": [
                {
                    "company_slug": "alibaba",
                    "company_name": "Alibaba",
                    "source_label": "Alibaba News and Resources",
                    "recovered_report_date": "2026-05-13",
                    "last_issue_report_date": "2026-05-12",
                    "occurrence_count": 2,
                    "issues": ["zero_fetched_entries"],
                }
            ],
        }
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["health-check"])

        self.assertEqual(exit_code, 0)
        self.assertIn("ok=True", output.getvalue())
        self.assertIn("company_count=15", output.getvalue())
        self.assertIn("latest_report_date=2026-05-13", output.getvalue())
        self.assertIn("snapshot_path=build/data/health_snapshot.json", output.getvalue())
        self.assertIn("operator_brief=当前优先处理 tesla；最近已恢复 alibaba。", output.getvalue())
        self.assertIn("high_priority_runtime severity=error company=tesla", output.getvalue())
        self.assertIn("recently_recovered_runtime company=alibaba", output.getvalue())
        self.assertIn("runtime_history severity=warning company=xiaomi", output.getvalue())

    @patch("tech_daily.cli.run_dry_run")
    def test_main_prints_dry_run_summary(self, mock_run_dry_run) -> None:
        mock_run_dry_run.return_value = {
            "ok": True,
            "report_date": "2026-05-12",
            "company_count": 15,
            "source_count": 20,
            "validation_issue_count": 0,
            "source_diagnostic_count": 20,
            "notes": [],
        }
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["dry-run", "--date", "2026-05-12"])

        self.assertEqual(exit_code, 0)
        self.assertIn("report_date=2026-05-12", output.getvalue())
        self.assertIn("validation_issue_count=0", output.getvalue())
        self.assertIn("source_diagnostic_count=20", output.getvalue())

    @patch("tech_daily.cli.run_chat_agent")
    def test_main_prints_chat_answer(self, mock_run_chat_agent) -> None:
        mock_run_chat_agent.return_value = {
            "answer": "今天最值得关注的是安全与治理。",
            "question_type": "daily_summary",
            "sources_used": ["report.json"],
            "follow_up_suggestions": ["Google 最近几天在做什么？"],
            "mode_used": "rule",
        }
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["chat", "--date", "2026-05-15", "--question", "今天最值得关注什么？"])

        self.assertEqual(exit_code, 0)
        self.assertIn("question_type=daily_summary", output.getvalue())
        self.assertIn("今天最值得关注的是安全与治理。", output.getvalue())


if __name__ == "__main__":
    unittest.main()
