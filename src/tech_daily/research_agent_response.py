from __future__ import annotations

from .chat_agent_memory import resolve_follow_up_route, trim_history
from .llm_client import LLMClient, LLMClientError
from .research_assistant_policy import (
    build_evidence_item,
    build_answer_note,
    build_evidence_items_from_blocks,
    build_rule_fallback_answer,
    build_runtime_answer_frame,
    finalize_answer_payload,
    follow_up_suggestions_for_scope,
    legacy_scope_defaults,
)


def _normalize_answer_note(note: str, grounding_mode: str) -> str:
    normalized = (note or "").strip()
    if normalized in {"grounded", "hybrid", "general"}:
        return build_answer_note(normalized)
    if not normalized:
        return build_answer_note(grounding_mode)
    return normalized


def _normalize_evidence_items(items: list[dict], context: dict) -> list[dict]:
    allowed_sources = set(context.get("selected_sources", []) or [])
    tool_result = context.get("tool_result", {}) or {}
    if tool_result.get("status") == "ok":
        allowed_sources.add(f"{tool_result.get('tool_name', 'tool')}.tool")
    if not allowed_sources and context.get("grounding_mode") == "general":
        return []
    normalized: list[dict] = []
    for item in items or []:
        source = item.get("source", "")
        if allowed_sources and source and source not in allowed_sources:
            continue
        normalized.append(item)
    return normalized


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
        normalized_items = _normalize_evidence_items(llm_answer.get("evidence_items") or [], context)
        normalized_note = _normalize_answer_note(llm_answer.get("answer_note", ""), llm_answer.get("grounding_mode") or rule_answer.get("grounding_mode", "grounded"))
        return {
            **rule_answer,
            "answer": llm_answer["answer"],
            "evidence_items": normalized_items or rule_answer["evidence_items"],
            "evidence_points": [item.get("detail", "") for item in normalized_items if item.get("detail")] or rule_answer["evidence_points"],
            "follow_up_suggestions": llm_answer.get("follow_up_suggestions") or rule_answer["follow_up_suggestions"],
            "answer_note": normalized_note,
            "grounding_mode": llm_answer.get("grounding_mode") or rule_answer.get("grounding_mode", "grounded"),
            "mode_used": llm_answer.get("mode_used", "llm"),
        }

    def _rule_answer(self, context: dict, history: list[dict] | None = None) -> dict:
        original_question_type = context.get("question_type", "out_of_scope")
        question_type = original_question_type
        primary_theme = context.get("primary_theme", "")
        entity = context.get("entity", "")
        question = context.get("question", "")
        grounding_mode = context.get("grounding_mode", "grounded")
        question_understanding = context.get("question_understanding", {}) or {}
        sources_used: list[str] = [source for source in [context.get("primary_source", "")] if source]
        selected_blocks = context.get("selected_blocks", []) or []

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
            resolved_scope, resolved_dimension = legacy_scope_defaults(question_type)
            question_understanding = {
                **question_understanding,
                "question_scope": resolved_scope,
                "explanation_dimension": resolved_dimension,
            }
        resolved_understanding = {
            **question_understanding,
            "question_type": question_type,
            "resolved_company": entity if entity else question_understanding.get("resolved_company", ""),
        }
        local_context = {
            **context,
            "question_understanding": resolved_understanding,
        }
        answer = build_rule_fallback_answer(local_context)
        theme_state = (local_context.get("theme_state") or "").strip()
        evidence_items = build_evidence_items_from_blocks(selected_blocks)
        if question_type == "theme_state" and theme_state and not any(
            item.get("label") in {"状态判断", "专题档案"} and theme_state in item.get("detail", "")
            for item in evidence_items
        ):
            evidence_items.insert(
                0,
                build_evidence_item(
                    "theme_dossier.json",
                    "专题档案",
                    f"当前主题阶段为 {theme_state}。",
                ),
            )
        frame = build_runtime_answer_frame(local_context)

        return finalize_answer_payload(
            answer=answer,
            answer_note=build_answer_note(grounding_mode),
            question_type=question_type,
            resolved_theme=primary_theme,
            resolved_company=entity if frame["question_scope"] == "company" else "",
            sources_used=sources_used,
            evidence_items=evidence_items,
            follow_up_suggestions=follow_up_suggestions_for_scope(
                question_scope=frame["question_scope"],
                explanation_dimension=frame["explanation_dimension"],
                primary_theme=primary_theme,
                company_positions=context.get("company_positions", {}),
                company=entity,
                needs_general_knowledge=bool(resolved_understanding.get("needs_general_knowledge")),
            ),
            mode_used="rule",
            grounding_mode=grounding_mode,
        )

    def _generate_llm_answer(self, context: dict, rule_answer: dict, history: list[dict] | None = None) -> dict:
        grounding_mode = context.get("grounding_mode", "grounded")
        tool_result = context.get("tool_result", {}) or {}
        answer_frame = build_runtime_answer_frame(context)
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
                "你的默认工作方式是：LLM 主导回答组织，RAG 负责 grounding，规则回答只作为兜底基线。"
                "先给判断，再给 1-2 个依据，中文自然，避免模板腔，不要机械复述问题类型。"
                "日报知识层是 grounding / evidence layer，不是唯一答案来源。"
                "当日报证据不足时，可以给出一般性的模型解释，但不要伪装成日报依据。"
            ),
            input_text=(
                f"项目内 skill：\n{context.get('research_skill_text', '')}\n"
                f"知识源说明：\n{context.get('knowledge_sources_text', '')}\n"
                f"问题模式说明：\n{context.get('question_patterns_text', '')}\n"
                f"RAG 与边界控制说明：\n{context.get('rag_and_boundaries_text', '')}\n"
                f"可用工具：\n{context.get('available_tools_text', '')}\n"
                f"已执行工具结果：{tool_result}\n"
                f"用户问题：{context.get('question', '')}\n"
                f"最近会话：{trim_history(history)}\n"
                f"问题理解：{question_understanding}\n"
                f"回答框架：{answer_frame}\n"
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
            "answer_note": _normalize_answer_note(payload.get("answer_note", ""), grounding_mode),
            "grounding_mode": grounding_mode,
            "mode_used": "llm",
        }
