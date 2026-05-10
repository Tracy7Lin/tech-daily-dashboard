from __future__ import annotations

import html
import json
from pathlib import Path
from string import Template

from .archive import load_report_snapshots
from .models import CompanyReport, DailyReport, TopicCluster
from .paths import TEMPLATES_DIR


def _load_template(name: str) -> Template:
    return Template((TEMPLATES_DIR / name).read_text(encoding="utf-8"))


def _render_topic_card(cluster: TopicCluster) -> str:
    links = "".join(
        f'<li><a href="{html.escape(entry.raw.url)}">{html.escape(entry.raw.company_name)}: {html.escape(entry.raw.title)}</a></li>'
        for entry in cluster.entries[:5]
    )
    return (
        "<section class='card topic-card'>"
        f"<h3>{html.escape(cluster.title)}</h3>"
        f"<p>{html.escape(cluster.summary)}</p>"
        f"<p><strong>差异对比：</strong>{html.escape(cluster.comparison)}</p>"
        f"<p><strong>趋势判断：</strong>{html.escape(cluster.trend)}</p>"
        f"<ul>{links}</ul>"
        "</section>"
    )


def _render_company_report(report: CompanyReport) -> str:
    if not report.entries:
        body = "<p class='empty'>今日无有效动态</p>"
    else:
        items = []
        for entry in report.entries:
            items.append(
                "<article class='entry'>"
                f"<h4>{html.escape(entry.raw.title)}</h4>"
                f"<p>{html.escape(entry.summary_cn)}</p>"
                f"<p class='meta'>标签：{html.escape(', '.join(entry.tags))} | 重要度：{entry.importance}</p>"
                f"<p><a href='{html.escape(entry.raw.url)}'>查看原文</a></p>"
                "</article>"
            )
        body = "".join(items)
    return (
        "<section class='card company-card'>"
        f"<h3>{html.escape(report.company_name)}</h3>"
        f"{body}"
        "</section>"
    )


def render_index(report: DailyReport) -> str:
    template = _load_template("index.html")
    topic_cards = "".join(_render_topic_card(cluster) for cluster in report.topic_clusters)
    company_cards = "".join(_render_company_report(company) for company in report.company_reports)
    return template.substitute(
        date=html.escape(report.date),
        headline=html.escape(report.headline),
        total_entries=str(report.total_entries),
        companies_covered=str(report.companies_covered),
        hottest_topics=html.escape(" / ".join(report.hottest_topics) or "暂无"),
        topic_cards=topic_cards,
        company_cards=company_cards,
    )


def render_daily(report: DailyReport) -> str:
    template = _load_template("daily.html")
    statuses = "".join(
        f"<li>{html.escape(status.company_name)} - {html.escape(status.source_label)} - {html.escape(status.message)}</li>"
        for status in report.source_statuses
    )
    return template.substitute(
        date=html.escape(report.date),
        headline=html.escape(report.headline),
        topic_cards="".join(_render_topic_card(cluster) for cluster in report.topic_clusters),
        company_cards="".join(_render_company_report(company) for company in report.company_reports),
        statuses=statuses or "<li>无</li>",
    )


def render_archive(reports: list[DailyReport]) -> str:
    template = _load_template("archive.html")
    items = []
    for report in reports:
        items.append(
            "<li>"
            f"<a href='./{html.escape(report.date)}/index.html'>{html.escape(report.date)}</a>"
            f" - {html.escape(report.headline)}"
            "</li>"
        )
    return template.substitute(archive_items="".join(items) or "<li>暂无归档</li>")


def write_site(report: DailyReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    daily_dir = output_dir / report.date
    daily_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "index.html").write_text(render_index(report), encoding="utf-8")
    (daily_dir / "index.html").write_text(render_daily(report), encoding="utf-8")
    (daily_dir / "report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    archived_reports = load_report_snapshots(output_dir)
    (output_dir / "archive.html").write_text(render_archive(archived_reports), encoding="utf-8")
