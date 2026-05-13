from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from .automation import generate_today_report, resolve_report_date
from .backfill import generate_backfill_reports
from .dry_run import run_dry_run
from .healthcheck import run_health_check
from .pipeline import generate_daily_report


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="tech-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="Generate daily dashboard")
    generate.add_argument("--date", required=True, help="Report date in YYYY-MM-DD format")
    generate.add_argument("--output-dir", default="", help="Optional site output directory")
    generate_today = subparsers.add_parser("generate-today", help="Generate today's dashboard in Asia/Shanghai")
    generate_today.add_argument("--output-dir", default="", help="Optional site output directory")
    subparsers.add_parser("health-check", help="Validate local configuration and runtime readiness")
    dry_run = subparsers.add_parser("dry-run", help="Validate the pipeline plan without fetching or writing output")
    dry_group = dry_run.add_mutually_exclusive_group(required=True)
    dry_group.add_argument("--date", help="Target report date in YYYY-MM-DD format")
    dry_group.add_argument("--today", action="store_true", help="Use today's date in Asia/Shanghai")
    backfill = subparsers.add_parser("backfill", help="Generate a range of daily dashboards")
    backfill.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
    backfill.add_argument("--days", required=True, type=int, help="Number of days to generate")
    backfill.add_argument("--output-dir", default="", help="Optional site output directory")
    return parser


def _print_report_summary(report) -> None:
    active_companies = ",".join(report.active_companies[:3]) or "-"
    print(
        f"report_date={report.date} total_entries={report.total_entries} "
        f"companies_covered={report.companies_covered} topic_count={len(report.topic_clusters)} "
        f"active_companies={active_companies}"
    )


def _print_health_check_summary(result: dict) -> None:
    print(
        f"ok={result['ok']} company_count={result['company_count']} "
        f"source_count={result['source_count']} llm_available={result['llm_available']} "
        f"summary_mode={result['summary_mode']} editorial_mode={result['editorial_mode']} "
        f"validation_issue_count={result.get('validation_issue_count', 0)} "
        f"latest_report_date={result.get('latest_report_date', '-') or '-'} "
        f"output_dir={result['output_dir']} "
        f"snapshot_path={result.get('snapshot_path', '-') or '-'}"
    )
    for note in result.get("notes", []):
        print(f"note={note}")
    for issue in result.get("validation_issues", [])[:5]:
        print(
            f"validation_issue severity={issue['severity']} code={issue['code']} "
            f"company={issue.get('company_slug', '-')}"
        )
    for diagnostic in result.get("source_diagnostics", [])[:5]:
        if diagnostic["severity"] != "ok":
            issues = ",".join(diagnostic["issues"]) or "-"
            print(
                f"source_diagnostic severity={diagnostic['severity']} "
                f"company={diagnostic['company_slug']} source={diagnostic['source_label']} issues={issues}"
            )
            if diagnostic.get("suggestion"):
                print(f"source_suggestion company={diagnostic['company_slug']} suggestion={diagnostic['suggestion']}")
    for diagnostic in result.get("recent_runtime_diagnostics", [])[:5]:
        issues = ",".join(diagnostic["issues"]) or "-"
        print(
            f"recent_runtime severity={diagnostic['severity']} "
            f"company={diagnostic['company_slug']} source={diagnostic['source_label']} issues={issues}"
        )
        if diagnostic.get("suggestion"):
            print(f"recent_runtime_suggestion company={diagnostic['company_slug']} suggestion={diagnostic['suggestion']}")
    for summary in result.get("high_priority_runtime_issues", [])[:5]:
        issues = ",".join(summary["issues"]) or "-"
        print(
            f"high_priority_runtime severity={summary['severity']} company={summary['company_slug']} "
            f"source={summary['source_label']} occurrences={summary['occurrence_count']} "
            f"latest_report_date={summary['latest_report_date']} issues={issues}"
        )
        if summary.get("suggestion"):
            print(f"high_priority_runtime_suggestion company={summary['company_slug']} suggestion={summary['suggestion']}")
    for recovered in result.get("recently_recovered_runtime_issues", [])[:5]:
        issues = ",".join(recovered["issues"]) or "-"
        print(
            f"recently_recovered_runtime company={recovered['company_slug']} "
            f"source={recovered['source_label']} recovered_report_date={recovered['recovered_report_date']} "
            f"last_issue_report_date={recovered['last_issue_report_date']} "
            f"occurrences={recovered['occurrence_count']} issues={issues}"
        )
    for summary in result.get("runtime_history_summary", [])[:5]:
        issues = ",".join(summary["issues"]) or "-"
        print(
            f"runtime_history severity={summary['severity']} company={summary['company_slug']} "
            f"source={summary['source_label']} occurrences={summary['occurrence_count']} "
            f"latest_report_date={summary['latest_report_date']} issues={issues}"
        )
        if summary.get("suggestion"):
            print(f"runtime_history_suggestion company={summary['company_slug']} suggestion={summary['suggestion']}")


def _print_dry_run_summary(result: dict) -> None:
    print(
        f"ok={result['ok']} report_date={result['report_date']} "
        f"company_count={result['company_count']} source_count={result['source_count']} "
        f"validation_issue_count={result['validation_issue_count']} "
        f"source_diagnostic_count={result.get('source_diagnostic_count', 0)}"
    )
    for issue in result.get("validation_issues", [])[:5]:
        print(
            f"validation_issue severity={issue['severity']} code={issue['code']} "
            f"company={issue.get('company_slug', '-')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "generate":
        output_dir = Path(args.output_dir) if args.output_dir else None
        report = generate_daily_report(args.date, output_dir=output_dir)
        _print_report_summary(report)
        return 0
    if args.command == "generate-today":
        output_dir = Path(args.output_dir) if args.output_dir else None
        report = generate_today_report(output_dir=output_dir)
        _print_report_summary(report)
        return 0
    if args.command == "health-check":
        result = run_health_check()
        _print_health_check_summary(result)
        return 0
    if args.command == "dry-run":
        report_date = resolve_report_date() if getattr(args, "today", False) else args.date
        result = run_dry_run(report_date)
        _print_dry_run_summary(result)
        return 0
    if args.command == "backfill":
        output_dir = Path(args.output_dir) if args.output_dir else None
        reports = generate_backfill_reports(args.end_date, args.days, output_dir=output_dir)
        if reports:
            _print_report_summary(reports[-1])
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
