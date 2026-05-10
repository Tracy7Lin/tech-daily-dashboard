from __future__ import annotations

from collections import defaultdict

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
    if {"model", "ai"} <= tags:
        return "model-release"
    if "safety" in tags:
        return "safety-governance"
    if "customer" in tags:
        return "customer-adoption"
    if "infrastructure" in tags:
        return "ai-infrastructure"
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
        names = [entry.raw.company_name for entry in topic_entries]
        title = TOPIC_TITLES.get(topic_id, topic_id)
        sorted_entries = sorted(topic_entries, key=lambda item: (-item.importance, item.raw.company_name))
        company_angles: dict[str, str] = {}
        for entry in sorted_entries:
            if entry.raw.company_name not in company_angles:
                angle = entry.category
                if "model" in entry.tags:
                    angle = "模型能力"
                elif "safety" in entry.tags:
                    angle = "安全治理"
                elif "customer" in entry.tags:
                    angle = "客户落地"
                elif "infrastructure" in entry.tags:
                    angle = "基础设施"
                elif "developer" in entry.tags:
                    angle = "开发者平台"
                company_angles[entry.raw.company_name] = angle
        comparison = "；".join(f"{name} 偏 {angle}" for name, angle in company_angles.items())
        trend = f"相关公司包括 {', '.join(sorted(set(names)))}，显示该方向正在继续演进。"
        summary = f"今日围绕 {title} 有 {len(topic_entries)} 条高相关动态，主要集中在 {', '.join(sorted(set(names))[:3])}。"
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
