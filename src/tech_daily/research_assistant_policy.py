from __future__ import annotations

from collections.abc import Iterable


def build_evidence_item(source: str, label: str, detail: str, bucket: str = "report_basis") -> dict:
    reference = {
        "theme_dossier.json": "theme-dossier",
        "theme_tracking_brief.json": "theme-tracking",
        "cross_day_intel_brief.json": "cross-day-brief",
        "health_snapshot.json": "health-snapshot",
        "report.json": "daily-report",
        "model_reasoning": "model-judgment",
        "general_knowledge": "general-knowledge",
    }.get(source, "knowledge-layer")
    return {
        "source": source,
        "label": label,
        "detail": detail,
        "reference": reference,
        "bucket": bucket,
    }


def build_answer_note(grounding_mode: str) -> str:
    if grounding_mode == "hybrid":
        return "这部分判断结合了当前日报内容与模型推断。"
    if grounding_mode == "general":
        return "这部分回答不直接来自当前日报，仅供参考。"
    return ""


def build_theme_state_answer(*, primary_theme: str, theme_state: str, summary: str, tracking_decision: str) -> str:
    return f"{primary_theme or '这个主题'} 当前处于 {theme_state or '观察期'}。{summary} {tracking_decision}".strip()


def build_company_position_answer(*, primary_theme: str, company: str, position: str, tracking_decision: str) -> str:
    resolved_position = position or "持续参与但位置尚未完全稳定"
    return f"{company} 在 {primary_theme or '当前主专题'} 里目前更偏向 {resolved_position}。{tracking_decision}".strip()


def build_timeline_focus_answer(*, company: str, title: str, why_it_matters: str) -> str:
    return f"最近几天最关键的时间线信号来自 {company or '相关公司'} 的“{title or '代表事件'}”。{timeline_explanation(why_it_matters)}".strip()


def timeline_explanation(detail: str) -> str:
    if not detail:
        return ""
    detail = detail.strip()
    if detail.endswith(("。", "！", "？")):
        return detail
    return f"{detail}。"


def follow_up_suggestions_for(
    question_type: str,
    primary_theme: str,
    company_positions: dict | None = None,
    company: str = "",
) -> list[str]:
    company_positions = company_positions or {}
    if question_type == "company_position" and company:
        return [
            f"{company} 为什么会处在这个位置？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            f"{primary_theme or '这个专题'} 值得继续跟踪吗？",
        ]
    if question_type == "theme_state":
        return [
            "为什么不是 active？",
            "最近几天关键时间线说明了什么？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
        ]
    if question_type == "timeline_focus":
        return [
            f"{primary_theme or '这个主专题'} 现在怎么理解？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
            "这个专题值得继续看吗？",
        ]
    if question_type == "dossier_summary":
        return [
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
        ]
    return [
        "这个主专题现在怎么理解？",
        "最近几天关键时间线说明了什么？",
        "现在哪些信源还有问题？",
    ]


def summarize_block_text(text: str, max_length: int = 90) -> str:
    trimmed = (text or "").strip()
    if not trimmed:
        return ""
    if len(trimmed) <= max_length:
        return trimmed
    return f"{trimmed[: max_length - 1].rstrip()}…"


def evidence_label_for_block(block: dict) -> str:
    kind = block.get("kind", "")
    if kind in {"headline", "editorial_signal", "theme_summary"}:
        return "核心判断"
    if kind in {"company_summary", "company_position"}:
        return "公司位置"
    if kind in {"timeline_event", "timeline_highlight"}:
        return "关键时间线"
    if kind in {"tracking_decision", "theme_state", "operator_brief"}:
        return "状态判断"
    if kind == "tool_result":
        return "本地工具结果"
    if kind == "entry":
        return "日报条目"
    return "日报依据"


def build_evidence_item_from_block(block: dict, bucket: str = "report_basis") -> dict:
    source = block.get("source", "knowledge-layer")
    detail = summarize_block_text(block.get("text", ""))
    return build_evidence_item(source, evidence_label_for_block(block), detail, bucket)


def build_evidence_items_from_blocks(blocks: Iterable[dict], bucket: str = "report_basis", limit: int = 3) -> list[dict]:
    items: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks:
        key = (block.get("source", ""), block.get("block_id", ""))
        if key in seen:
            continue
        seen.add(key)
        item = build_evidence_item_from_block(block, bucket=bucket)
        if item.get("detail"):
            items.append(item)
        if len(items) >= limit:
            break
    return items


