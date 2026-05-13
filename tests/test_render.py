import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import CompanyReport, DailyReport, EnrichedEntry, RawEntry, SourceStatus, TopicCluster
from tech_daily.render import render_daily, render_index, write_site


def _entry(
    company_slug: str,
    company_name: str,
    title: str,
    summary_cn: str,
    *,
    source_label: str = "News",
    summary: str = "",
    published_at: str = "2026-05-10T12:00:00Z",
    tags: list[str] | None = None,
    category: str = "product",
    importance: int = 4,
    comparison_angle: str = "product",
) -> EnrichedEntry:
    return EnrichedEntry(
        raw=RawEntry(
            company_slug=company_slug,
            company_name=company_name,
            source_label=source_label,
            title=title,
            url=f"https://example.com/{company_slug}/{title.replace(' ', '-').lower()}",
            summary=summary,
            published_at=published_at,
        ),
        tags=tags or ["product"],
        category=category,
        importance=importance,
        summary_cn=summary_cn,
        comparison_angle=comparison_angle,
    )


class RenderTests(unittest.TestCase):
    def test_render_index_contains_topic_section(self) -> None:
        entry = _entry(
            "openai",
            "OpenAI",
            "Advancing voice intelligence with new models in the API",
            "OpenAI 发布了模型与能力更新。",
            summary="<p>New voice models for the API with reasoning and translation support.</p>",
            tags=["ai", "model", "developer"],
            category="technology",
            importance=5,
            comparison_angle="ai、model、developer",
        )
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=["AI Agent"],
            total_entries=1,
            companies_covered=1,
            topic_clusters=[
                TopicCluster(
                    topic_id="ai-agent",
                    title="AI Agent",
                    summary="summary",
                    comparison="comparison",
                    trend="trend",
                    entries=[entry],
                )
            ],
            company_reports=[CompanyReport(company_slug="openai", company_name="OpenAI", entries=[entry], has_updates=True)],
            source_statuses=[],
        )
        html = render_index(report)
        self.assertIn("site-shell", html)
        self.assertIn("hero-stats", html)
        self.assertIn("signal-rail", html)
        self.assertIn("signal-card", html)
        self.assertIn("metric-pill", html)
        self.assertIn("modal-root", html)
        self.assertIn("data-modal-trigger", html)
        self.assertIn("openModal", html)
        self.assertIn("topic-stat-chip", html)
        self.assertIn("主题对比", html)
        self.assertIn("重点观察", html)
        self.assertIn("涉及公司", html)
        self.assertIn("代表事件", html)
        self.assertIn("来源：News", html)
        self.assertIn("分类：technology", html)
        self.assertIn("对比角度：ai、model、developer", html)
        self.assertIn("New voice models for the API", html)

    def test_render_daily_includes_highlights_and_enriched_company_metadata(self) -> None:
        entry = _entry(
            "google",
            "Google",
            "Google Health Coach is becoming globally available",
            "Google 发布了一项产品相关的更新。",
            source_label="Google Blog",
            summary="<img src='hero.png'>Google Health Coach, now available globally, provides personalized insights on workouts, sleep and recovery.",
            tags=["product", "consumer"],
            category="product",
            importance=4,
            comparison_angle="product、consumer",
        )
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=["新产品发布"],
            total_entries=1,
            companies_covered=1,
            topic_clusters=[
                TopicCluster(
                    topic_id="product-launch",
                    title="新产品发布",
                    summary="summary",
                    comparison="comparison",
                    trend="trend",
                    entries=[entry],
                )
            ],
            company_reports=[CompanyReport(company_slug="google", company_name="Google", entries=[entry], has_updates=True)],
            source_statuses=[],
        )
        html = render_daily(report)
        self.assertIn("site-shell", html)
        self.assertIn("page-header", html)
        self.assertIn("status-list", html)
        self.assertIn("modal-root", html)
        self.assertIn("data-modal-trigger", html)
        self.assertIn("modal-panel", html)
        self.assertIn("modal-summary-grid", html)
        self.assertIn("summary-block", html)
        self.assertIn("重点观察", html)
        self.assertIn("原文补充", html)
        self.assertIn("Google Blog", html)
        self.assertIn("发布时间", html)
        self.assertIn("分类：product", html)
        self.assertIn("对比角度：product、consumer", html)
        self.assertIn("Google Health Coach, now available globally", html)
        self.assertNotIn("<img", html)

    def test_render_company_report_empty_state_uses_padded_card(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[CompanyReport(company_slug="apple", company_name="Apple", entries=[], has_updates=False)],
            source_statuses=[],
        )
        html = render_index(report)
        self.assertIn("<section class='card company-card'>", html)
        self.assertIn("Apple", html)
        self.assertIn("今日无有效动态", html)
        self.assertNotIn("<section class='card company-card summary-card'>", html)

    def test_render_company_report_empty_state_surfaces_unstable_source_reason(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[CompanyReport(company_slug="tesla", company_name="Tesla", entries=[], has_updates=False)],
            source_statuses=[
                SourceStatus(
                    company_slug="tesla",
                    company_name="Tesla",
                    source_label="Tesla IR Press",
                    source_url="https://ir.tesla.com/press?view=all",
                    ok=False,
                    message="http_error:403;kept:0;date_matched:0;final_included:0",
                )
            ],
        )
        html = render_index(report)
        self.assertIn("信源暂未稳定", html)
        self.assertIn("Tesla 官方新闻入口当前持续拒绝抓取请求", html)
        self.assertIn("Tesla IR Press", html)

    def test_render_company_report_empty_state_surfaces_zero_fetched_placeholder(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[CompanyReport(company_slug="xiaomi", company_name="Xiaomi", entries=[], has_updates=False)],
            source_statuses=[
                SourceStatus(
                    company_slug="xiaomi",
                    company_name="Xiaomi",
                    source_label="Xiaomi News",
                    source_url="https://www.mi.com/global/discover/newsroom",
                    ok=True,
                    message="ok;fetched:0;kept:0;date_matched:0;final_included:0",
                    fetched_count=0,
                    kept_count=0,
                )
            ],
        )
        html = render_daily(report)
        self.assertIn("信源暂未稳定", html)
        self.assertIn("Xiaomi Global Discover 当前以动态渲染为主", html)
        self.assertIn("Xiaomi News", html)

    def test_render_preserves_rfc_weekday_and_timezone_in_published_time(self) -> None:
        entry = _entry(
            "openai",
            "OpenAI",
            "Introducing Trusted Contact in ChatGPT",
            "OpenAI 更新了安全与治理相关能力。",
            source_label="OpenAI News",
            summary="Optional safety feature.",
            published_at="Thu, 07 May 2026 00:00:00 GMT",
            tags=["safety"],
            category="general",
            importance=4,
            comparison_angle="safety",
        )
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=1,
            companies_covered=1,
            topic_clusters=[
                TopicCluster(
                    topic_id="safety-governance",
                    title="安全与治理",
                    summary="summary",
                    comparison="comparison",
                    trend="trend",
                    entries=[entry],
                )
            ],
            company_reports=[CompanyReport(company_slug="openai", company_name="OpenAI", entries=[entry], has_updates=True)],
            source_statuses=[],
        )
        html = render_daily(report)
        self.assertIn("Thu, 07 May 2026 00:00:00 GMT", html)

    def test_write_site_preserves_existing_archive_entries(self) -> None:
        older_report = DailyReport(
            date="2026-05-09",
            headline="older",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        newer_report = DailyReport(
            date="2026-05-10",
            headline="newer",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_site(older_report, output_dir)
            write_site(newer_report, output_dir)
            archive_html = (output_dir / "archive.html").read_text(encoding="utf-8")
            self.assertIn("archive-list", archive_html)
            self.assertIn("2026-05-10", archive_html)
            self.assertIn("2026-05-09", archive_html)


if __name__ == "__main__":
    unittest.main()
