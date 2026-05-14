from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Source:
    kind: str
    url: str
    label: str = ""
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    path_prefixes: list[str] = field(default_factory=list)
    max_entries: int = 20
    fetch_article_details: bool = False
    detail_fetch_limit: int = 5
    require_published_at: bool = False


@dataclass(frozen=True)
class Company:
    slug: str
    name: str
    region: str
    sources: list[Source] = field(default_factory=list)


@dataclass(frozen=True)
class RawEntry:
    company_slug: str
    company_name: str
    source_label: str
    title: str
    url: str
    summary: str = ""
    published_at: str = ""
    content: str = ""
    requires_published_at: bool = False


@dataclass(frozen=True)
class SourceStatus:
    company_slug: str
    company_name: str
    source_label: str
    source_url: str
    ok: bool
    message: str
    fetched_count: int = 0
    kept_count: int = 0
    date_matched_count: int = 0
    final_included_count: int = 0


@dataclass(frozen=True)
class EnrichedEntry:
    raw: RawEntry
    tags: list[str]
    category: str
    importance: int
    summary_cn: str
    comparison_angle: str


@dataclass(frozen=True)
class TopicCluster:
    topic_id: str
    title: str
    summary: str
    comparison: str
    trend: str
    entries: list[EnrichedEntry] = field(default_factory=list)


@dataclass(frozen=True)
class CompanyReport:
    company_slug: str
    company_name: str
    entries: list[EnrichedEntry] = field(default_factory=list)
    has_updates: bool = False


@dataclass(frozen=True)
class DailyIntelBrief:
    report_date: str
    editorial_signal: str
    ops_signal: str
    top_content_themes: list[str] = field(default_factory=list)
    watchlist: list[str] = field(default_factory=list)
    source_risks: list[str] = field(default_factory=list)
    recoveries: list[str] = field(default_factory=list)
    tomorrow_focus: list[str] = field(default_factory=list)
    mode_used: str = "rule"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DailyReport:
    date: str
    headline: str
    hottest_topics: list[str]
    total_entries: int
    companies_covered: int
    active_companies: list[str] = field(default_factory=list)
    topic_clusters: list[TopicCluster] = field(default_factory=list)
    company_reports: list[CompanyReport] = field(default_factory=list)
    source_statuses: list[SourceStatus] = field(default_factory=list)
    agent_brief: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
