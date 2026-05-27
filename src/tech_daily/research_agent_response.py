from __future__ import annotations

from .chat_agent_memory import resolve_follow_up_route, trim_history
from .llm_client import LLMClient, LLMClientError
from .research_assistant_policy import (
    build_answer_note,
    build_company_position_answer,
    build_evidence_item,
    build_theme_state_answer,
    build_timeline_focus_answer,
    finalize_answer_payload,
    follow_up_suggestions_for,
)


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
            "answer_note": llm_answer.get("answer_note") or rule_answer.get("answer_note", ""),
            "grounding_mode": llm_answer.get("grounding_mode") or rule_answer.get("grounding_mode", "grounded"),
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
        grounding_mode = context.get("grounding_mode", "grounded")
        evidence_items: list[dict] = []
        sources_used: list[str] = [source for source in [context.get("primary_source", "")] if source]

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
                evidence_items.append(build_evidence_item("theme_dossier.json", "专题档案", f"当前主题阶段为 {theme_state}。", "report_basis"))
        elif question_type == "theme_state":
            summary = dossier.get("theme_summary", "") or context.get("cross_day_intel_brief", {}).get("editorial_signal", "")
            answer = build_theme_state_answer(
                primary_theme=primary_theme,
                theme_state=theme_state or "观察期",
                summary=f"因为它已经形成持续信号，但还没有完全稳定。{summary}".strip(),
                tracking_decision=tracking_decision,
            )
            evidence_items.append(build_evidence_item("theme_dossier.json", "专题档案", f"状态机判断为 {theme_state or '观察期'}。", "report_basis"))
        elif question_type == "company_position":
            position = company_positions.get(entity, "")
            answer = build_company_position_answer(
                primary_theme=primary_theme,
                company=entity,
                position=position,
                tracking_decision=tracking_decision,
            )
            evidence_items.append(build_evidence_item("theme_dossier.json", "公司位置", f"{entity} 的 dossier 位置是：{position or '待进一步明确'}。", "report_basis"))
        elif question_type == "timeline_focus":
            lead = timeline_events[-1] if timeline_events else {}
            title = lead.get("title", "近期代表事件")
            why = lead.get("why_it_matters", "")
            company = lead.get("company", "相关公司")
            answer = build_timeline_focus_answer(company=company, title=title, why_it_matters=why)
            evidence_items.append(build_evidence_item("theme_dossier.json", "关键时间线", f"{lead.get('date', '')} · {company} · {title}", "report_basis"))
        elif question_type == "company_focus":
            company_reports = report.get("company_reports", [])
            matched = next((item for item in company_reports if item.get("company_name", "").lower() == entity.lower()), {})
            entries = matched.get("entries", [])
            latest = entries[0].get("raw", {}).get("title", "") if entries else ""
            answer = f"{entity} 最近几天最值得看的动作是“{latest}”。" if latest else f"{entity} 最近几天没有明显的高价值动态被保留。"
            if latest:
                evidence_items.append(build_evidence_item("report.json", "公司动态", latest, "report_basis"))
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
                        "report_basis",
                    )
                )
        elif question_type == "daily_summary":
            answer = context.get("editorial_signal", "") or report.get("headline", "") or "今天暂时没有足够高价值的内容被保留下来。"
        else:
            answer = "当前日报知识层里没有直接覆盖这个问题。我可以先给你一个通用解释，如果你愿意，也可以把问题收回到今天的主题、公司或专题档案上。"

        return finalize_answer_payload(
            answer=answer,
            answer_note=build_answer_note(grounding_mode),
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
            grounding_mode=grounding_mode,
        )

    def _generate_llm_answer(self, context: dict, rule_answer: dict, history: list[dict] | None = None) -> dict:
        grounding_mode = context.get("grounding_mode", "grounded")
        if grounding_mode == "grounded":
            answering_policy = "优先依据 selected_context 和日报证据回答，不要脱离证据层。"
        elif grounding_mode == "hybrid":
            answering_policy = "优先依据 selected_context 回答；若日报证据不足，可以结合模型推断补足解释，但要把补充判断与日报依据区分开。"
        else:
            answering_policy = "如果日报知识层没有直接覆盖，可以基于你的通用知识回答，但要明确说明这部分回答不直接来自当前日报，仅供参考。"
        selected_blocks = context.get("selected_blocks", []) or []
        selected_block_lines = "\n".join(
            f"- [{block.get('source', '')}::{block.get('kind', '')}] {block.get('text', '')}"
            for block in selected_blocks
        )
        question_understanding = context.get("question_understanding", {})
        payload = self.client.generate_json(
            instructions=(
                "你是科技日报的研究助理。你必须遵守给定的项目内 research skill。"
                f"{answering_policy}"
                "先给判断，再给 1-2 个依据，中文自然，避免模板腔。"
                "日报知识层是 grounding / evidence layer，不是唯一答案来源。"
                "当日报证据不足时，可以给出一般性的模型解释，但不要伪装成日报依据。"
            ),
            input_text=(
                f"项目内 skill：\n{context.get('research_skill_text', '')}\n"
                f"知识源说明：\n{context.get('knowledge_sources_text', '')}\n"
                f"问题模式说明：\n{context.get('question_patterns_text', '')}\n"
                f"用户问题：{context.get('question', '')}\n"
                f"最近会话：{trim_history(history)}\n"
                f"问题理解：{question_understanding}\n"
                f"回答模式：{grounding_mode}\n"
                f"优先来源：{context.get('preferred_sources', [])}\n"
                f"实际选中来源：{context.get('selected_sources', [])}\n"
                f"选中证据块：\n{selected_block_lines or '无直接命中的日报证据块'}\n"
                f"选中上下文：{context.get('selected_context', {})}\n"
                f"回退基线：{rule_answer['answer']}\n"
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
                                "bucket": {"type": "string"},
                            },
                            "required": ["source", "label", "detail", "reference", "bucket"],
                            "additionalProperties": False,
                        },
                    },
                    "evidence_points": {"type": "array", "items": {"type": "string"}},
                    "follow_up_suggestions": {"type": "array", "items": {"type": "string"}},
                    "answer_note": {"type": "string"},
                },
                "required": ["answer", "evidence_points", "follow_up_suggestions", "answer_note"],
                "additionalProperties": False,
            },
        )
        return {
            "answer": (payload.get("answer") or "").strip(),
            "evidence_items": payload.get("evidence_items") or [],
            "evidence_points": payload.get("evidence_points") or [],
            "follow_up_suggestions": payload.get("follow_up_suggestions") or [],
            "answer_note": (payload.get("answer_note") or build_answer_note(grounding_mode)).strip(),
            "grounding_mode": grounding_mode,
            "mode_used": "llm",
        }
