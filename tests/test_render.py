import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.models import CompanyReport, DailyReport, EnrichedEntry, RawEntry, SourceStatus, TopicCluster
from tech_daily.render import render_archive, render_daily, render_dossier_page, render_index, render_topic_page, write_site


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
        report = replace(
            report,
            theme_tracking_brief={
                "primary_theme": "AI Agent",
                "theme_summary": "AI Agent 仍然是当前主专题。",
                "participating_companies": ["OpenAI"],
                "next_day_theme_focus": ["AI Agent"],
            },
            theme_dossier_brief={
                "primary_theme": "AI Agent",
                "theme_state": "emerging",
                "theme_definition": "AI Agent 正在从能力发布走向更完整的平台化动作。",
                "tracking_decision": "建议继续跟踪。",
            },
            chat_agent_context={
                "report_date": "2026-05-10",
                "quick_questions": ["这个主专题现在怎么理解？"],
            },
        )
        html = render_index(report)
        self.assertIn("site-shell", html)
        self.assertIn("cover-grid", html)
        self.assertIn("当前主专题", html)
        self.assertIn("进入专题页", html)
        self.assertIn("查看最新日报", html)
        self.assertIn("最近几期", html)
        self.assertIn("./2026-05-10/index.html", html)
        self.assertIn("./2026-05-10/topic.html", html)
        self.assertIn("./2026-05-10/dossier.html", html)
        self.assertIn("chat-drawer", html)
        self.assertIn("cover-frame", html)
        self.assertIn("editorial-rule", html)
        self.assertIn("--paper", html)
        self.assertIn("ink-panel", html)
        self.assertIn("cover-spotlight", html)
        self.assertIn("section-card-featured", html)
        self.assertIn("data-motion", html)
        self.assertIn("page-curtain", html)
        self.assertIn("page-transition-script", html)
        self.assertIn("data-page-link", html)
        self.assertIn("cover-ledger", html)
        self.assertIn("cover-editorial-note", html)
        self.assertIn("section-rail-asymmetric", html)
        self.assertIn("magazine-nav", html)
        self.assertIn("./archive.html", html)

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
        self.assertIn("进入专题页", html)
        self.assertIn("查看主题档案", html)
        self.assertIn("page-curtain", html)
        self.assertIn("page-transition-script", html)
        self.assertIn("data-page-link", html)
        self.assertIn("magazine-nav", html)
        self.assertIn("返回主刊首页", html)
        self.assertIn("./topic.html", html)
        self.assertIn("./dossier.html", html)

    def test_render_daily_includes_agent_brief_block_when_present(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[],
            source_statuses=[],
            agent_brief={
                "editorial_signal": "内容层最值得关注的是安全与治理。",
                "ops_signal": "当前优先处理 tesla。",
                "tomorrow_focus": ["安全与治理", "tesla"],
            },
        )
        html = render_daily(report)
        self.assertIn("情报判断", html)
        self.assertIn("今日核心判断", html)
        self.assertIn("当前优先处理 tesla", html)
        self.assertIn("查看完整 Markdown 报告", html)

    def test_render_daily_includes_cross_day_brief_block_when_present(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[],
            source_statuses=[],
            cross_day_brief={
                "warming_themes": ["安全与治理"],
                "steady_companies": ["OpenAI"],
                "persistent_source_risks": ["tesla"],
                "recent_source_recoveries": ["alibaba"],
                "next_day_focus": ["安全与治理", "tesla"],
            },
        )
        html = render_daily(report)
        self.assertIn("跨日观察", html)
        self.assertIn("连续活跃公司", html)
        self.assertIn("OpenAI", html)
        self.assertIn("查看完整跨日 Markdown 报告", html)

    def test_render_daily_includes_theme_tracking_brief_block_when_present(self) -> None:
        report = DailyReport(
            date="2026-05-15",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[],
            source_statuses=[],
            theme_tracking_brief={
                "primary_theme": "安全与治理",
                "theme_summary": "安全与治理仍是最近几天最值得继续跟踪的专题。",
                "participating_companies": ["OpenAI", "Google"],
                "continue_tracking": True,
                "next_day_theme_focus": ["安全与治理"],
            },
        )
        html = render_daily(report)
        self.assertIn("专题跟踪", html)
        self.assertIn("主专题", html)
        self.assertIn("进入专题页", html)

    def test_render_daily_includes_theme_dossier_brief_block_when_present(self) -> None:
        report = DailyReport(
            date="2026-05-15",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[],
            source_statuses=[],
            theme_dossier_brief={
                "primary_theme": "安全与治理",
                "theme_state": "active",
                "theme_definition": "不同公司正在把安全与治理从原则讨论推进到更具体的产品与平台动作。",
                "theme_summary": "安全与治理已从单点动作变成持续主线。",
                "tracking_decision": "建议继续跟踪，因为多家公司都在通过不同切入点推进这一主题。",
                "lead_positions": [
                    "OpenAI：更偏平台与安全控制前置",
                    "Google：更偏产品功能约束",
                ],
                "timeline_highlight": "2026-05-15 · Google · Google expands education safeguards",
            },
        )
        html = render_daily(report)
        self.assertIn("主题档案", html)
        self.assertIn("当前阶段", html)
        self.assertIn("查看主题档案", html)
        self.assertIn("公司位置观察", html)
        self.assertIn("时间线焦点", html)

    def test_render_topic_page_outputs_cross_day_tracking_and_dossier_summary(self) -> None:
        report = DailyReport(
            date="2026-05-17",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=0,
            companies_covered=0,
            cross_day_brief={
                "warming_themes": ["安全与治理"],
                "steady_companies": ["OpenAI", "Google"],
                "next_day_focus": ["安全与治理"],
            },
            theme_tracking_brief={
                "primary_theme": "安全与治理",
                "theme_summary": "安全与治理仍是最近几天最值得继续盯住的专题。",
                "participating_companies": ["OpenAI", "Google"],
                "theme_evolution": "正在从原则讨论走向更明确的产品约束。",
                "continue_tracking": True,
                "next_day_theme_focus": ["安全与治理"],
            },
            theme_dossier_brief={
                "primary_theme": "安全与治理",
                "theme_definition": "不同公司正在把安全机制前置到产品和平台层。",
                "theme_state": "emerging",
                "tracking_decision": "建议继续跟踪。",
            },
            chat_agent_context={
                "report_date": "2026-05-17",
                "quick_questions": ["这个主专题现在怎么理解？"],
            },
        )
        html = render_topic_page(report)
        self.assertIn("专题页", html)
        self.assertIn("跨日观察", html)
        self.assertIn("专题跟踪", html)
        self.assertIn("主题档案摘要", html)
        self.assertIn("./dossier.html", html)
        self.assertIn("chat-drawer", html)
        self.assertIn("page-frame", html)
        self.assertIn("section-rule", html)
        self.assertIn("page-accent-band", html)
        self.assertIn("page-curtain", html)
        self.assertIn("page-transition-script", html)
        self.assertIn("data-page-link", html)
        self.assertIn("spread-layout", html)
        self.assertIn("spread-margin-note", html)
        self.assertIn("magazine-nav", html)
        self.assertIn("./dossier.html", html)
        self.assertIn("../archive.html", html)

    def test_render_dossier_page_outputs_theme_archive_content(self) -> None:
        report = DailyReport(
            date="2026-05-17",
            headline="headline",
            hottest_topics=["安全与治理"],
            total_entries=0,
            companies_covered=0,
            theme_dossier_brief={
                "primary_theme": "安全与治理",
                "theme_definition": "不同公司正在把安全机制前置到产品和平台层。",
                "theme_state": "emerging",
                "theme_summary": "安全与治理已成为值得持续跟踪的主题。",
                "lead_positions": ["OpenAI：偏平台", "Google：偏产品"],
                "timeline_highlight": "2026-05-17 · OpenAI · Trusted Contact",
                "tracking_decision": "建议继续跟踪。",
                "next_day_focus": ["安全与治理"],
            },
            chat_agent_context={
                "report_date": "2026-05-17",
                "quick_questions": ["为什么现在是 emerging？"],
            },
        )
        html = render_dossier_page(report)
        self.assertIn("主题档案", html)
        self.assertIn("当前阶段", html)
        self.assertIn("主题定义", html)
        self.assertIn("公司位置观察", html)
        self.assertIn("关键时间线", html)
        self.assertIn("chat-drawer", html)
        self.assertIn("dossier-frame", html)
        self.assertIn("timeline-rule", html)
        self.assertIn("dossier-accent-band", html)
        self.assertIn("page-curtain", html)
        self.assertIn("page-transition-script", html)
        self.assertIn("data-page-link", html)
        self.assertIn("dossier-spread", html)
        self.assertIn("timeline-entry", html)
        self.assertIn("magazine-nav", html)
        self.assertIn("./topic.html", html)
        self.assertIn("../archive.html", html)

    def test_render_daily_includes_chat_agent_shell_when_context_present(self) -> None:
        report = DailyReport(
            date="2026-05-15",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[],
            source_statuses=[],
            chat_agent_context={
                "report_date": "2026-05-15",
                "daily_summary": {"answer": "今天最值得关注的是安全与治理。"},
                "theme_tracking": {"primary_theme": "安全与治理", "answer": "安全与治理仍是主专题。"},
                "ops_status": {"answer": "当前优先处理 tesla。"},
                "companies": ["Google"],
                "company_answers": {"google": "Google 最近几天仍有动作。"},
                "quick_questions": ["今天最值得关注什么？"],
                "follow_up_suggestions": ["Google 最近几天在做什么？"],
                "mode_used": "rule",
            },
        )
        html = render_daily(report)
        self.assertIn("情报问答", html)
        self.assertIn("chat-drawer", html)
        self.assertIn("今天最值得关注什么？", html)
        self.assertIn("chat-status", html)
        self.assertIn("正在整理静态回答", html)
        self.assertIn("使用 python run_dashboard.py serve --port 8080 启动实时问答服务", html)
        self.assertIn("aria-live='polite'", html)
        self.assertIn("aria-expanded='false'", html)
        self.assertIn("/api/chat", html)
        self.assertIn("当前使用真实增强问答模式", html)
        self.assertIn("chat-evidence", html)
        self.assertIn("messages: conversationHistory", html)
        self.assertIn("chat-follow-ups", html)
        self.assertIn("回答依据来源", html)
        self.assertIn("chat-evidence-reference", html)

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
        html = render_daily(report)
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
        html = render_daily(report)
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

    def test_render_company_report_empty_state_distinguishes_stable_no_news(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="headline",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
            topic_clusters=[],
            company_reports=[CompanyReport(company_slug="openai", company_name="OpenAI", entries=[], has_updates=False)],
            source_statuses=[
                SourceStatus(
                    company_slug="openai",
                    company_name="OpenAI",
                    source_label="OpenAI News",
                    source_url="https://openai.com/news/rss.xml",
                    ok=True,
                    message="fetched:10;kept:10;date_matched:0;final_included:0",
                    fetched_count=10,
                    kept_count=10,
                    date_matched_count=0,
                    final_included_count=0,
                )
            ],
        )
        html = render_daily(report)
        self.assertIn("当日无动态", html)
        self.assertIn("官方信源抓取正常", html)
        self.assertNotIn("信源暂未稳定", html)

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

    def test_render_archive_includes_magazine_nav_and_latest_links(self) -> None:
        report = DailyReport(
            date="2026-05-10",
            headline="newer",
            hottest_topics=[],
            total_entries=0,
            companies_covered=0,
        )
        html = render_archive([report])

        self.assertIn("magazine-nav", html)
        self.assertIn("./index.html", html)
        self.assertIn("./2026-05-10/index.html", html)
        self.assertIn("./2026-05-10/topic.html", html)
        self.assertIn("./2026-05-10/dossier.html", html)


if __name__ == "__main__":
    unittest.main()
