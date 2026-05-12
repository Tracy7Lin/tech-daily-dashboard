import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.cli import build_parser


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

    def test_build_parser_supports_backfill_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["backfill", "--end-date", "2026-05-10", "--days", "7"])
        self.assertEqual(args.command, "backfill")
        self.assertEqual(args.end_date, "2026-05-10")
        self.assertEqual(args.days, 7)


if __name__ == "__main__":
    unittest.main()
