from __future__ import annotations

from .models import EnrichedEntry, RawEntry
from .summarizer import Summarizer

TAG_KEYWORDS = {
    "ai": ("ai", "model", "llm", "agent", "genai", "copilot"),
    "product": ("launch", "release", "introduce", "new", "debut"),
    "developer": ("api", "sdk", "developer", "platform"),
    "enterprise": ("enterprise", "business", "workspace", "cloud"),
    "hardware": ("device", "phone", "laptop", "chip", "robot", "vehicle", "automotive"),
    "strategy": ("partnership", "strategy", "future", "vision", "roadmap"),
    "model": ("gpt", "claude", "gemini", "llama", "opus", "sonnet", "model"),
    "safety": ("safety", "privacy", "wellbeing", "trusted", "policy", "governance", "security"),
    "customer": ("customer", "customers", "bank", "uber", "enterprise", "adoption", "uses openai", "helps"),
    "infrastructure": ("data center", "compute", "fabric", "infrastructure", "silicon", "ethernet", "capacity"),
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
            entry.url.lower(),
        ]
    )


def classify_entry(entry: RawEntry) -> EnrichedEntry:
    blob = _lower_blob(entry)
    tags = [tag for tag, words in TAG_KEYWORDS.items() if any(word in blob for word in words)]
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
