from __future__ import annotations

import html
import json
import re
from pathlib import Path
from string import Template

from .archive import load_report_snapshots
from .models import CompanyReport, DailyReport, EnrichedEntry, TopicCluster
from .paths import TEMPLATES_DIR


def _load_template(name: str) -> Template:
    return Template((TEMPLATES_DIR / name).read_text(encoding="utf-8"))


def _strip_html(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text).split()).strip()


def _truncate(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "item"


def _format_published_at(value: str) -> str:
    if not value:
        return "未知"
    if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
        return value.replace("T", " ").replace("Z", " UTC")
    return value


def _entry_supplement(entry: EnrichedEntry) -> str:
    cleaned = _strip_html(entry.raw.summary)
    if cleaned:
        return _truncate(cleaned, 180)
    return "暂无原文补充说明。"


def _entry_meta(entry: EnrichedEntry) -> str:
    return (
        f"来源：{html.escape(entry.raw.source_label)} | "
        f"发布时间：{html.escape(_format_published_at(entry.raw.published_at))} | "
        f"分类：{html.escape(entry.category)} | "
        f"重要度：{entry.importance} | "
        f"对比角度：{html.escape(entry.comparison_angle)} | "
        f"标签：{html.escape(', '.join(entry.tags))}"
    )


def _select_highlights(report: DailyReport, limit: int) -> list[EnrichedEntry]:
    entries = [entry for company in report.company_reports for entry in company.entries]
    entries.sort(key=lambda item: (-item.importance, item.raw.company_name, item.raw.title))
    return entries[:limit]


def _render_entry_detail(entry: EnrichedEntry) -> str:
    tag_badges = "".join(f"<span class='tag-chip'>{html.escape(tag)}</span>" for tag in entry.tags[:4])
    return (
        f"<div class='modal-detail-header'><p class='eyebrow'>{html.escape(entry.raw.company_name)}</p><span class='importance-pill'>P{entry.importance}</span></div>"
        f"<h3>{html.escape(entry.raw.title)}</h3>"
        f"<p class='section-copy'>{html.escape(entry.summary_cn)}</p>"
        f"<p class='meta meta-line'>{_entry_meta(entry)}</p>"
        f"<div class='tag-row'>{tag_badges}</div>"
        f"<p class='supplement'><strong>原文补充：</strong>{html.escape(_entry_supplement(entry))}</p>"
        f"<p><a class='inline-link' href='{html.escape(entry.raw.url)}'>查看原文</a></p>"
    )


def _render_highlight_card(entry: EnrichedEntry, modal_prefix: str = "highlight") -> str:
    modal_id = f"{modal_prefix}-{entry.raw.company_slug}-{_slugify(entry.raw.title)}"
    summary = _truncate(entry.summary_cn, 92)
    return (
        "<article class='card summary-card highlight-card'>"
        f"<button class='card-trigger' type='button' data-modal-trigger='{html.escape(modal_id)}'>"
        f"<div class='card-topline'><p class='eyebrow'>{html.escape(entry.raw.company_name)}</p><span class='importance-pill'>P{entry.importance}</span></div>"
        f"<h3>{html.escape(entry.raw.title)}</h3>"
        f"<p class='section-copy'>{html.escape(summary)}</p>"
        f"<p class='meta meta-line'>{html.escape(_format_published_at(entry.raw.published_at))} · {html.escape(entry.raw.source_label)}</p>"
        "<span class='trigger-hint'>点击查看完整内容</span>"
        "</button>"
        f"<template id='{html.escape(modal_id)}'>{_render_entry_detail(entry)}</template>"
        "</article>"
    )


def _render_highlights(report: DailyReport, limit: int) -> str:
    highlights = _select_highlights(report, limit)
    if not highlights:
        return "<p class='empty'>今日暂无重点观察</p>"
    return "".join(_render_highlight_card(entry) for entry in highlights)


def _render_topic_card(cluster: TopicCluster, modal_prefix: str = "topic") -> str:
    companies = sorted({entry.raw.company_name for entry in cluster.entries})
    modal_id = f"{modal_prefix}-{cluster.topic_id}"
    representative_entries = "".join(
        "<li class='topic-event'>"
        f"<div class='topic-event-title'><strong>{html.escape(entry.raw.company_name)}</strong><a class='inline-link' href=\"{html.escape(entry.raw.url)}\">{html.escape(entry.raw.title)}</a></div>"
        f"<p class='section-copy'>{html.escape(entry.summary_cn)}</p>"
        "</li>"
        for entry in cluster.entries[:3]
    )
    summary = _truncate(cluster.summary, 104)
    return (
        "<section class='card topic-card summary-card'>"
        f"<button class='card-trigger' type='button' data-modal-trigger='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(cluster.title)}</h3>"
        f"<p class='meta meta-line'>涉及公司：{len(companies)} | 条目数：{len(cluster.entries)} | 公司：{html.escape(', '.join(companies))}</p>"
        f"<p class='section-copy'>{html.escape(summary)}</p>"
        f"<p class='topic-note'><strong>趋势判断：</strong>{html.escape(_truncate(cluster.trend, 96))}</p>"
        "<span class='trigger-hint'>点击展开完整主题分析</span>"
        "</button>"
        f"<template id='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(cluster.title)}</h3>"
        f"<p class='meta meta-line'>涉及公司：{len(companies)} | 条目数：{len(cluster.entries)} | 公司：{html.escape(', '.join(companies))}</p>"
        f"<p class='section-copy'>{html.escape(cluster.summary)}</p>"
        f"<p class='topic-note'><strong>差异对比：</strong>{html.escape(cluster.comparison)}</p>"
        f"<p class='topic-note'><strong>趋势判断：</strong>{html.escape(cluster.trend)}</p>"
        "<p class='topic-list-label'><strong>代表事件：</strong></p>"
        f"<ul class='topic-event-list'>{representative_entries}</ul>"
        "</template>"
        "</section>"
    )


def _render_company_report(report: CompanyReport, modal_prefix: str = "company") -> str:
    if not report.entries:
        body = "<p class='empty'>今日无有效动态</p>"
    else:
        items = []
        for entry in report.entries:
            items.append(
                "<article class='entry'>"
                f"<h4>{html.escape(entry.raw.title)}</h4>"
                f"<p class='section-copy'>{html.escape(entry.summary_cn)}</p>"
                f"<p class='meta meta-line'>{_entry_meta(entry)}</p>"
                f"<p class='supplement'><strong>原文补充：</strong>{html.escape(_entry_supplement(entry))}</p>"
                f"<p><a class='inline-link' href='{html.escape(entry.raw.url)}'>查看原文</a></p>"
                "</article>"
            )
        body = "".join(items)
    if not report.entries:
        return (
            "<section class='card company-card summary-card'>"
            f"<h3>{html.escape(report.company_name)}</h3>"
            f"{body}"
            "</section>"
        )
    modal_id = f"{modal_prefix}-{report.company_slug}"
    lead = report.entries[0]
    summary = _truncate(lead.summary_cn, 96)
    return (
        "<section class='card company-card summary-card'>"
        f"<button class='card-trigger' type='button' data-modal-trigger='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(report.company_name)}</h3>"
        f"<p class='meta'>当日动态：{len(report.entries)} 条</p>"
        f"<p class='section-copy'>{html.escape(summary)}</p>"
        f"<p class='meta meta-line'>最新来源：{html.escape(lead.raw.source_label)} | 发布时间：{html.escape(_format_published_at(lead.raw.published_at))}</p>"
        "<span class='trigger-hint'>点击查看公司完整动态</span>"
        "</button>"
        f"<template id='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(report.company_name)}</h3>"
        f"{body}"
        "</template>"
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
        highlights=_render_highlights(report, limit=5),
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
        highlights=_render_highlights(report, limit=8),
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
