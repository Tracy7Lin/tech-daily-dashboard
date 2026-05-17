from __future__ import annotations

from .chat_agent_memory import resolve_follow_up_route, trim_history
from .llm_client import LLMClient, LLMClientError
from .chat_agent_analysis import classify_chat_question
from .chat_agent_input import ChatAgentInputs


def _evidence_item(source: str, label: str, detail: str) -> dict:
    return {
        "source": source,
        "label": label,
        "detail": detail,
    }


def _select_placeholder_status(statuses: list[dict]) -> dict | None:
    if not statuses:
        return None
    statuses = sorted(
        statuses,
        key=lambda status: (
            0 if not status.get("ok", True) else 1,
            status.get("final_included_count", 0),
            status.get("date_matched_count", 0),
            status.get("kept_count", 0),
            status.get("fetched_count", 0),
        ),
    )
    return statuses[0]


def _is_stable_no_news_status(status: dict) -> bool:
    return (
        status.get("ok", False)
        and status.get("fetched_count", 0) > 0
        and status.get("kept_count", 0) > 0
        and status.get("date_matched_count", 0) == 0
        and status.get("final_included_count", 0) == 0
    )


def _is_stable_filtered_status(status: dict) -> bool:
    return (
        status.get("ok", False)
        and status.get("date_matched_count", 0) > 0
        and status.get("final_included_count", 0) == 0
    )


def _placeholder_reason(status: dict) -> str:
    company_name = status.get("company_name", "")
    source_label = status.get("source_label", "")
    message = status.get("message", "")
    lowered = message.lower()

    if "http_error:403" in lowered and company_name.lower() == "tesla":
        return "Tesla 官方新闻入口当前持续拒绝抓取请求，先保留占位，后续再评估更稳的官方接入方式。"
    if status.get("fetched_count", 0) == 0 and company_name.lower() == "xiaomi":
        return "Xiaomi Global Discover 当前以动态渲染为主，静态抓取器尚未拿到稳定文章链接，先保留占位。"
    if not status.get("ok", True):
        return f"{company_name or source_label} 当前抓取异常，建议优先检查官方入口是否可访问。"
    if status.get("fetched_count", 0) == 0:
        return f"{company_name or source_label} 当前没有抓到稳定条目，先保留占位，后续再继续调优信源。"
    return f"{company_name or source_label} 今天没有形成可发布动态，建议结合源状态继续观察。"


def _build_company_answer(company_name: str, entries: list[dict], statuses: list[dict]) -> str:
    latest_title = entries[0].get("raw", {}).get("title", "") if entries else ""
    if entries:
        return f"{company_name} 最近几天仍有动作，当前最值得看的更新是“{latest_title}”。"
    status = _select_placeholder_status(statuses)
    if status is None:
        return f"{company_name} 今天没有保留下可发布的动态。"
    if _is_stable_no_news_status(status):
        return f"{company_name} 官方信源抓取正常，但今天没有落在日报日期范围内的有效动态。"
    if _is_stable_filtered_status(status):
        return f"{company_name} 官方信源抓取正常，也抓到了同日内容，但今天没有保留下可发布条目。"
    return f"{company_name} 信源暂未稳定。{_placeholder_reason(status)}"


