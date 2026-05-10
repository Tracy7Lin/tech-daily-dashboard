from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from pathlib import Path

from .classifier import classify_entry
from .collector import collect_entries
from .config_loader import load_companies
from .models import CompanyReport, DailyReport, EnrichedEntry
from .quality import filter_high_signal_entries, matches_report_date
from .render import write_site
from .settings import DEFAULT_SETTINGS
from .topics import build_topic_clusters


def _sort_entries(entries: list[EnrichedEntry]) -> list[EnrichedEntry]:
    return sorted(entries, key=lambda item: (-item.importance, item.raw.company_name, item.raw.title))


def _build_company_reports(companies, entries: list[EnrichedEntry]) -> list[CompanyReport]:
    grouped: dict[str, list[EnrichedEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.raw.company_slug].append(entry)

    reports: list[CompanyReport] = []
    for company in companies:
        company_entries = _sort_entries(grouped.get(company.slug, []))
        reports.append(
            CompanyReport(
                company_slug=company.slug,
                company_name=company.name,
                entries=company_entries,
                has_updates=bool(company_entries),
            )
        )
    return reports


def _build_status_index(statuses):
    return {(status.company_slug, status.source_label): status for status in statuses}


def _augment_status_counts(statuses, raw_entries, dated_entries, final_entries):
    status_index = _build_status_index(statuses)
    dated_counts: dict[tuple[str, str], int] = defaultdict(int)
    final_counts: dict[tuple[str, str], int] = defaultdict(int)

    for entry in dated_entries:
        dated_counts[(entry.company_slug, entry.source_label)] += 1
    for entry in final_entries:
        final_counts[(entry.raw.company_slug, entry.raw.source_label)] += 1

    enriched_statuses = []
    for status in statuses:
        key = (status.company_slug, status.source_label)
        enriched_statuses.append(
            replace(
                status,
                date_matched_count=dated_counts.get(key, 0),
                final_included_count=final_counts.get(key, 0),
                message=(
                    f"{status.message};date_matched:{dated_counts.get(key, 0)};"
                    f"final_included:{final_counts.get(key, 0)}"
                ),
            )
        )
    return enriched_statuses


def _build_headline(total_entries: int, statuses) -> str:
    if total_entries:
        return ""

    healthy_sources = sum(1 for status in statuses if status.ok)
    any_date_matches = any(status.date_matched_count > 0 for status in statuses)
    any_final_included = any(status.final_included_count > 0 for status in statuses)

    if healthy_sources == 0:
        return "今天未生成日报内容，当前可用信源抓取全部失败。"
    if any_date_matches and not any_final_included:
        return "今天抓到了同日官方动态，但在质量约束下未保留可发布条目。"
    if not any_date_matches:
        return "今天未发现符合北京时间自然日范围的高价值官方动态。"
    return "今天没有抓到高价值官方动态，建议检查信源配置与抓取状态。"


def _build_daily_brief(topic_clusters, company_reports, total_entries: int) -> str:
    if not total_entries:
        return ""
    active_companies = [report.company_name for report in company_reports if report.has_updates][:3]
    lead = topic_clusters[0].title if topic_clusters else "官方动态"
    if len(topic_clusters) > 1:
        second = topic_clusters[1].title
        return f"今天共筛出 {total_entries} 条高价值动态，重点集中在 {lead} 与 {second}，活跃公司包括 {', '.join(active_companies)}。"
    return f"今天共筛出 {total_entries} 条高价值动态，重点集中在 {lead}，活跃公司包括 {', '.join(active_companies)}。"


def build_daily_report(date_str: str) -> DailyReport:
    companies = load_companies()
    raw_entries, statuses = collect_entries(companies)
    dated_entries = [
        entry
        for entry in raw_entries
        if entry.published_at and matches_report_date(entry.published_at, date_str)
    ]
    enriched_entries = _sort_entries(filter_high_signal_entries(classify_entry(entry) for entry in dated_entries))
    statuses = _augment_status_counts(statuses, raw_entries, dated_entries, enriched_entries)
    topic_clusters = build_topic_clusters(enriched_entries, DEFAULT_SETTINGS.max_topic_cards)
    company_reports = _build_company_reports(companies, enriched_entries)

    hottest_topics = [cluster.title for cluster in topic_clusters[:3]]
    if hottest_topics:
        headline = _build_daily_brief(topic_clusters, company_reports, len(enriched_entries))
    else:
        headline = _build_headline(len(enriched_entries), statuses)

    companies_covered = sum(1 for report in company_reports if report.has_updates)
    return DailyReport(
        date=date_str,
        headline=headline,
        hottest_topics=hottest_topics,
        total_entries=len(enriched_entries),
        companies_covered=companies_covered,
        active_companies=[report.company_name for report in company_reports if report.has_updates],
        topic_clusters=topic_clusters,
        company_reports=company_reports,
        source_statuses=statuses,
    )


def generate_daily_report(date_str: str, output_dir: Path | None = None) -> DailyReport:
    report = build_daily_report(date_str)
    destination = output_dir or Path(DEFAULT_SETTINGS.site_output_dir)
    write_site(report, destination)
    return report
