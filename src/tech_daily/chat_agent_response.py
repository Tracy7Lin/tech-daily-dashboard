from __future__ import annotations

from .llm_client import LLMClient, LLMClientError
from .chat_agent_analysis import classify_chat_question
from .chat_agent_input import ChatAgentInputs


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
        "ops_status": {
            "answer": ops_brief,
            "high_priority": high_priority,
        },
        "company_answers": company_answers,
        "companies": company_names,
        "quick_questions": [
            "今天最值得关注什么？",
            "为什么今天的主专题是这个？",
            "现在哪些信源还有问题？",
        ],
        "follow_up_suggestions": [
            "OpenAI 最近几天在做什么？",
            "为什么今天的主专题是这个？",
            "现在哪些信源还有问题？",
        ],
        "mode_used": "rule",
    }


def answer_chat_question(question: str, context: dict) -> dict:
    question_type, entity = classify_chat_question(
        question,
        context.get("companies", []),
        context.get("theme_tracking", {}).get("primary_theme", ""),
    )

    if question_type == "daily_summary":
        answer = context.get("daily_summary", {}).get("answer", "今天还没有可直接回答的日报摘要。")
    elif question_type == "company_focus":
        answer = context.get("company_answers", {}).get(
            entity.lower(),
            "当前还没有足够明确的公司上下文，建议直接问某家公司最近几天在做什么。",
        )
    elif question_type == "theme_focus":
        answer = context.get("theme_tracking", {}).get("answer", "当前还没有形成明确主专题。")
    elif question_type == "ops_status":
        answer = context.get("ops_status", {}).get("answer", "当前没有额外运维提示。")
    else:
        answer = "当前问答主要基于今日日报、跨日观察、专题跟踪和运维状态。你可以继续问今天重点、某家公司、主专题或信源状态。"

    return {
        "answer": answer,
        "question_type": question_type,
        "sources_used": [
            "report.json",
            "daily_intel_brief.json",
            "cross_day_intel_brief.json",
            "theme_tracking_brief.json",
            "health_snapshot.json",
        ],
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
        "ops_status": responder.answer("现在哪些信源还有问题？", context),
        "company_focus": company_bank,
        "out_of_scope": responder.answer("我还可以问别的吗？", context),
    }


class ChatAgentResponder:
    def __init__(self, mode: str = "rule", client: LLMClient | None = None) -> None:
        self.mode = mode
        self.client = client

    def answer(self, question: str, context: dict) -> dict:
        rule_answer = answer_chat_question(question, context)
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
                    f"问题类型：{rule_answer['question_type']}\n"
                    f"规则回答：{rule_answer['answer']}\n"
                    f"可用上下文：{context}\n"
                ),
                schema_name="chat_answer_payload",
                schema={
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "follow_up_suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["answer", "follow_up_suggestions"],
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
            "follow_up_suggestions": payload.get("follow_up_suggestions") or rule_answer["follow_up_suggestions"],
            "mode_used": "llm",
        }