def follow_up_suggestions_for_scope(
    *,
    question_scope: str,
    explanation_dimension: str,
    primary_theme: str,
    company_positions: dict | None = None,
    company: str = "",
    needs_general_knowledge: bool = False,
) -> list[str]:
    company_positions = company_positions or {}
    if question_scope == "company" and company:
        return [
            f"{company} 为什么会处在这个位置？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            f"{primary_theme or '这个专题'} 值得继续跟踪吗？",
        ]
    if question_scope == "theme" and explanation_dimension == "evolution":
        return [
            f"{primary_theme or '这个主专题'} 现在怎么理解？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
            "为什么这个主题还值得继续跟踪？",
        ]
    if question_scope == "theme":
        return [
            "为什么现在还值得继续跟踪？",
            "最近几天关键时间线说明了什么？",
            f"{next(iter(company_positions.keys()), 'OpenAI')} 在这个专题里处于什么位置？",
        ]
    if question_scope == "ops":
        return [
            "现在哪些信源还有问题？",
            "最近恢复的公司有哪些？",
            "如果我现在重新生成日报，会发生什么？",
        ]
    if needs_general_knowledge or question_scope == "general":
        return [
            "如果结合今天的日报内容再看，会得出什么判断？",
            "这和当前主专题有什么关系？",
            "今天的日报里有没有相关公司动作？",
        ]
    return [
        "今天最值得关注什么？",
        "这个主专题现在怎么理解？",
        "最近几天关键时间线说明了什么？",
    ]


def legacy_scope_defaults(question_type: str) -> tuple[str, str]:
    if question_type in {"dossier_summary", "theme_state", "theme_focus"}:
        return "theme", "judgment"
    if question_type == "timeline_focus":
        return "theme", "evolution"
    if question_type in {"company_position", "company_focus"}:
        return "company", "comparison"
    if question_type == "ops_status":
        return "ops", "evidence"
    if question_type in {"general_explainer", "out_of_scope"}:
        return "general", "explanation"
    return "report", "judgment"


def build_runtime_answer_frame(context: dict) -> dict:
    understanding = context.get("question_understanding", {}) or {}
    question_type = understanding.get("question_type") or context.get("question_type", "out_of_scope")
    question_scope = understanding.get("question_scope") or context.get("question_scope", "report")
    explanation_dimension = understanding.get("explanation_dimension") or context.get("explanation_dimension", "judgment")
    if question_scope == "report" and explanation_dimension == "judgment":
        question_scope, explanation_dimension = legacy_scope_defaults(question_type)
    requested_tool = understanding.get("requested_tool", "")
    primary_theme = context.get("primary_theme", "")
    entity = context.get("entity", "") or understanding.get("resolved_company", "")
    grounding_mode = context.get("grounding_mode", "grounded")
    tool_result = context.get("tool_result", {}) or {}
    selected_blocks = context.get("selected_blocks", []) or []
    top_block = selected_blocks[0] if selected_blocks else {}
    top_block_summary = summarize_block_text(top_block.get("text", ""))
    if requested_tool or tool_result.get("status") == "ok":
        answer_goal = "先交代工具执行结果，再说明这对当前日报或研究判断意味着什么。"
    elif question_scope == "company":
        answer_goal = "优先解释目标公司在当前主专题、日报或档案里的位置与动作，再补一句为什么这件事重要。"
    elif question_scope == "theme":
        answer_goal = "优先给出主题判断，再结合时间线、状态或跟踪决策解释为什么。"
    elif question_scope == "ops":
        answer_goal = "优先说明当前系统/信源状态，再给出最重要的运行诊断。"
    elif question_scope == "general":
        answer_goal = "如果日报依据不足，可以直接回答通用知识，但要自然区分日报依据与一般性说明。"
    else:
        answer_goal = "优先回答今天的情报主线，再结合最相关的日报证据块解释。"
    return {
        "question_scope": question_scope,
        "explanation_dimension": explanation_dimension,
        "requested_tool": requested_tool,
        "primary_theme": primary_theme,
        "entity": entity,
        "grounding_mode": grounding_mode,
        "top_block_summary": top_block_summary,
        "answer_goal": answer_goal,
        "note_policy": build_answer_note(grounding_mode),
    }