def build_chat_context(inputs: ChatAgentInputs) -> dict:
    company_reports = inputs.report.get("company_reports", [])
    source_statuses = inputs.report.get("source_statuses", [])
    statuses_by_company = {}
    for status in source_statuses:
        statuses_by_company.setdefault(status.get("company_slug", ""), []).append(status)
    company_answers = {}
    company_names = []
    for report in company_reports:
        company_slug = report.get("company_slug", "")
        company_name = report.get("company_name", "")
        if not company_name:
            continue
        company_names.append(company_name)
        entries = report.get("entries", [])
        company_answers[company_name.lower()] = _build_company_answer(
            company_name,
            entries,
            statuses_by_company.get(company_slug, []),
        )

    primary_theme = inputs.theme_tracking_brief.get("primary_theme", "")
    theme_summary = inputs.theme_tracking_brief.get("theme_summary", "") or "当前还没有形成明确主专题。"
    theme_evolution = inputs.theme_tracking_brief.get("theme_evolution", "")
    participating_companies = inputs.theme_tracking_brief.get("participating_companies", [])
    theme_dossier = {
        "primary_theme": inputs.theme_dossier_brief.get("primary_theme", ""),
        "theme_definition": inputs.theme_dossier_brief.get("theme_definition", ""),
        "theme_state": inputs.theme_dossier_brief.get("theme_state", ""),
        "theme_summary": inputs.theme_dossier_brief.get("theme_summary", ""),
        "company_positions": inputs.theme_dossier_brief.get("company_positions", {}),
        "timeline_events": inputs.theme_dossier_brief.get("timeline_events", []),
        "tracking_decision": inputs.theme_dossier_brief.get("tracking_decision", ""),
        "next_day_focus": inputs.theme_dossier_brief.get("next_day_focus", []),
    }
    ops_brief = inputs.health_snapshot.get("ops_status_analysis", {}).get("operator_brief", "") or "当前没有额外运维提示。"
    high_priority = [issue.get("company_slug", "") for issue in inputs.health_snapshot.get("high_priority_runtime_issues", [])]

    return {
        "report_date": inputs.report_date,
        "daily_summary": {
            "answer": inputs.daily_brief.get("editorial_signal")
            or inputs.report.get("headline")
            or "今天暂时没有足够高价值的内容被保留下来。",
        },
        "theme_tracking": {
            "primary_theme": primary_theme,
            "answer": f"{theme_summary} {theme_evolution}".strip(),
            "participating_companies": participating_companies,
        },
        "theme_dossier": theme_dossier,
        "ops_status": {
            "answer": ops_brief,
            "high_priority": high_priority,
        },
        "company_answers": company_answers,
        "companies": company_names,
        "quick_questions": [
            "今天最值得关注什么？",
            "这个主专题现在怎么理解？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            "现在哪些信源还有问题？",
        ],
        "follow_up_suggestions": [
            "OpenAI 最近几天在做什么？",
            "这个主专题现在怎么理解？",
            "为什么现在是 emerging？",
            "最近几天关键时间线说明了什么？",
            "现在哪些信源还有问题？",
        ],
        "runtime_chat": {
            "endpoint": "/api/chat",
        },
        "mode_used": "rule",
    }


