from __future__ import annotations

from .llm_client import LLMClient
from .llm_postprocess import clean_editorial_text, validate_mentioned_companies
from .models import EnrichedEntry
from .rule_editorial import (
    build_daily_headline as build_rule_daily_headline,
    build_topic_comparison as build_rule_topic_comparison,
    build_topic_trend as build_rule_topic_trend,
)


def _entry_lines(entries: list[EnrichedEntry], limit: int = 4) -> str:
    parts = []
    for entry in entries[:limit]:
        parts.append(
            f"- 公司：{entry.raw.company_name}；标题：{entry.raw.title}；"
            f"标签：{', '.join(entry.tags)}；分类：{entry.category}；摘要：{entry.raw.summary}"
        )
    return "\n".join(parts)


class LLMEditorial:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def is_available(self) -> bool:
        return self.client.is_available()

    def build_daily_headline(self, topic_clusters, company_reports, total_entries: int) -> str:
        if total_entries <= 3:
            return build_rule_daily_headline(topic_clusters, company_reports, total_entries)
        active_companies = [report.company_name for report in company_reports if report.has_updates][:4]
        topics = [cluster.title for cluster in topic_clusters[:3]]
        payload = self.client.generate_json(
            instructions=(
                "你是科技行业分析博客编辑。请写一句中文日报总览，强调今天最值得关注的信号。"
                "要像高质量行业简报，不要使用模板腔，不要写元话术。"
            ),
            input_text=(
                f"总条数：{total_entries}\n"
                f"热点主题：{'、'.join(topics)}\n"
                f"活跃公司：{'、'.join(active_companies)}\n"
            ),
            schema_name="headline_payload",
            schema={
                "type": "object",
                "properties": {"headline": {"type": "string"}},
                "required": ["headline"],
                "additionalProperties": False,
            },
        )
        return clean_editorial_text(payload["headline"])

    def build_topic_summary(self, title: str, entries: list[EnrichedEntry]) -> str:
        return self._build_topic_field(title, entries, "summary", "总结这个主题今天真正发生了什么。")

    def build_topic_comparison(self, entries: list[EnrichedEntry]) -> str:
        companies = sorted({entry.raw.company_name for entry in entries})
        if len(companies) <= 1:
            return build_rule_topic_comparison(entries)

        payload = self.client.generate_json(
            instructions=(
                "你是科技行业分析博客编辑。请比较给定公司之间的切入点差异。"
                "只能比较输入中明确出现的公司，不得引入任何未提供的公司、品牌或媒体。"
                "不要使用“根据提供信息”“可以看出”这类元话术。"
            ),
            input_text=(
                f"允许提及的公司：{'、'.join(companies)}\n"
                f"代表事件：\n{_entry_lines(entries)}\n"
            ),
            schema_name="comparison_payload",
            schema={
                "type": "object",
                "properties": {
                    "comparison": {"type": "string"},
                    "mentioned_companies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["comparison", "mentioned_companies"],
                "additionalProperties": False,
            },
        )
        validate_mentioned_companies(payload["mentioned_companies"], companies)
        return clean_editorial_text(payload["comparison"])

    def build_topic_trend(self, title: str, entries: list[EnrichedEntry]) -> str:
        companies = sorted({entry.raw.company_name for entry in entries})
        if len(companies) <= 1:
            return build_rule_topic_trend(title, entries)
        return self._build_topic_field(title, entries, "trend", "总结这说明行业正在往哪里变化。")

    def _build_topic_field(self, title: str, entries: list[EnrichedEntry], field_name: str, instruction: str) -> str:
        payload = self.client.generate_json(
            instructions=(
                "你是科技行业分析博客编辑。请根据给定主题和代表事件输出高质量中文分析。"
                "不要使用“根据提供信息”“可以看出”这类元话术。"
                + instruction
            ),
            input_text=f"主题：{title}\n代表事件：\n{_entry_lines(entries)}\n",
            schema_name=f"{field_name}_payload",
            schema={
                "type": "object",
                "properties": {field_name: {"type": "string"}},
                "required": [field_name],
                "additionalProperties": False,
            },
        )
        return clean_editorial_text(payload[field_name])
