from __future__ import annotations

from .llm_client import LLMClient
from .models import RawEntry
from .rule_summarizer import clean_whitespace


class LLMSummarizer:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def is_available(self) -> bool:
        return self.client.is_available()

    def summarize(self, entry: RawEntry, tags: list[str], category: str) -> str:
        payload = self.client.generate_json(
            instructions=(
                "你是科技行业日报编辑。请将单条官方动态压缩成 1-3 句中文简报。"
                "不要编造事实，不要写元话术，不要重复标题。必须点出发生了什么以及为什么值得看。"
            ),
            input_text=(
                f"公司：{entry.company_name}\n"
                f"标题：{entry.title}\n"
                f"摘要：{clean_whitespace(entry.summary)}\n"
                f"标签：{', '.join(tags)}\n"
                f"分类：{category}\n"
            ),
            schema_name="summary_payload",
            schema={
                "type": "object",
                "properties": {"summary_cn": {"type": "string"}},
                "required": ["summary_cn"],
                "additionalProperties": False,
            },
        )
        return payload["summary_cn"].strip()