def answer_chat_question(question: str, context: dict, route: tuple[str, str] | None = None) -> dict:
    question_type, entity = route or classify_chat_question(
        question,
        context.get("companies", []),
        context.get("theme_tracking", {}).get("primary_theme", ""),
    )

    evidence_points: list[str] = []
    evidence_items: list[dict] = []
    sources_used: list[str] = []

    def add_evidence(source: str, label: str, detail: str) -> None:
        if not detail:
            return
        evidence_points.append(detail)
        evidence_items.append(_evidence_item(source, label, detail))
        if source not in sources_used:
            sources_used.append(source)

    if question_type == "daily_summary":
        answer = context.get("daily_summary", {}).get("answer", "今天还没有可直接回答的日报摘要。")
        primary_theme = context.get("theme_tracking", {}).get("primary_theme", "")
        if primary_theme:
            add_evidence("theme_tracking_brief.json", "专题跟踪", f"当前主专题是 {primary_theme}。")
        ops_answer = context.get("ops_status", {}).get("answer", "")
        if ops_answer:
            add_evidence("health_snapshot.json", "运维快照", ops_answer)
    elif question_type == "company_focus":
        answer = context.get("company_answers", {}).get(
            entity.lower(),
            "当前还没有足够明确的公司上下文，建议直接问某家公司最近几天在做什么。",
        )
        dossier = context.get("theme_dossier", {})
        if dossier.get("primary_theme"):
            add_evidence("theme_dossier.json", "专题档案", f"当前主专题是 {dossier.get('primary_theme')}。")
        if entity.lower() in context.get("company_answers", {}):
            add_evidence("report.json", "公司日报", context["company_answers"][entity.lower()])
    elif question_type == "company_position":
        dossier = context.get("theme_dossier", {})
        primary_theme = dossier.get("primary_theme", "") or context.get("theme_tracking", {}).get("primary_theme", "")
        position = dossier.get("company_positions", {}).get(entity, "")
        if position:
            answer = f"{entity} 在 {primary_theme} 这个专题里当前更偏向 {position}。这说明它的切入点已经开始稳定下来。"
            add_evidence("theme_dossier.json", "专题档案", f"{entity} 在 dossier 中的当前位置是：{position}。")
            if dossier.get("theme_state"):
                add_evidence("theme_dossier.json", "专题档案", f"当前主题阶段为 {dossier.get('theme_state')}。")
        else:
            answer = f"当前 dossier 里还没有足够明确地定义 {entity} 在这个专题中的位置。"
    elif question_type == "theme_focus":
        answer = context.get("theme_tracking", {}).get("answer", "当前还没有形成明确主专题。")
        theme_tracking = context.get("theme_tracking", {})
        if theme_tracking.get("primary_theme"):
            add_evidence(
                "theme_tracking_brief.json",
                "专题跟踪",
                f"最近几天持续聚焦的主专题是 {theme_tracking.get('primary_theme')}。",
            )
        if theme_tracking.get("participating_companies"):
            add_evidence(
                "theme_tracking_brief.json",
                "专题跟踪",
                f"当前参与公司包括：{'、'.join(theme_tracking.get('participating_companies', []))}。",
            )
    elif question_type == "dossier_summary":
        dossier = context.get("theme_dossier", {})
        primary_theme = dossier.get("primary_theme", "") or context.get("theme_tracking", {}).get("primary_theme", "")
        theme_definition = dossier.get("theme_definition", "")
        tracking_decision = dossier.get("tracking_decision", "")
        if primary_theme:
            answer = f"{primary_theme} 目前可以理解为：{theme_definition or context.get('theme_tracking', {}).get('answer', '')} {tracking_decision}".strip()
            if dossier.get("theme_state"):
                add_evidence("theme_dossier.json", "专题档案", f"当前主题阶段是 {dossier.get('theme_state')}。")
            if dossier.get("company_positions"):
                add_evidence(
                    "theme_dossier.json",
                    "专题档案",
                    f"当前持续参与公司包括：{'、'.join(dossier.get('company_positions', {}).keys())}。",
                )
        else:
            answer = "当前还没有形成足够清晰的专题档案。"
    elif question_type == "theme_state":
        dossier = context.get("theme_dossier", {})
        state = dossier.get("theme_state", "")
        summary = dossier.get("theme_summary", "")
        decision = dossier.get("tracking_decision", "")
        if state:
            answer = f"这个主题当前处于 {state}。{summary} {decision}".strip()
            add_evidence("theme_dossier.json", "专题档案", f"当前 dossier 状态机结果是 {state}。")
            if summary:
                add_evidence("cross_day_intel_brief.json", "跨日观察", summary)
        else:
            answer = "当前还没有足够明确的专题阶段判断。"
    elif question_type == "timeline_focus":
        dossier = context.get("theme_dossier", {})
        timeline = dossier.get("timeline_events", [])
        if timeline:
            lead = timeline[-1]
            answer = (
                f"最近几天最关键的时间线信号来自 {lead.get('company', '相关公司')} 的“{lead.get('title', '代表事件')}”。"
                f"{lead.get('why_it_matters', '')}"
            )
            add_evidence(
                "theme_dossier.json",
                "主题时间线",
                f"{lead.get('date', '')} · {lead.get('company', '相关公司')} · {lead.get('title', '代表事件')}",
            )
            if lead.get("why_it_matters"):
                add_evidence("theme_dossier.json", "主题时间线", lead.get("why_it_matters"))
        else:
            answer = "当前 dossier 里还没有足够明确的关键时间线。"
    elif question_type == "ops_status":
        answer = context.get("ops_status", {}).get("answer", "当前没有额外运维提示。")
        for company_slug in context.get("ops_status", {}).get("high_priority", []):
            add_evidence("health_snapshot.json", "运维快照", f"高优先级信源问题：{company_slug}")
    else:
        answer = "当前问答主要基于今日日报、跨日观察、专题跟踪和运维状态。你可以继续问今天重点、某家公司、主专题或信源状态。"

    return {
        "answer": answer,
        "question_type": question_type,
        "resolved_theme": context.get("theme_dossier", {}).get("primary_theme", "") or context.get("theme_tracking", {}).get("primary_theme", ""),
        "resolved_company": entity if question_type in {"company_focus", "company_position"} else "",
        "sources_used": sources_used or ["report.json"],
        "evidence_items": evidence_items[:3],
        "evidence_points": evidence_points[:3],
        "follow_up_suggestions": context.get("follow_up_suggestions", []),
        "mode_used": context.get("mode_used", "rule"),
    }


