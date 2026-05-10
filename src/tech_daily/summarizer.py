from __future__ import annotations

from .classifier import classify_entry
from .models import EnrichedEntry, RawEntry


class Summarizer:
    def summarize(self, entry: RawEntry) -> EnrichedEntry:
        return classify_entry(entry)
