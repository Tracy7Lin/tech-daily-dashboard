from __future__ import annotations

from .chat_agent_memory import resolve_follow_up_route, trim_history
from .llm_client import LLMClient, LLMClientError
from .research_assistant_policy import build_evidence_item, finalize_answer_payload, follow_up_suggestions_for


class ResearchAgentResponder:
    def __init__(self, mode: str = "rule", client: LLMClient | None = None) -> None:
        self.mode = mode
        self.client = client

    def answer(self, context: dict, history: list[dict] | None = None) -> dict:
        rule_answer = self._rule_answer(context, history=history)
        client_available = True
        if self.client is None:
            client_available = False
        elif hasattr(self.client, "is_available"):
            client_available = bool(self.client.is_available())
        if self.mode == "rule" or not client_available:
            return rule_answer
        try:
            llm_answer = self._generate_llm_answer(context, rule_answer, history=history)
        except (LLMClientError, KeyError, TypeError, ValueError):
            return rule_answer
        if not llm_answer or not llm_answer.get("answer"):
            return rule_answer
        return {
            **rule_answer,
            "answer": llm_answer["answer"],
            "evidence_items": llm_answer.get("evidence_items") or rule_answer["evidence_items"],
            "evidence_points": llm_answer.get("evidence_points") or rule_answer["evidence_points"],
            "follow_up_suggestions": llm_answer.get("follow_up_suggestions") or rule_answer["follow_up_suggestions"],
            "mode_used": llm_answer.get("mode_used", "llm"),
        }

    def _rule_answer(self, context: dict, history: list[dict] | None = None) -> dict:
        question_type = context.get("question_type", "out_of_scope")
        primary_theme = context.get("primary_theme", "")
        tracking_decision = context.get("tracking_decision", "")
        theme_state = context.get("theme_state", "")
        dossier = context.get("theme_dossier", {})
        report = context.get("report", {})
        company_positions = context.get("company_positions", {})
        entity = context.get("entity", "")
        timeline_events = context.get("timeline_events", [])
        question = context.get("question", "")
        evidence_items: list[dict] = []
        evidence_points: list[str] = []
        sources_used: list[str] = [context.get("primary_source", "report.json")]

        resolved_route = resolve_follow_up_route(
            question,
            history,
            context.get("companies", []),
            primary_theme,
        )
        if resolved_route:
            resolved_question_type, resolved_entity = resolved_route
        else:
            resolved_question_type, resolved_entity = question_type, entity
        if resolved_question_type != question_type:
            question_type = resolved_question_type
            entity = resolved_entity

        if question_type == "dossier_summary":
            definition = dossier.get("theme_definition", "")
            summary = dossier.get("theme_summary", "") or context.get("theme_tracking_brief", {}).get("theme_summary", "")
            answer = f"{primary_theme} 当前最值得从 {definition or summary or '主题持续升温'} 这个角度理解。{tracking_decision}".strip()
            if theme_state:
                evidence_items.append(build_evidence_item("theme_dossier.json", "专题档案", f"当前主题阶段为 {theme_state}。"))
        elif question_type == "theme_state":
            summary = dossier.get("theme_summary", "") or context.get("cross_day_intel_brief", {}).get("editorial_signal", "")
            answer = f"{primary_theme or '这个主题'} 当前处于 {theme_state or '观察期'}，因为它已经形成持续信号，但还没有完全稳定。{summary} {tracking_decision}".strip()
            evidence_items.append(build_evidence_item("theme_dossier.json", "专题档案", f"状态机判断为 {theme_state or '观察期'}。"))
        elif question_type == "company_position":
            position = company_positions.get(entity, "")
            answer = (
                f"{entity} 在 {primary_theme} 这个专题里目前更偏向 {position or '持续参与但位置尚未完全稳定'}。"
                f" {tracking_decision}".strip()
            )
            evidence_items.append(build_evidence_item("theme_dossier.json", "公司位置", f"{entity} 的 dossier 位置是：{position or '待进一步明确'}。"))
        elif question_type == "timeline_focus":
            lead = timeline_events[-1] if timeline_events else {}
            title = lead.get("title", "近期代表事件")
            why = lead.get("why_it_matters", "")
            company = lead.get("company", "相关公司")
            answer = f"最近几天最关键的时间线信号来自 {company} 的“{title}”。{why}".strip()
            evidence_items.append(build_evidence_item("theme_dossier.json", "关键时间线", f"{lead.get('date', '')} · {company} · {title}"))
        elif question_type == "company_focus":
            company_reports = report.get("company_reports", [])
            matched = next((item for item in company_reports if item.get("company_name", "").lower() == entity.lower()), {})
            entries = matched.get("entries", [])
            latest = entries[0].get("raw", {}).get("title", "") if entries else ""
            answer = f"{entity} 最近几天最值得看的动作是“{latest}”。" if latest else f"{entity} 最近几天没有明显的高价值动态被保留。"
            if latest:
                evidence_items.append(build_evidence_item("report.json", "公司动态", latest))
        elif question_type == "theme_focus":
            answer = context.get("theme_tracking_brief", {}).get("theme_summary", "") or context.get("editorial_signal", "") or "当前主专题仍在形成。"
        elif question_type == "ops_status":
            answer = context.get("operator_brief", "") or "当前没有额外运维提示。"
            for issue in (context.get("health_snapshot", {}).get("high_priority_runtime_issues") or [])[:2]:
                evidence_items.append(
                    build_evidence_item(
                        "health_snapshot.json",
                        "运维快照",
                        f"{issue.get('company_slug', '')}：{','.join(issue.get('issues', []))}",
                    )
                )
        elif question_type == "daily_summary":
            answer = context.get("editorial_signal", "") or report.get("headline", "") or "今天暂时没有足够高价值的内容被保留下来。"
        else:
            answer = "我会基于日报、跨日观察、专题跟踪和主题档案来回答。你可以直接追问主题、公司、时间线或状态判断。"

        return finalize_answer_payload(
            answer=answer,
            question_type=question_type,
            resolved_theme=primary_theme,
            resolved_company=entity if question_type in {"company_focus", "company_position"} else "",
            sources_used=sources_used,
            evidence_items=evidence_items,
            follow_up_suggestions=follow_up_suggestions_for(
                question_type,
                primary_theme,
                context.get("company_positions", {}),
                entity,
            ),
            mode_used="rule",
        )

    def _generate_llm_answer(self, context: dict, rule_answer: dict, history: list[dict] | None = None) -> dict:
        payload = self.client.generate_json(
            instructions=(
                "你是科技日报的研究助理。你必须遵守给定的项目内 research skill。"
                "你只能基于给定的日报结构化知识层回答，不能引入外部事实。"
                "优先依据 selected_context 回答，先给判断，再给 1-2 个依据，中文自然，避免模板腔。"
            ),
            input_text=(
                f"项目内 skill：\n{context.get('research_skill_text', '')}\n"
                f"知识源说明：\n{context.get('knowledge_sources_text', '')}\n"
                f"问题模式说明：\n{context.get('question_patterns_text', '')}\n"
                f"用户问题：{context.get('question', '')}\n"
                f"最近会话：{trim_history(history)}\n"
                f"问题类型：{rule_answer['question_type']}\n"
                f"优先来源：{context.get('preferred_sources', [])}\n"
                f"实际选中来源：{context.get('selected_sources', [])}\n"
                f"规则回答：{rule_answer['answer']}\n"
                f"选中上下文：{context.get('selected_context', {})}\n"
                f"补充上下文：{context}\n"
            ),
            schema_name="runtime_research_answer",
            schema={
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "evidence_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "label": {"type": "string"},
                                "detail": {"type": "string"},
                                "reference": {"type": "string"},
                            },
                            "required": ["source", "label", "detail", "reference"],
                            "additionalProperties": False,
                        },
                    },
                    "evidence_points": {"type": "array", "items": {"type": "string"}},
                    "follow_up_suggestions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["answer", "evidence_points", "follow_up_suggestions"],
                "additionalProperties": False,
            },
        )
        return {
            "answer": (payload.get("answer") or "").strip(),
            "evidence_items": payload.get("evidence_items") or [],
            "evidence_points": payload.get("evidence_points") or [],
            "follow_up_suggestions": payload.get("follow_up_suggestions") or [],
            "mode_used": "llm",
        }
