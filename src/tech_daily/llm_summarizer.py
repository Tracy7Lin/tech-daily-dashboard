from __future__ import annotations

from .llm_client import LLMClient
from .llm_postprocess import clean_summary_text
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
                "你是科技行业日报编辑，负责把官方动态写成高质量中文简报。"
                "输出应像成熟科技简报，而不是模板改写。"
                "要求：2-3 句；不要复述标题；不要写“根据提供信息”“可以看出”等元话术；"
                "必须交代发生了什么，以及为什么值得关注。"
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
        return clean_summary_text(payload["summary_cn"], title=entry.title)
