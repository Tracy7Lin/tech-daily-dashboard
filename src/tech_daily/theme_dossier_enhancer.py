from __future__ import annotations

from dataclasses import replace

from .llm_client import LLMClient, LLMClientError
from .models import ThemeDossierBrief, ThemeDossierTimelineEvent


class ThemeDossierEnhancer:
    def __init__(self, mode: str = "rule", client: LLMClient | None = None) -> None:
        self.mode = mode
        self.client = client

    def enhance(self, brief: ThemeDossierBrief) -> ThemeDossierBrief:
        if self.mode == "rule":
            return brief
        if self.client is None or not self.client.is_available():
            return brief

        try:
            payload = self.client.generate_json(
                instructions=(
                    "你是科技情报专题研究助理。请在不引入新事实的前提下，"
                    "把给定的主题 dossier 基线改写成更像研究简报的中文表达。"
                    "不要改变主题状态，不要新增未给定的公司、事件或结论。"
                ),
                input_text=(
                    f"主题名称：{brief.primary_theme}\n"
                    f"主题阶段：{brief.theme_state}\n"
                    f"主题定义：{brief.theme_definition}\n"
                    f"主题摘要：{brief.theme_summary}\n"
                    f"参与公司：{brief.participating_companies}\n"
                    f"公司位置：{brief.company_positions}\n"
                    f"跟踪决策：{brief.tracking_decision}\n"
                    f"明日关注：{brief.next_day_focus}\n"
                    f"时间线：{[{'date': e.date, 'company': e.company, 'title': e.title, 'why_it_matters': e.why_it_matters} for e in brief.timeline_events]}\n"
                ),
                schema_name="theme_dossier_enhancement",
                schema={
                    "type": "object",
                    "properties": {
                        "theme_definition": {"type": "string"},
                        "theme_summary": {"type": "string"},
                        "tracking_decision": {"type": "string"},
                        "next_day_focus": {"type": "array", "items": {"type": "string"}},
                        "company_positions": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                        "timeline_events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "why_it_matters": {"type": "string"},
                                },
                                "required": ["why_it_matters"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "theme_definition",
                        "theme_summary",
                        "tracking_decision",
                        "next_day_focus",
                        "company_positions",
                        "timeline_events",
                    ],
                    "additionalProperties": False,
                },
            )
        except (LLMClientError, KeyError, TypeError, ValueError):
            return brief

        try:
            timeline = [
                replace(event, why_it_matters=(payload.get("timeline_events", [])[index].get("why_it_matters") or event.why_it_matters).strip())
                if index < len(payload.get("timeline_events", []))
                else event
                for index, event in enumerate(brief.timeline_events)
            ]
        except (AttributeError, IndexError, TypeError):
            return brief

        theme_definition = (payload.get("theme_definition") or "").strip()
        theme_summary = (payload.get("theme_summary") or "").strip()
        tracking_decision = (payload.get("tracking_decision") or "").strip()
        next_day_focus = [item.strip() for item in (payload.get("next_day_focus") or []) if isinstance(item, str) and item.strip()]
        company_positions = {
            company: value.strip()
            for company, value in (payload.get("company_positions") or {}).items()
            if company in brief.company_positions and isinstance(value, str) and value.strip()
        }
        if not theme_definition or not theme_summary or not tracking_decision:
            return brief

        return replace(
            brief,
            theme_definition=theme_definition,
            theme_summary=theme_summary,
            company_positions=company_positions or brief.company_positions,
            timeline_events=timeline,
            tracking_decision=tracking_decision,
            next_day_focus=next_day_focus or brief.next_day_focus,
            mode_used="llm",
        )