def build_chat_response_bank(context: dict, responder: "ChatAgentResponder") -> dict:
    primary_theme = context.get("theme_tracking", {}).get("primary_theme", "")
    company_bank = {}
    for company in context.get("companies", []):
        company_bank[company.lower()] = responder.answer(f"{company} 最近几天在做什么？", context)

    return {
        "daily_summary": responder.answer("今天最值得关注什么？", context),
        "theme_focus": responder.answer(
            f"为什么今天的主专题是{primary_theme or '这个主题'}？",
            context,
        ),
        "dossier_summary": responder.answer("这个主专题现在怎么理解？", context),
        "theme_state": responder.answer("为什么现在是 emerging？", context),
        "timeline_focus": responder.answer("最近几天关键时间线说明了什么？", context),
        "ops_status": responder.answer("现在哪些信源还有问题？", context),
        "company_focus": company_bank,
        "company_position_answers": {
            company.lower(): responder.answer(f"{company} 在这个专题里处于什么位置？", context)
            for company in context.get("companies", [])
        },
        "out_of_scope": responder.answer("我还可以问别的吗？", context),
    }


class ChatAgentResponder:
    def __init__(self, mode: str = "rule", client: LLMClient | None = None) -> None:
        self.mode = mode
        self.client = client

    def answer(self, question: str, context: dict, history: list[dict] | None = None) -> dict:
        route = resolve_follow_up_route(
            question,
            history,
            context.get("companies", []),
            context.get("theme_tracking", {}).get("primary_theme", ""),
        )
        rule_answer = answer_chat_question(question, context, route=route)
        if self.mode == "rule":
            return rule_answer
        if self.client is None or not self.client.is_available():
            return rule_answer
        try:
            payload = self.client.generate_json(
                instructions=(
                    "你是科技日报的情报助理。请基于给定上下文回答用户问题。"
                    "回答必须简洁、可信、中文自然，不能引入上下文之外的新事实。"
                    "先给结论，再给 1-2 个依据。"
                ),
                input_text=(
                    f"用户问题：{question}\n"
                    f"最近会话：{trim_history(history)}\n"
                    f"问题类型：{rule_answer['question_type']}\n"
                    f"规则回答：{rule_answer['answer']}\n"
                    f"已有依据：{rule_answer['evidence_points']}\n"
                    f"可用上下文：{context}\n"
                ),
                schema_name="chat_answer_payload",
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
                                },
                                "required": ["source", "label", "detail"],
                                "additionalProperties": False,
                            },
                        },
                        "evidence_points": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "follow_up_suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["answer", "evidence_points", "follow_up_suggestions"],
                    "additionalProperties": False,
                },
            )
        except (LLMClientError, KeyError, TypeError, ValueError):
            return rule_answer

        answer = (payload.get("answer") or "").strip()
        if not answer:
            return rule_answer
        return {
            **rule_answer,
            "answer": answer,
            "evidence_items": payload.get("evidence_items") or rule_answer["evidence_items"],
            "evidence_points": payload.get("evidence_points") or rule_answer["evidence_points"],
            "follow_up_suggestions": payload.get("follow_up_suggestions") or rule_answer["follow_up_suggestions"],
            "mode_used": "llm",
        }
