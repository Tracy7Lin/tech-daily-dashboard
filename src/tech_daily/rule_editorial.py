from __future__ import annotations

from collections import defaultdict

from .models import EnrichedEntry


def _company_angles(entries: list[EnrichedEntry]) -> dict[str, str]:
    grouped: dict[str, list[EnrichedEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.raw.company_name].append(entry)

    angles: dict[str, str] = {}
    for company_name, company_entries in grouped.items():
        lead = sorted(company_entries, key=lambda item: (-item.importance, item.raw.title))[0]
        angles[company_name] = angle_for_entry(lead)
    return angles


def angle_for_entry(entry: EnrichedEntry) -> str:
    tags = set(entry.tags)
    if {"customer", "enterprise"} <= tags:
        return "客户落地与业务验证"
    if {"safety", "consumer"} <= tags:
        return "面向用户触点的安全控制"
    if {"safety", "infrastructure"} <= tags:
        return "关键基础设施的安全防护"
    if "safety" in tags:
        return "安全与治理机制前置"
    if {"model", "developer"} <= tags:
        return "模型与平台能力外放"
    if "model" in tags:
        return "核心模型能力升级"
    if "infrastructure" in tags:
        return "底层基础设施扩张"
    if "hardware" in tags:
        return "终端或设备入口探索"
    if {"product", "consumer"} <= tags:
        return "具体产品与使用场景落地"
    if "customer" in tags:
        return "客户触达与用户价值验证"
    if "product" in tags:
        return "产品功能落地"
    if {"ai", "enterprise"} <= tags:
        return "企业流程中的 AI 落地"
    if "developer" in tags:
        return "开发者接入与平台扩展"
    if "ai" in tags:
        return "AI 能力向实际场景延展"
    if entry.category == "strategy":
        return "战略方向与资源配置"
    return "重点方向仍在继续试探"


def build_daily_headline(topic_clusters, company_reports, total_entries: int) -> str:
    if not total_entries:
        return ""
    active_companies = [report.company_name for report in company_reports if report.has_updates][:3]
    companies_label = "、".join(active_companies)
    lead = topic_clusters[0].title if topic_clusters else "官方动态"
    if len(topic_clusters) > 1:
        second = topic_clusters[1].title
        return (
            f"今天最值得关注的信号是，{lead}与{second}同时升温；"
            f"{companies_label} 正在把竞争继续推向更具体的产品、平台或落地场景。"
        )
    return (
        f"今天最值得关注的信号是，{lead}成为主线；"
        f"{companies_label} 都在围绕这一方向继续加码。"
    )


def build_topic_summary(title: str, entries: list[EnrichedEntry]) -> str:
    companies = sorted({entry.raw.company_name for entry in entries})
    angles = list(dict.fromkeys(angle_for_entry(entry) for entry in entries))
    if len(companies) == 1:
        return f"{companies[0]} 今天把 {title} 推到台前，重点落在{angles[0]}。"
    if len(angles) > 1:
        return (
            f"今天 {title} 的讨论主要由 {'、'.join(companies[:3])} 拉动，"
            f"焦点分别落在{angles[0]}与{angles[1]}。"
        )
    return f"今天 {title} 的讨论主要由 {'、'.join(companies[:3])} 拉动，核心重心落在{angles[0]}。"


def build_topic_comparison(entries: list[EnrichedEntry]) -> str:
    angles = _company_angles(entries)
    items = list(angles.items())
    if not items:
        return "暂无可比较的公司切入点。"
    if len(items) == 1:
        company, angle = items[0]
        return f"{company} 这次更偏向{angle}。"
    if len(items) == 2:
        return f"{items[0][0]} 更偏 {items[0][1]}，{items[1][0]} 则更偏 {items[1][1]}。"
    lead = f"{items[0][0]} 更偏 {items[0][1]}"
    rest = "；".join(f"{company} 更偏 {angle}" for company, angle in items[1:])
    return f"{lead}；{rest}。"


def build_topic_trend(title: str, entries: list[EnrichedEntry]) -> str:
    companies = sorted({entry.raw.company_name for entry in entries})
    if title == "安全与治理":
        return "这说明厂商正在把安全控制从附属要求前置到正式产品、用户触点和关键能力开放流程里。"
    if title == "客户落地案例":
        return "这说明竞争正在从能力展示转向真实客户案例、业务验证与可复制落地。"
    if title == "模型与能力发布":
        return "这说明竞争焦点已经不只是模型本身，而是模型如何通过 API、平台与具体场景释放价值。"
    if title == "新产品发布":
        return "这说明各家正在加快把 AI 或数字能力打包成更具体的产品入口，而不是停留在概念层。"
    if title == "AI 基础设施":
        return "这说明厂商开始把投入重心继续压向底层基础设施，为后续模型和产品扩张预留空间。"
    if title == "其他重要动态":
        return f"这说明除了主线 AI 竞争，{'、'.join(companies[:3])} 也在同步推进外围产品与场景动作。"
    return "这说明相关公司正在把同一方向的竞争进一步推向更具体的执行层。"


class RuleEditorial:
    def build_daily_headline(self, topic_clusters, company_reports, total_entries: int) -> str:
        return build_daily_headline(topic_clusters, company_reports, total_entries)

    def build_topic_summary(self, title: str, entries: list[EnrichedEntry]) -> str:
        return build_topic_summary(title, entries)

    def build_topic_comparison(self, entries: list[EnrichedEntry]) -> str:
        return build_topic_comparison(entries)

    def build_topic_trend(self, title: str, entries: list[EnrichedEntry]) -> str:
        return build_topic_trend(title, entries)
