from __future__ import annotations

import re

from .models import RawEntry

TITLE_MAX_LEN = 72

TAG_FOCUS = {
    "model": "模型能力升级",
    "ai-agent": "Agent 工作流能力",
    "developer": "开发者接入与平台能力",
    "enterprise": "企业场景落地",
    "customer": "客户落地与采用进展",
    "safety": "安全、治理与可信使用",
    "infrastructure": "算力、数据中心与基础设施",
    "hardware": "终端与硬件入口",
    "consumer": "面向用户的产品体验",
}


def _contains_phrase(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def clean_whitespace(text: str) -> str:
    without_html = re.sub(r"<[^>]+>", " ", text)
    return " ".join(without_html.split()).strip()


def short_title(title: str, company_name: str) -> str:
    cleaned = clean_whitespace(title)
    if cleaned.lower().startswith(company_name.lower()):
        cleaned = cleaned[len(company_name) :].strip(" -:,.")
    if len(cleaned) > TITLE_MAX_LEN:
        cleaned = cleaned[: TITLE_MAX_LEN - 1].rstrip() + "…"
    return cleaned or title.strip()


def pick_focus(tags: list[str], category: str) -> str:
    ordered = ("safety", "customer", "infrastructure", "developer", "enterprise", "hardware", "model", "consumer")
    for tag in ordered:
        if tag in tags:
            return TAG_FOCUS[tag]
    if category == "strategy":
        return "合作方向与战略布局"
    if category == "product":
        return "产品更新与功能落地"
    if category == "technology":
        return "AI 能力与平台演进"
    return "官方动态与后续影响"


def why_clause(summary: str, tags: list[str], category: str) -> str:
    lowered = summary.lower()
    if summary:
        if any(_contains_phrase(lowered, word) for word in ("privacy", "safety", "trusted", "security", "safeguard", "safeguards")):
            return "重点在于把能力升级和安全控制同时往前推进。"
        if any(_contains_phrase(lowered, word) for word in ("global", "globally", "worldwide")):
            return "重点在于把这项能力从局部试点推向面向更大范围用户的正式上线。"
        if any(_contains_phrase(lowered, word) for word in ("enterprise", "customer", "customers", "bank", "banks", "workflow", "workflows", "business", "deploy", "deployment")):
            return "重点在于验证能力能否进入真实业务场景并形成可复制的客户案例。"
        if any(_contains_phrase(lowered, word) for word in ("model", "models", "reasoning", "coding", "agents", "agent")):
            return "重点在于模型能力、推理表现或工作流效果的提升。"
        if any(_contains_phrase(lowered, word) for word in ("personalized", "personalised", "insights", "experience", "available")):
            return "重点在于把新能力直接变成用户可感知的日常体验。"
    if "customer" in tags:
        return "重点在于真实业务场景中的采用速度，以及能否沉淀成客户案例。"
    if "infrastructure" in tags:
        return "重点在于支撑后续 AI 能力扩张的底层投入。"
    if "safety" in tags:
        return "重点在于安全、治理与可控使用边界。"
    if category == "strategy":
        return "重点在于公司对外释放的方向判断与资源配置。"
    if category == "technology":
        return "重点在于 AI 能力与平台演进。"
    return "重点在于产品能力是否真正落地到用户或开发者场景。"


def action_clause(tags: list[str], category: str) -> str:
    if "customer" in tags:
        return "披露了一则客户案例"
    if "safety" in tags:
        return "更新了安全与治理相关能力"
    if "infrastructure" in tags:
        return "披露了基础设施相关进展"
    if "model" in tags:
        return "发布了模型与能力更新"
    if category == "strategy":
        return "披露了一项战略层面的更新"
    if category == "technology":
        return "发布了一项技术能力相关的更新"
    if category == "product":
        return "发布了一项产品相关的更新"
    return "披露了一项值得关注的官方动态"


def build_summary(entry: RawEntry, tags: list[str], category: str) -> str:
    title = short_title(entry.title, entry.company_name)
    focus = pick_focus(tags, category)
    why = why_clause(clean_whitespace(entry.summary), tags, category)
    action = action_clause(tags, category)
    return f"{entry.company_name} 围绕“{title}”{action}，核心看点是 {focus}。{why}"


class RuleSummarizer:
    def summarize(self, entry: RawEntry, tags: list[str], category: str) -> str:
        return build_summary(entry, tags, category)