def build_rule_fallback_answer(context: dict) -> str:
    understanding = context.get("question_understanding", {}) or {}
    frame = build_runtime_answer_frame(context)
    selected_blocks = context.get("selected_blocks", []) or []
    selected_summaries = [summarize_block_text(block.get("text", "")) for block in selected_blocks[:2] if block.get("text")]
    tool_result = context.get("tool_result", {}) or {}
    primary_theme = context.get("primary_theme", "")
    entity = frame["entity"]
    question_scope = frame["question_scope"]
    explanation_dimension = frame["explanation_dimension"]
    tracking_decision = (context.get("tracking_decision", "") or "").strip()
    theme_state = (context.get("theme_state", "") or "").strip()
    operator_brief = (context.get("operator_brief", "") or "").strip()
    editorial_signal = (context.get("editorial_signal", "") or "").strip()
    report_headline = (context.get("report_headline", "") or "").strip()
    company_positions = context.get("company_positions", {}) or {}

    if tool_result.get("status") == "ok":
        summary = tool_result.get("summary", "") or "工具执行已完成。"
        if selected_summaries:
            return f"{summary} 目前最相关的日报信号是：{selected_summaries[0]}".strip()
        return summary

    if question_scope == "ops":
        if operator_brief:
            return operator_brief
        if selected_summaries:
            return f"当前最值得先看的运行状态是：{selected_summaries[0]}"
        return "当前没有额外运维提示。"

    if question_scope == "company" and entity:
        position = company_positions.get(entity, "").strip()
        if position:
            return f"{entity} 在 {primary_theme or '当前主专题'} 里目前更偏向 {position}。{tracking_decision}".strip()
        if selected_summaries:
            return f"如果只看当前日报与专题材料，{entity} 最相关的信号是：{selected_summaries[0]}"
        return f"当前日报里还没有足够材料解释 {entity} 在这个专题里的位置。"

    if question_scope == "theme":
        state_text = f"当前处于 {theme_state}。" if theme_state else ""
        if selected_summaries:
            if explanation_dimension == "evolution":
                return f"{primary_theme or '当前主专题'} 最近几天最关键的演化信号是：{selected_summaries[0]}"
            decision_text = tracking_decision or ""
            return f"{primary_theme or '当前主专题'} {state_text}最值得先看的依据是：{selected_summaries[0]} {decision_text}".strip()
        if theme_state or tracking_decision:
            return f"{primary_theme or '当前主专题'} 当前更像是在持续形成过程中。{state_text} {tracking_decision}".strip()
        return f"{primary_theme or '当前主专题'} 还需要更多日报材料来支撑进一步判断。"

    if question_scope == "report":
        if editorial_signal:
            return editorial_signal
        if report_headline:
            return report_headline
        if selected_summaries:
            return f"今天最值得先看的信号是：{selected_summaries[0]}"
        return "今天暂时没有足够高价值的内容被保留下来。"

    if understanding.get("needs_general_knowledge") or question_scope == "general":
        if selected_summaries:
            return f"当前日报里和这个问题最接近的线索是：{selected_summaries[0]}。如果你愿意，我也可以先给一个更通用的解释。"
        return "当前日报知识层里没有直接覆盖这个问题。我可以先给你一个通用解释；如果你愿意，也可以再收回到今天的主题、公司或专题档案上。"

    if selected_summaries:
        return f"就当前日报知识层看，最相关的线索是：{selected_summaries[0]}"
    return "我会先按当前日报知识层和已有研究上下文来理解这个问题；如果日报依据不够，我会补充一个更通用的解释。"


def finalize_answer_payload(
    *,
    answer: str,
    question_type: str,
    resolved_theme: str,
    resolved_company: str,
    sources_used: list[str],
    evidence_items: list[dict],
    follow_up_suggestions: list[str],
    mode_used: str,
    grounding_mode: str = "grounded",
    answer_note: str = "",
) -> dict:
    evidence_points = [item["detail"] for item in evidence_items if item.get("detail")]
    return {
        "answer": answer.strip(),
        "answer_note": answer_note,
        "question_type": question_type,
        "resolved_theme": resolved_theme,
        "resolved_company": resolved_company,
        "sources_used": sources_used,
        "evidence_items": evidence_items,
        "evidence_points": evidence_points,
        "follow_up_suggestions": follow_up_suggestions,
        "mode_used": mode_used,
        "grounding_mode": grounding_mode,
    }
