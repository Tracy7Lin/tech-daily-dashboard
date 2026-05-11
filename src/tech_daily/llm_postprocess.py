from __future__ import annotations

import re

META_PHRASES = (
    "根据提供信息",
    "可以看出",
    "从以上信息来看",
    "从这些信息来看",
    "综合来看",
    "整体来看",
    "值得一提的是",
)

GENERIC_PATTERNS = (
    "这是一次更新",
    "都在推进相关工作",
    "相关工作",
)

MAX_SUMMARY_CHARS = 160
MAX_EDITORIAL_CHARS = 140


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = text.replace("。。", "。")
    return text


def _trim_title_repetition(text: str, title: str) -> str:
    cleaned_title = _clean_text(title)
    if not cleaned_title:
        return text
    patterns = [
        rf"^{re.escape(cleaned_title)}[。；，,:：\s-]*",
        rf"^[^。！？]*{re.escape(cleaned_title)}[。；，,:：\s-]*",
    ]
    updated = text
    for pattern in patterns:
        updated = re.sub(pattern, "", updated, count=1, flags=re.IGNORECASE)
    return updated.strip()


def _remove_meta_phrases(text: str) -> str:
    updated = text
    for phrase in META_PHRASES:
        updated = updated.replace(phrase, "")
    updated = re.sub(r"^[，,。；;:\s]+", "", updated)
    updated = re.sub(r"[，,]{2,}", "，", updated)
    return updated.strip()


def _enforce_max_length(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    shortened = text[: limit - 1].rstrip("，,；;:： ") + "…"
    return shortened


def _is_low_signal(text: str) -> bool:
    if len(text) < 18:
        return True
    return any(pattern in text for pattern in GENERIC_PATTERNS)


def clean_summary_text(text: str, *, title: str) -> str:
    cleaned = _clean_text(text)
    cleaned = _remove_meta_phrases(cleaned)
    cleaned = _trim_title_repetition(cleaned, title)
    cleaned = _clean_text(cleaned)
    cleaned = _enforce_max_length(cleaned, MAX_SUMMARY_CHARS)
    if _is_low_signal(cleaned):
        raise ValueError("llm_summary_low_signal")
    return cleaned


def clean_editorial_text(text: str) -> str:
    cleaned = _clean_text(text)
    cleaned = _remove_meta_phrases(cleaned)
    cleaned = _clean_text(cleaned)
    cleaned = _enforce_max_length(cleaned, MAX_EDITORIAL_CHARS)
    if _is_low_signal(cleaned):
        raise ValueError("llm_editorial_low_signal")
    return cleaned
