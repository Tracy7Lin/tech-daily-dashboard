from __future__ import annotations

import re

from .models import EnrichedEntry, RawEntry
from .summarizer import Summarizer

TAG_KEYWORDS = {
    "ai": ("ai", "model", "models", "llm", "agent", "agents", "genai", "copilot"),
    "product": ("launch", "launches", "launched", "release", "releases", "released", "introduce", "introducing", "introduced", "new", "debut", "debuts"),
    "developer": ("api", "apis", "sdk", "sdks", "developer", "developers", "platform", "platforms"),
    "enterprise": ("enterprise", "enterprises", "business", "businesses", "workspace", "workspaces", "cloud"),
    "hardware": ("device", "devices", "phone", "phones", "laptop", "laptops", "chip", "chips", "robot", "robots", "vehicle", "vehicles", "automotive"),
    "strategy": ("partnership", "partnerships", "strategy", "strategic", "future", "vision", "roadmap"),
    "model": ("gpt", "claude", "gemini", "llama", "opus", "sonnet", "model", "models"),
    "safety": ("safety", "privacy", "trusted", "policy", "policies", "governance", "security", "safeguard", "safeguards"),
    "customer": ("customer", "customers", "bank", "banks", "uber", "adoption", "adopt", "deploy", "deployment", "uses openai", "use openai"),
    "infrastructure": ("data center", "data centers", "compute", "fabric", "infrastructure", "silicon", "ethernet", "capacity"),
    "consumer": ("chatgpt", "chrome", "assistant", "glasses", "alexa", "whatsapp"),
}

PRIORITY_COMPANIES = {"openai", "google", "microsoft", "anthropic", "meta", "amazon"}
SUMMARIZER = Summarizer()


def _lower_blob(entry: RawEntry) -> str:
    return " ".join(
        [
            entry.title.lower(),
            entry.summary.lower(),
            entry.content.lower(),
        ]
    )


def _contains_keyword(blob: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, blob) is not None


def classify_entry(entry: RawEntry) -> EnrichedEntry:
    blob = _lower_blob(entry)
    tags = [tag for tag, words in TAG_KEYWORDS.items() if any(_contains_keyword(blob, word) for word in words)]
    if not tags:
        tags = ["general"]

    if "strategy" in tags:
        category = "strategy"
    elif "product" in tags or "hardware" in tags:
        category = "product"
    elif "ai" in tags or "developer" in tags:
        category = "technology"
    else:
        category = "general"

    importance = 1
    if "ai" in tags:
        importance += 1
    if "product" in tags or "strategy" in tags:
        importance += 1
    if "enterprise" in tags or "hardware" in tags:
        importance += 1
    if "model" in tags or "safety" in tags or "infrastructure" in tags:
        importance += 1
    if entry.company_slug in PRIORITY_COMPANIES and any(
        tag in tags for tag in ("model", "safety", "customer", "infrastructure", "developer")
    ):
        importance += 1

    comparison_angle = "、".join(tag for tag in tags if tag != "general") or "general"
    summary_cn = SUMMARIZER.summarize(entry, tags, category)
    return EnrichedEntry(
        raw=entry,
        tags=tags,
        category=category,
        importance=min(importance, 5),
        summary_cn=summary_cn,
        comparison_angle=comparison_angle,
    )
