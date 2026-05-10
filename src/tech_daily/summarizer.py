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


def _clean_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()


def _short_title(title: str, company_name: str) -> str:
    cleaned = _clean_whitespace(title)
    if cleaned.lower().startswith(company_name.lower()):
        cleaned = cleaned[len(company_name) :].strip(" -:,.")
    if len(cleaned) > TITLE_MAX_LEN:
        cleaned = cleaned[: TITLE_MAX_LEN - 1].rstrip() + "…"
    return cleaned or title.strip()


def _pick_focus(tags: list[str], category: str) -> str:
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


def _why_clause(summary: str, tags: list[str], category: str) -> str:
    if summary:
        lowered = summary.lower()
        if any(word in lowered for word in ("privacy", "safety", "trusted", "security")):
            return "重点在于把能力升级和安全控制同时往前推进。"
        if any(word in lowered for word in ("enterprise", "customer", "bank", "workflow", "business")):
            return "重点在于把能力进一步推向真实业务与工作流。"
        if any(word in lowered for word in ("model", "performance", "reasoning", "coding", "agents")):
            return "重点在于模型能力、推理表现或工作流效果的提升。"
    if "customer" in tags:
        return "重点在于真实客户场景中的采用和落地速度。"
    if "infrastructure" in tags:
        return "重点在于支撑后续 AI 能力扩张的底层投入。"
    if "safety" in tags:
        return "重点在于安全、治理与可控使用边界。"
    if category == "strategy":
        return "重点在于公司对外释放的方向判断与资源配置。"
    if category == "technology":
        return "重点在于 AI 能力与平台演进。"
    return "重点在于产品能力是否真正落地到用户或开发者场景。"


def build_summary(entry: RawEntry, tags: list[str], category: str) -> str:
    short_title = _short_title(entry.title, entry.company_name)
    focus = _pick_focus(tags, category)
    why = _why_clause(_clean_whitespace(entry.summary), tags, category)

    if category == "strategy":
        action = "披露了一项战略层面的更新"
    elif category == "technology":
        action = "发布了一项技术能力相关的更新"
    elif category == "product":
        action = "发布了一项产品相关的更新"
    else:
        action = "披露了一项值得关注的官方动态"

    return f"{entry.company_name} 围绕“{short_title}”{action}，核心看点是 {focus}。{why}"


class Summarizer:
    def summarize(self, entry: RawEntry, tags: list[str], category: str) -> str:
        return build_summary(entry, tags, category)
