from __future__ import annotations

from collections import defaultdict

from .editorial import build_topic_comparison, build_topic_summary, build_topic_trend
from .models import EnrichedEntry, TopicCluster

TOPIC_TITLES = {
    "ai-agent": "AI Agent",
    "enterprise-ai": "企业 AI 平台",
    "model-release": "模型与能力发布",
    "safety-governance": "安全与治理",
    "customer-adoption": "客户落地案例",
    "ai-infrastructure": "AI 基础设施",
    "consumer-entry": "消费级入口",
    "product-launch": "新产品发布",
    "device-entry": "终端 AI 入口",
    "general": "其他重要动态",
}


def topic_id_for_entry(entry: EnrichedEntry) -> str:
    tags = set(entry.tags)
    if "safety" in tags:
        return "safety-governance"
    if "customer" in tags:
        return "customer-adoption"
    if "infrastructure" in tags:
        return "ai-infrastructure"
    if {"model", "ai"} <= tags:
        return "model-release"
    if {"ai", "developer"} <= tags:
        return "ai-agent"
    if {"ai", "enterprise"} <= tags:
        return "enterprise-ai"
    if {"ai", "consumer"} <= tags:
        return "consumer-entry"
    if {"ai", "hardware"} <= tags:
        return "device-entry"
    if "product" in tags:
        return "product-launch"
    return "general"


def group_entries_by_topic(entries: list[EnrichedEntry]) -> dict[str, list[EnrichedEntry]]:
    grouped: dict[str, list[EnrichedEntry]] = defaultdict(list)
    for entry in entries:
        grouped[topic_id_for_entry(entry)].append(entry)
    return dict(grouped)


def build_topic_clusters(entries: list[EnrichedEntry], limit: int = 5) -> list[TopicCluster]:
    grouped = group_entries_by_topic(entries)
    clusters: list[TopicCluster] = []
    for topic_id, topic_entries in grouped.items():
        title = TOPIC_TITLES.get(topic_id, topic_id)
        sorted_entries = sorted(topic_entries, key=lambda item: (-item.importance, item.raw.company_name))
        comparison = build_topic_comparison(sorted_entries)
        trend = build_topic_trend(title, sorted_entries)
        summary = build_topic_summary(title, sorted_entries)
        clusters.append(
            TopicCluster(
                topic_id=topic_id,
                title=title,
                summary=summary,
                comparison=comparison,
                trend=trend,
                entries=sorted_entries,
            )
        )
    clusters.sort(key=lambda cluster: len(cluster.entries), reverse=True)
    return clusters[:limit]
