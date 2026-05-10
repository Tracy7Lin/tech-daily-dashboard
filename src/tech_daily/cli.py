from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from .backfill import generate_backfill_reports
from .pipeline import generate_daily_report


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="tech-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="Generate daily dashboard")
    generate.add_argument("--date", required=True, help="Report date in YYYY-MM-DD format")
    generate.add_argument("--output-dir", default="", help="Optional site output directory")
    backfill = subparsers.add_parser("backfill", help="Generate a range of daily dashboards")
    backfill.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
    backfill.add_argument("--days", required=True, type=int, help="Number of days to generate")
    backfill.add_argument("--output-dir", default="", help="Optional site output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "generate":
        output_dir = Path(args.output_dir) if args.output_dir else None
        generate_daily_report(args.date, output_dir=output_dir)
        return 0
    if args.command == "backfill":
        output_dir = Path(args.output_dir) if args.output_dir else None
        generate_backfill_reports(args.end_date, args.days, output_dir=output_dir)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
