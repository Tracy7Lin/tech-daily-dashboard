from __future__ import annotations

import html
import json
import re
from pathlib import Path
from string import Template

from .archive import load_report_snapshots
from .models import CompanyReport, DailyReport, EnrichedEntry, SourceStatus, TopicCluster
from .paths import TEMPLATES_DIR


def _load_template(name: str) -> Template:
    return Template((TEMPLATES_DIR / name).read_text(encoding="utf-8"))


def _render_page_transition_shell() -> str:
    return (
        "<div class='page-curtain' id='page-curtain' aria-hidden='true'>"
        "<div class='page-curtain-ink'></div>"
        "<div class='page-curtain-accent'></div>"
        "<div class='page-curtain-label'>Tech Intelligence Review</div>"
        "</div>"
        "<script id='page-transition-script'>"
        "(() => {"
        "const curtain = document.getElementById('page-curtain');"
        "if (!curtain) return;"
        "const TRANSITION_MS = 260;"
        "const isInternalDocumentLink = (anchor) => {"
        "  const href = anchor.getAttribute('href') || '';"
        "  if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto:')) return false;"
        "  return href.endsWith('.html') || href.includes('.html?') || href.includes('.html#') || href.startsWith('./') || href.startsWith('../');"
        "};"
        "const reveal = () => {"
        "  curtain.dataset.state = 'revealed';"
        "  document.body.dataset.pageState = 'ready';"
        "};"
        "requestAnimationFrame(() => {"
        "  document.body.dataset.pageState = 'staging';"
        "  window.setTimeout(reveal, 60);"
        "});"
        "document.addEventListener('click', (event) => {"
        "  const anchor = event.target instanceof Element ? event.target.closest('a') : null;"
        "  if (!anchor || !isInternalDocumentLink(anchor)) return;"
        "  if (anchor.target && anchor.target !== '_self') return;"
        "  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;"
        "  event.preventDefault();"
        "  const destination = anchor.href;"
        "  document.body.dataset.pageState = 'leaving';"
        "  curtain.dataset.state = 'covering';"
        "  window.setTimeout(() => { window.location.href = destination; }, TRANSITION_MS);"
        "});"
        "window.addEventListener('pageshow', () => { reveal(); });"
        "})();"
        "</script>"
    )


def _strip_html(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text).split()).strip()


def _truncate(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "item"


def _format_published_at(value: str) -> str:
    if not value:
        return "未知"
    if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
        return value.replace("T", " ").replace("Z", " UTC")
    return value


def _entry_supplement(entry: EnrichedEntry) -> str:
    cleaned = _strip_html(entry.raw.summary)
    if cleaned:
        return _truncate(cleaned, 180)
    return "暂无原文补充说明。"


def _entry_meta(entry: EnrichedEntry) -> str:
    return (
        f"来源：{html.escape(entry.raw.source_label)} | "
        f"发布时间：{html.escape(_format_published_at(entry.raw.published_at))} | "
        f"分类：{html.escape(entry.category)} | "
        f"重要度：{entry.importance} | "
        f"对比角度：{html.escape(entry.comparison_angle)} | "
        f"标签：{html.escape(', '.join(entry.tags))}"
    )


def _render_summary_grid(items: list[tuple[str, str]]) -> str:
    blocks = "".join(
        "<section class='summary-block'>"
        f"<p class='summary-label'>{html.escape(label)}</p>"
        f"<p class='summary-value'>{html.escape(value)}</p>"
        "</section>"
        for label, value in items
        if value
    )
    return f"<div class='modal-summary-grid'>{blocks}</div>" if blocks else ""


def _render_signal_rail(report: DailyReport) -> str:
    active_companies = "、".join(report.active_companies[:4]) or "暂无"
    hottest_topics = " / ".join(report.hottest_topics[:3]) or "暂无"
    signal_cards = [
        ("今日主线", hottest_topics),
        ("活跃公司", active_companies),
        ("日报判断", _truncate(report.headline, 88)),
    ]
    return "".join(
        "<article class='signal-card'>"
        f"<p class='signal-label'>{html.escape(label)}</p>"
        f"<p class='signal-value'>{html.escape(value)}</p>"
        "</article>"
        for label, value in signal_cards
    )


def _statuses_by_company(statuses: list[SourceStatus]) -> dict[str, list[SourceStatus]]:
    grouped: dict[str, list[SourceStatus]] = {}
    for status in statuses:
        grouped.setdefault(status.company_slug, []).append(status)
    return grouped


def _select_placeholder_status(statuses: list[SourceStatus]) -> SourceStatus | None:
    if not statuses:
        return None
    ranked = sorted(
        statuses,
        key=lambda status: (
            status.ok,
            status.fetched_count > 0,
            status.kept_count > 0,
            status.final_included_count > 0,
        ),
    )
    return ranked[0]


def _placeholder_reason(status: SourceStatus) -> str:
    message = status.message.lower()
    if "http_error:403" in message:
        if "tesla" in status.company_slug:
            return "Tesla 官方新闻入口当前持续拒绝抓取请求，先保留占位，后续再评估更稳的官方接入方式。"
        return "官方源当前拒绝抓取请求，已暂时保留占位并等待后续适配。"
    if "http_error:500" in message:
        return "官方源当前返回服务错误，后续会继续检查入口稳定性。"
    if "mi.com/global/discover" in status.source_url and (status.fetched_count == 0 or "fetched:0" in message):
        return "Xiaomi Global Discover 当前以动态渲染为主，静态抓取器尚未拿到稳定文章链接，先保留占位。"
    if status.fetched_count == 0 or "fetched:0" in message:
        return "当前入口尚未抓到可用条目，后续会继续升级抓取适配。"
    if status.kept_count == 0 or status.final_included_count == 0:
        return "今天没有保留下可发布条目，当前先保留占位方便回看。"
    return "官方源暂未稳定，后续会继续升级抓取与筛选策略。"


def _is_stable_no_news_status(status: SourceStatus) -> bool:
    return (
        status.ok
        and status.fetched_count > 0
        and status.kept_count > 0
        and status.date_matched_count == 0
        and status.final_included_count == 0
    )


def _is_stable_filtered_status(status: SourceStatus) -> bool:
    return (
        status.ok
        and status.date_matched_count > 0
        and status.final_included_count == 0
    )


def _select_highlights(report: DailyReport, limit: int) -> list[EnrichedEntry]:
    entries = [entry for company in report.company_reports for entry in company.entries]
    entries.sort(key=lambda item: (-item.importance, item.raw.company_name, item.raw.title))
    return entries[:limit]


def _render_entry_detail(entry: EnrichedEntry) -> str:
    tag_badges = "".join(f"<span class='tag-chip'>{html.escape(tag)}</span>" for tag in entry.tags[:4])
    return (
        f"<div class='modal-detail-header'><p class='eyebrow'>{html.escape(entry.raw.company_name)}</p><span class='importance-pill'>P{entry.importance}</span></div>"
        f"<h3>{html.escape(entry.raw.title)}</h3>"
        f"{_render_summary_grid([('核心摘要', entry.summary_cn), ('来源与时间', f'{entry.raw.source_label} · {_format_published_at(entry.raw.published_at)}'), ('分类与角度', f'{entry.category} · {entry.comparison_angle}')])}"
        f"<p class='section-copy'>{html.escape(entry.summary_cn)}</p>"
        f"<p class='meta meta-line'>{_entry_meta(entry)}</p>"
        f"<div class='tag-row'>{tag_badges}</div>"
        f"<p class='supplement'><strong>原文补充：</strong>{html.escape(_entry_supplement(entry))}</p>"
        f"<p><a class='inline-link' href='{html.escape(entry.raw.url)}'>查看原文</a></p>"
    )


def _render_highlight_card(entry: EnrichedEntry, modal_prefix: str = "highlight") -> str:
    modal_id = f"{modal_prefix}-{entry.raw.company_slug}-{_slugify(entry.raw.title)}"
    summary = _truncate(entry.summary_cn, 92)
    return (
        "<article class='card summary-card highlight-card'>"
        f"<button class='card-trigger' type='button' data-modal-trigger='{html.escape(modal_id)}'>"
        f"<div class='card-topline'><p class='eyebrow'>{html.escape(entry.raw.company_name)}</p><span class='importance-pill'>P{entry.importance}</span></div>"
        f"<h3>{html.escape(entry.raw.title)}</h3>"
        f"<p class='section-copy'>{html.escape(summary)}</p>"
        f"<p class='meta meta-line'>{html.escape(_format_published_at(entry.raw.published_at))} · {html.escape(entry.raw.source_label)}</p>"
        "<span class='trigger-hint'>点击查看完整内容</span>"
        "</button>"
        f"<template id='{html.escape(modal_id)}'>{_render_entry_detail(entry)}</template>"
        "</article>"
    )


def _render_highlights(report: DailyReport, limit: int) -> str:
    highlights = _select_highlights(report, limit)
    if not highlights:
        return "<p class='empty'>今日暂无重点观察</p>"
    return "".join(_render_highlight_card(entry) for entry in highlights)


def _render_agent_brief(brief: dict) -> str:
    if not brief:
        return ""
    tomorrow_focus = "、".join(brief.get("tomorrow_focus", [])) or "暂无"
    markdown_link = "./agent-brief.md"
    return (
        "<section class='section'>"
        "<h2>情报判断</h2>"
        "<p class='section-hint'>这一部分由最小情报分析 agent 基于当日日报与运维状态生成，用于快速提取内容与运维层面的关键信号。</p>"
        "<div class='card'>"
        f"<p class='section-copy'><strong>今日核心判断：</strong>{html.escape(brief.get('editorial_signal', ''))}</p>"
        f"<p class='section-copy'><strong>运维提示：</strong>{html.escape(brief.get('ops_signal', ''))}</p>"
        f"<p class='section-copy'><strong>明日关注：</strong>{html.escape(tomorrow_focus)}</p>"
        f"<p><a class='inline-link' href='{markdown_link}'>查看完整 Markdown 报告</a></p>"
        "</div>"
        "</section>"
    )


def _render_cross_day_brief(brief: dict) -> str:
    if not brief:
        return ""
    warming = "、".join(brief.get("warming_themes", [])) or "暂无明显升温主题"
    steady_companies = "、".join(brief.get("steady_companies", [])) or "暂无"
    risks = "、".join(brief.get("persistent_source_risks", [])) or "暂无"
    recoveries = "、".join(brief.get("recent_source_recoveries", [])) or "暂无"
    next_focus = "、".join(brief.get("next_day_focus", [])) or "暂无"
    markdown_link = "./cross-day-brief.md"
    return (
        "<section class='section'>"
        "<h2>跨日观察</h2>"
        "<p class='section-hint'>这一部分基于最近几天的日报与 health snapshot 历史生成，用于快速提取持续升温主题、连续活跃公司和持续运维风险。</p>"
        "<div class='card'>"
        f"<p class='section-copy'><strong>最近几天主线：</strong>{html.escape(warming)}</p>"
        f"<p class='section-copy'><strong>连续活跃公司：</strong>{html.escape(steady_companies)}</p>"
        f"<p class='section-copy'><strong>持续风险：</strong>{html.escape(risks)}</p>"
        f"<p class='section-copy'><strong>最近恢复：</strong>{html.escape(recoveries)}</p>"
        f"<p class='section-copy'><strong>明日关注：</strong>{html.escape(next_focus)}</p>"
        f"<p><a class='inline-link' href='{markdown_link}'>查看完整跨日 Markdown 报告</a></p>"
        "</div>"
        "</section>"
    )


def _render_theme_tracking_brief(brief: dict) -> str:
    if not brief:
        return ""
    primary_theme = brief.get("primary_theme", "") or "暂无"
    participating_companies = "、".join(brief.get("participating_companies", [])) or "暂无"
    next_focus = "、".join(brief.get("next_day_theme_focus", [])) or "暂无"
    continue_tracking = "建议继续跟踪" if brief.get("continue_tracking") else "暂不需要继续加重跟踪"
    markdown_link = "./theme-tracking-brief.md"
    return (
        "<section class='section'>"
        "<h2>专题跟踪</h2>"
        "<p class='section-hint'>这一部分聚焦最近几天最值得继续盯住的主专题，强调主题演化和公司切入点，而不是重复罗列单日新闻。</p>"
        "<div class='card'>"
        f"<p class='section-copy'><strong>主专题：</strong>{html.escape(primary_theme)}</p>"
        f"<p class='section-copy'><strong>主题摘要：</strong>{html.escape(brief.get('theme_summary', ''))}</p>"
        f"<p class='section-copy'><strong>参与公司：</strong>{html.escape(participating_companies)}</p>"
        f"<p class='section-copy'><strong>主题演化：</strong>{html.escape(brief.get('theme_evolution', ''))}</p>"
        f"<p class='section-copy'><strong>继续跟踪：</strong>{html.escape(continue_tracking)}</p>"
        f"<p class='section-copy'><strong>明日关注：</strong>{html.escape(next_focus)}</p>"
        f"<p><a class='inline-link' href='{markdown_link}'>查看完整专题 Markdown 报告</a></p>"
        "</div>"
        "</section>"
    )


def _render_theme_dossier_brief(brief: dict) -> str:
    if not brief:
        return ""
    primary_theme = brief.get("primary_theme", "") or "暂无"
    theme_state = brief.get("theme_state", "") or "暂无"
    theme_definition = brief.get("theme_definition", "") or "暂无"
    lead_positions = "；".join(brief.get("lead_positions", [])[:2]) or "暂无"
    timeline_highlight = brief.get("timeline_highlight", "") or "暂无"
    next_focus = "、".join(brief.get("next_day_focus", [])) or "暂无"
    markdown_link = "./theme-dossier.md"
    return (
        "<section class='section'>"
        "<h2>主题档案</h2>"
        "<p class='section-hint'>这一部分把当前主专题沉淀成一个轻量 dossier，用于快速判断这个主题现在处于什么阶段，以及明天是否仍值得继续盯。</p>"
        "<div class='card'>"
        f"<p class='section-copy'><strong>主专题：</strong>{html.escape(primary_theme)}</p>"
        f"<p class='section-copy'><strong>当前阶段：</strong>{html.escape(theme_state)}</p>"
        f"<p class='section-copy'><strong>主题定义：</strong>{html.escape(theme_definition)}</p>"
        f"<p class='section-copy'><strong>主题判断：</strong>{html.escape(brief.get('theme_summary', ''))}</p>"
        f"<p class='section-copy'><strong>公司位置观察：</strong>{html.escape(lead_positions)}</p>"
        f"<p class='section-copy'><strong>时间线焦点：</strong>{html.escape(timeline_highlight)}</p>"
        f"<p class='section-copy'><strong>跟踪决策：</strong>{html.escape(brief.get('tracking_decision', ''))}</p>"
        f"<p class='section-copy'><strong>明日关注：</strong>{html.escape(next_focus)}</p>"
        f"<p><a class='inline-link' href='{markdown_link}'>查看完整 dossier Markdown</a></p>"
        "</div>"
        "</section>"
    )


def _json_script_payload(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _render_chat_agent_shell(context: dict) -> str:
    if not context:
        return ""
    return (
        "<button class='chat-launcher' type='button' id='chat-launcher' aria-controls='chat-drawer' aria-expanded='false'>情报问答</button>"
        "<aside class='chat-drawer' id='chat-drawer' role='dialog' aria-modal='false' hidden>"
        "<div class='chat-drawer-header'>"
        "<div><p class='chat-kicker'>Agent v1</p><h3>情报问答</h3><p class='chat-subtitle'>基于今日日报、跨日观察与专题跟踪回答</p></div>"
        "<button class='chat-close' type='button' id='chat-close' aria-label='关闭问答'>×</button>"
        "</div>"
        "<div class='chat-quick-questions' id='chat-quick-questions'></div>"
        "<p class='chat-status' id='chat-status' aria-live='polite'>页面内问题会优先使用已生成的问答结果回答；你也可以继续追问今天重点、主专题、某家公司最近几天的动作，或者当前信源状态。</p>"
        "<div class='chat-messages' id='chat-messages'></div>"
        "<div class='chat-input-row'>"
        "<input class='chat-input' id='chat-input' type='text' placeholder='问我：今天最值得关注什么？' />"
        "<button class='chat-send' type='button' id='chat-send'>发送</button>"
        "</div>"
        "</aside>"
        "<script id='chat-agent-context' type='application/json'>"
        f"{_json_script_payload(context)}"
        "</script>"
        "<script>"
        "(() => {"
        "const launcher = document.getElementById('chat-launcher');"
        "const drawer = document.getElementById('chat-drawer');"
        "const closeButton = document.getElementById('chat-close');"
        "const input = document.getElementById('chat-input');"
        "const send = document.getElementById('chat-send');"
        "const messages = document.getElementById('chat-messages');"
        "const status = document.getElementById('chat-status');"
        "const quickContainer = document.getElementById('chat-quick-questions');"
        "const rawContext = document.getElementById('chat-agent-context');"
        "if (!launcher || !drawer || !input || !send || !messages || !rawContext || !status) { return; }"
        "const context = JSON.parse(rawContext.textContent || '{}');"
        "const responseBank = context.response_bank || {};"
        "const companies = context.companies || [];"
        "const primaryTheme = (context.theme_tracking || {}).primary_theme || '';"
        "const runtimeChat = context.runtime_chat || {};"
        "const runtimeEndpoint = runtimeChat.endpoint || '/api/chat';"
        "const runtimeEnabled = ['http:', 'https:'].includes(window.location.protocol);"
        "const conversationHistory = [];"
        "let lastFocused = null;"
        "function setStatus(text, state) {"
        "  status.textContent = text;"
        "  if (state) status.dataset.state = state;"
        "  else delete status.dataset.state;"
        "}"
        "function addMessage(role, text) {"
        "  const bubble = document.createElement('div');"
        "  bubble.className = role === 'user' ? 'chat-message user' : 'chat-message agent';"
        "  bubble.textContent = text;"
        "  messages.appendChild(bubble);"
        "  messages.scrollTop = messages.scrollHeight;"
        "}"
        "function addAgentResponse(response) {"
        "  addMessage('agent', response.answer || '当前没有可返回的问答结果。');"
        "  const evidenceItems = response.evidence_items || [];"
        "  const evidencePoints = response.evidence_points || [];"
        "  if (evidenceItems.length || evidencePoints.length) {"
        "    const evidence = document.createElement('div');"
        "    evidence.className = 'chat-evidence';"
        "    const title = document.createElement('p');"
        "    title.className = 'chat-evidence-title';"
        "    title.textContent = '回答依据来源';"
        "    evidence.appendChild(title);"
        "    const list = document.createElement('ul');"
        "    list.className = 'chat-evidence-list';"
        "    if (evidenceItems.length) {"
        "      for (const evidenceItem of evidenceItems) {"
        "        const item = document.createElement('li');"
        "        item.className = 'chat-evidence-item';"
        "        const source = document.createElement('span');"
        "        source.className = 'chat-evidence-source';"
        "        source.textContent = evidenceItem.label || evidenceItem.source || '依据';"
        "        const reference = document.createElement('span');"
        "        reference.className = 'chat-evidence-reference';"
        "        reference.textContent = evidenceItem.reference || '';"
        "        const detail = document.createElement('span');"
        "        detail.className = 'chat-evidence-detail';"
        "        detail.textContent = evidenceItem.detail || '';"
        "        item.appendChild(source);"
        "        if (reference.textContent) item.appendChild(reference);"
        "        item.appendChild(detail);"
        "        list.appendChild(item);"
        "      }"
        "    } else {"
        "      for (const point of evidencePoints) {"
        "        const item = document.createElement('li');"
        "        item.textContent = point;"
        "        list.appendChild(item);"
        "      }"
        "    }"
        "    evidence.appendChild(list);"
        "    messages.appendChild(evidence);"
        "  }"
        "  const followUps = response.follow_up_suggestions || [];"
        "  if (followUps.length) {"
        "    const followSection = document.createElement('div');"
        "    followSection.className = 'chat-follow-ups';"
        "    const followTitle = document.createElement('p');"
        "    followTitle.className = 'chat-follow-ups-title';"
        "    followTitle.textContent = '建议继续追问';"
        "    followSection.appendChild(followTitle);"
        "    const followRow = document.createElement('div');"
        "    followRow.className = 'chat-follow-up-list';"
        "    for (const suggestion of followUps.slice(0, 3)) {"
        "      const chip = document.createElement('button');"
        "      chip.type = 'button';"
        "      chip.className = 'chat-chip chat-follow-up-chip';"
        "      chip.textContent = suggestion;"
        "      chip.addEventListener('click', () => ask(suggestion));"
        "      followRow.appendChild(chip);"
        "    }"
        "    followSection.appendChild(followRow);"
        "    messages.appendChild(followSection);"
        "  }"
        "  messages.scrollTop = messages.scrollHeight;"
        "}"
        "function rememberTurn(question, response) {"
        "  conversationHistory.push({ role: 'user', content: question });"
        "  conversationHistory.push({"
        "    role: 'assistant',"
        "    content: response.answer || '',"
        "    question_type: response.question_type || '',"
        "    resolved_theme: response.resolved_theme || '',"
        "    resolved_company: response.resolved_company || ''"
        "  });"
        "  while (conversationHistory.length > 12) conversationHistory.shift();"
        "}"
        "function openDrawer() {"
        "  lastFocused = document.activeElement;"
        "  launcher.setAttribute('aria-expanded', 'true');"
        "  document.body.dataset.previousOverflow = document.body.style.overflow || '';"
        "  document.body.style.overflow = 'hidden';"
        "  drawer.hidden = false;"
        "  input.focus();"
        "}"
        "function closeDrawer() {"
        "  drawer.hidden = true;"
        "  launcher.setAttribute('aria-expanded', 'false');"
        "  document.body.style.overflow = document.body.dataset.previousOverflow || '';"
        "  (lastFocused && typeof lastFocused.focus === 'function' ? lastFocused : launcher).focus();"
        "}"
        "function classify(question) {"
        "  const normalized = (question || '').trim();"
        "  const lowered = normalized.toLowerCase();"
        "  if (['时间线','演化','关键事件'].some((token) => normalized.includes(token))) return { type: 'timeline_focus', entity: primaryTheme };"
        "  if (['emerging','active','fragmenting','cooling'].some((token) => lowered.includes(token)) || normalized.includes('阶段')) return { type: 'theme_state', entity: primaryTheme };"
        "  if (['怎么理解','值得跟踪','值得继续跟踪','主专题现在'].some((token) => normalized.includes(token))) return { type: 'dossier_summary', entity: primaryTheme };"
        "  for (const company of companies) {"
        "    if (company && lowered.includes(company.toLowerCase()) && ['位置','角色','专题里'].some((token) => normalized.includes(token))) return { type: 'company_position', entity: company };"
        "    if (company && lowered.includes(company.toLowerCase())) return { type: 'company_focus', entity: company };"
        "  }"
        "  if (['信源','抓取','异常','问题','恢复','运维'].some((token) => normalized.includes(token))) return { type: 'ops_status', entity: '' };"
        "  if (primaryTheme && normalized.includes(primaryTheme)) return { type: 'theme_focus', entity: primaryTheme };"
        "  if (['主题','专题'].some((token) => normalized.includes(token))) return { type: 'theme_focus', entity: primaryTheme };"
        "  if (['今天','关注','主线','值得看','总结','重点'].some((token) => normalized.includes(token))) return { type: 'daily_summary', entity: '' };"
        "  return { type: 'out_of_scope', entity: '' };"
        "}"
        "function answer(question) {"
        "  const route = classify(question);"
        "  if (route.type === 'daily_summary') return responseBank.daily_summary || { answer: '今天还没有可直接回答的日报摘要。', mode_used: 'rule' };"
        "  if (route.type === 'company_focus') return (responseBank.company_focus || {})[(route.entity || '').toLowerCase()] || { answer: '当前还没有足够明确的公司上下文。', mode_used: 'rule' };"
        "  if (route.type === 'company_position') return (responseBank.company_position_answers || {})[(route.entity || '').toLowerCase()] || { answer: '当前还没有足够明确的公司专题位置。', mode_used: 'rule' };"
        "  if (route.type === 'dossier_summary') return responseBank.dossier_summary || responseBank.theme_focus || { answer: '当前还没有形成明确的专题档案。', mode_used: 'rule' };"
        "  if (route.type === 'theme_state') return responseBank.theme_state || { answer: '当前还没有足够明确的主题阶段判断。', mode_used: 'rule' };"
        "  if (route.type === 'timeline_focus') return responseBank.timeline_focus || { answer: '当前还没有足够明确的关键时间线。', mode_used: 'rule' };"
        "  if (route.type === 'theme_focus') return responseBank.theme_focus || { answer: '当前还没有形成明确主专题。', mode_used: 'rule' };"
        "  if (route.type === 'ops_status') return responseBank.ops_status || { answer: '当前没有额外运维提示。', mode_used: 'rule' };"
        "  return responseBank.out_of_scope || { answer: '当前问答主要基于今日日报、跨日观察、专题跟踪和运维状态。你可以继续问今天重点、某家公司、主专题或信源状态。', mode_used: 'rule' };"
        "}"
        "async function ask(question) {"
        "  if (!question.trim()) return;"
        "  addMessage('user', question);"
        "  setStatus(runtimeEnabled ? '正在连接本地问答服务…' : '正在整理回答…', 'loading');"
        "  send.disabled = true;"
        "  input.disabled = true;"
        "  try {"
        "    let response = null;"
        "    if (runtimeEnabled) {"
        "      try {"
        "        const apiResponse = await fetch(runtimeEndpoint, {"
        "          method: 'POST',"
        "          headers: { 'Content-Type': 'application/json' },"
        "          body: JSON.stringify({ date: context.report_date, question, messages: conversationHistory })"
        "        });"
        "        if (!apiResponse.ok) throw new Error('runtime_chat_failed');"
        "        response = await apiResponse.json();"
        "      } catch (runtimeError) {"
        "        response = answer(question);"
        "        response.mode_used = response.mode_used || 'rule';"
        "        response._fell_back = true;"
        "      }"
        "    } else {"
        "      response = answer(question);"
        "    }"
        "    addAgentResponse(response);"
        "    rememberTurn(question, response);"
        "    const mode = response.mode_used || 'rule';"
        "    if (response._fell_back) setStatus('本地问答服务暂不可用，已回退到内嵌回答。', 'fallback');"
        "    else if (mode === 'rule') setStatus(runtimeEnabled ? '当前由本地问答服务返回规则回答，可继续追问。' : '当前使用本地规则问答，可继续追问。', 'fallback');"
        "    else setStatus('当前使用真实增强问答模式，可继续追问。', 'enhanced');"
        "  } catch (error) {"
        "    addMessage('agent', '这次问答没有顺利完成，我先回退到日报内可直接支持的问题：今天重点、主专题、某家公司、信源状态。');"
        "    setStatus('问答已降级到安全模式。', 'error');"
        "  } finally {"
        "    send.disabled = false;"
        "    input.disabled = false;"
        "  }"
        "  input.value = '';"
        "}"
        "launcher.addEventListener('click', openDrawer);"
        "closeButton?.addEventListener('click', closeDrawer);"
        "send.addEventListener('click', () => ask(input.value));"
        "input.addEventListener('keydown', (event) => { if (event.key === 'Enter') ask(input.value); });"
        "drawer.addEventListener('keydown', (event) => {"
        "  if (event.key === 'Escape') { closeDrawer(); return; }"
        "  if (event.key !== 'Tab') return;"
        "  const focusables = drawer.querySelectorAll('button, [href], input');"
        "  if (!focusables.length) return;"
        "  const first = focusables[0];"
        "  const last = focusables[focusables.length - 1];"
        "  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }"
        "  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }"
        "});"
        "for (const question of (context.quick_questions || [])) {"
        "  const chip = document.createElement('button');"
        "  chip.type = 'button';"
        "  chip.className = 'chat-chip';"
        "  chip.textContent = question;"
        "  chip.addEventListener('click', () => ask(question));"
        "  quickContainer.appendChild(chip);"
        "}"
        "if (!(context.quick_questions || []).length) {"
        "  const empty = document.createElement('p');"
        "  empty.className = 'chat-note';"
        "  empty.textContent = '今天没有额外快捷问题，你也可以直接输入问题。';"
        "  quickContainer.appendChild(empty);"
        "}"
        "addMessage('agent', '可以直接问我今天重点、主专题、某家公司最近几天的动作，或者当前信源状态。');"
        "})();"
        "</script>"
    )


def _render_recent_issue_items(items: list[dict]) -> str:
    return "".join(
        "<article class='recent-item'>"
        f"<p class='recent-date'>{html.escape(item.get('label', ''))}</p>"
        "<div>"
        f"<h3 class='recent-title'><a href='{html.escape(item.get('href', '#'))}'>{html.escape(item.get('label', ''))}</a></h3>"
        f"<p class='recent-headline'>{html.escape(item.get('headline', ''))}</p>"
        "</div>"
        "</article>"
        for item in items
    )


def _render_meta_cards(items: list[tuple[str, str]]) -> str:
    return "".join(
        "<article class='meta-card'>"
        f"<strong>{html.escape(label)}</strong>"
        f"<p class='section-copy'>{html.escape(value)}</p>"
        "</article>"
        for label, value in items
        if value
    )


def _render_topic_card(cluster: TopicCluster, modal_prefix: str = "topic") -> str:
    companies = sorted({entry.raw.company_name for entry in cluster.entries})
    modal_id = f"{modal_prefix}-{cluster.topic_id}"
    representative_entries = "".join(
        "<li class='topic-event'>"
        f"<div class='topic-event-title'><strong>{html.escape(entry.raw.company_name)}</strong><a class='inline-link' href=\"{html.escape(entry.raw.url)}\">{html.escape(entry.raw.title)}</a></div>"
        f"<p class='section-copy'>{html.escape(entry.summary_cn)}</p>"
        "</li>"
        for entry in cluster.entries[:3]
    )
    summary = _truncate(cluster.summary, 104)
    return (
        "<section class='card topic-card summary-card'>"
        f"<button class='card-trigger' type='button' data-modal-trigger='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(cluster.title)}</h3>"
        f"<div class='topic-stat-row'><span class='topic-stat-chip'>涉及公司 {len(companies)}</span><span class='topic-stat-chip'>条目 {len(cluster.entries)}</span></div>"
        f"<p class='meta meta-line'>公司：{html.escape(', '.join(companies))}</p>"
        f"<p class='section-copy'>{html.escape(summary)}</p>"
        f"<p class='topic-note'><strong>趋势判断：</strong>{html.escape(_truncate(cluster.trend, 96))}</p>"
        "<span class='trigger-hint'>点击展开完整主题分析</span>"
        "</button>"
        f"<template id='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(cluster.title)}</h3>"
        f"{_render_summary_grid([('涉及公司', '、'.join(companies)), ('条目数量', str(len(cluster.entries))), ('差异对比', cluster.comparison), ('趋势判断', cluster.trend)])}"
        f"<p class='meta meta-line'>涉及公司：{len(companies)} | 条目数：{len(cluster.entries)} | 公司：{html.escape(', '.join(companies))}</p>"
        f"<p class='section-copy'>{html.escape(cluster.summary)}</p>"
        f"<p class='topic-note'><strong>差异对比：</strong>{html.escape(cluster.comparison)}</p>"
        f"<p class='topic-note'><strong>趋势判断：</strong>{html.escape(cluster.trend)}</p>"
        "<p class='topic-list-label'><strong>代表事件：</strong></p>"
        f"<ul class='topic-event-list'>{representative_entries}</ul>"
        "</template>"
        "</section>"
    )


def _render_company_report(
    report: CompanyReport,
    statuses_by_company: dict[str, list[SourceStatus]] | None = None,
    modal_prefix: str = "company",
) -> str:
    if not report.entries:
        statuses = (statuses_by_company or {}).get(report.company_slug, [])
        placeholder_status = _select_placeholder_status(statuses)
        if placeholder_status is None:
            body = "<p class='empty'>今日无有效动态</p>"
        elif _is_stable_no_news_status(placeholder_status):
            body = (
                "<div class='placeholder-block'>"
                "<span class='status-pill stable'>当日无动态</span>"
                "<p class='placeholder-note'>官方信源抓取正常，但今天没有落在日报日期范围内的有效动态。</p>"
                f"<p class='meta meta-line'>当前来源：{html.escape(placeholder_status.source_label)} | 诊断：{html.escape(placeholder_status.message)}</p>"
                "</div>"
            )
        elif _is_stable_filtered_status(placeholder_status):
            body = (
                "<div class='placeholder-block'>"
                "<span class='status-pill stable'>当日无可发布动态</span>"
                "<p class='placeholder-note'>官方信源抓取正常，也抓到了同日内容，但今天没有保留下可发布条目。</p>"
                f"<p class='meta meta-line'>当前来源：{html.escape(placeholder_status.source_label)} | 诊断：{html.escape(placeholder_status.message)}</p>"
                "</div>"
            )
        else:
            body = (
                "<div class='placeholder-block'>"
                "<span class='status-pill'>信源暂未稳定</span>"
                f"<p class='placeholder-note'>{html.escape(_placeholder_reason(placeholder_status))}</p>"
                f"<p class='meta meta-line'>当前来源：{html.escape(placeholder_status.source_label)} | 诊断：{html.escape(placeholder_status.message)}</p>"
                "</div>"
            )
    else:
        items = []
        for entry in report.entries:
            items.append(
                "<article class='entry'>"
                f"<h4>{html.escape(entry.raw.title)}</h4>"
                f"<p class='section-copy'>{html.escape(entry.summary_cn)}</p>"
                f"<p class='meta meta-line'>{_entry_meta(entry)}</p>"
                f"<p class='supplement'><strong>原文补充：</strong>{html.escape(_entry_supplement(entry))}</p>"
                f"<p><a class='inline-link' href='{html.escape(entry.raw.url)}'>查看原文</a></p>"
                "</article>"
            )
        body = "".join(items)
    if not report.entries:
        return (
            "<section class='card company-card'>"
            f"<h3>{html.escape(report.company_name)}</h3>"
            f"{body}"
            "</section>"
        )
    modal_id = f"{modal_prefix}-{report.company_slug}"
    lead = report.entries[0]
    summary = _truncate(lead.summary_cn, 96)
    return (
        "<section class='card company-card summary-card'>"
        f"<button class='card-trigger' type='button' data-modal-trigger='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(report.company_name)}</h3>"
        f"<div class='topic-stat-row'><span class='topic-stat-chip'>当日动态 {len(report.entries)} 条</span><span class='topic-stat-chip'>最高重要度 P{lead.importance}</span></div>"
        f"<p class='section-copy'>{html.escape(summary)}</p>"
        f"<p class='meta meta-line'>最新来源：{html.escape(lead.raw.source_label)} | 发布时间：{html.escape(_format_published_at(lead.raw.published_at))}</p>"
        "<span class='trigger-hint'>点击查看公司完整动态</span>"
        "</button>"
        f"<template id='{html.escape(modal_id)}'>"
        f"<h3>{html.escape(report.company_name)}</h3>"
        f"{_render_summary_grid([('动态数量', str(len(report.entries))), ('最新来源', lead.raw.source_label), ('最新发布时间', _format_published_at(lead.raw.published_at))])}"
        f"{body}"
        "</template>"
        "</section>"
    )


def render_index(report: DailyReport) -> str:
    template = _load_template("home_magazine.html")
    cover = report.magazine_pages.get("cover", {})
    return template.substitute(
        primary_theme=html.escape(cover.get("primary_theme", "暂无主专题")),
        cover_summary=html.escape(cover.get("cover_summary", report.headline)),
        latest_report_date=html.escape(str(cover.get("latest_report_date", report.date))),
        latest_daily_href=html.escape(cover.get("daily_href", f"./{report.date}/index.html")),
        topic_href=html.escape(cover.get("topic_href", f"./{report.date}/topic.html")),
        dossier_href=html.escape(cover.get("dossier_href", f"./{report.date}/dossier.html")),
        editorial_line=html.escape(cover.get("editorial_line", report.headline)),
        theme_state=html.escape(cover.get("theme_state", "暂无")),
        participating_companies=html.escape("、".join(cover.get("participating_companies", [])) or "暂无"),
        next_focus=html.escape("、".join(cover.get("next_focus", [])) or "暂无"),
        recent_issues=_render_recent_issue_items(cover.get("recent_issues", [])),
        chat_agent_shell=_render_chat_agent_shell(report.chat_agent_context),
        page_transition_shell=_render_page_transition_shell(),
    )


def render_daily(report: DailyReport) -> str:
    template = _load_template("daily.html")
    statuses_by_company = _statuses_by_company(report.source_statuses)
    statuses = "".join(
        f"<li>{html.escape(status.company_name)} - {html.escape(status.source_label)} - {html.escape(status.message)}</li>"
        for status in report.source_statuses
    )
    return template.substitute(
        date=html.escape(report.date),
        headline=html.escape(report.headline),
        agent_brief_section=_render_agent_brief(report.agent_brief),
        cross_day_brief_section=_render_cross_day_brief(report.cross_day_brief),
        theme_tracking_brief_section=_render_theme_tracking_brief(report.theme_tracking_brief),
        theme_dossier_brief_section=_render_theme_dossier_brief(report.theme_dossier_brief),
        topic_page_href="./topic.html",
        dossier_page_href="./dossier.html",
        highlights=_render_highlights(report, limit=8),
        topic_cards="".join(_render_topic_card(cluster) for cluster in report.topic_clusters),
        company_cards="".join(
            _render_company_report(company, statuses_by_company=statuses_by_company)
            for company in report.company_reports
        ),
        statuses=statuses or "<li>无</li>",
        chat_agent_shell=_render_chat_agent_shell(report.chat_agent_context),
        page_transition_shell=_render_page_transition_shell(),
    )


def render_topic_page(report: DailyReport) -> str:
    template = _load_template("topic.html")
    tracking = report.theme_tracking_brief or {}
    dossier = report.theme_dossier_brief or {}
    cross_day = report.cross_day_brief or {}
    title = tracking.get("primary_theme") or dossier.get("primary_theme") or "暂无主专题"
    return template.substitute(
        title=html.escape(title),
        summary=html.escape(tracking.get("theme_summary", report.headline)),
        cross_day_summary=html.escape("、".join(cross_day.get("warming_themes", [])) or "最近几天暂无明显升温主题。"),
        theme_tracking_summary=html.escape(tracking.get("theme_evolution", tracking.get("theme_summary", "暂无专题跟踪摘要。"))),
        theme_tracking_meta=_render_meta_cards(
            [
                ("参与公司", "、".join(tracking.get("participating_companies", [])) or "暂无"),
                ("继续跟踪", "建议继续跟踪" if tracking.get("continue_tracking") else "暂不需要继续加重跟踪"),
                ("下一步关注", "、".join(tracking.get("next_day_theme_focus", [])) or "暂无"),
            ]
        ),
        dossier_summary=html.escape(dossier.get("theme_summary", dossier.get("theme_definition", "暂无主题档案摘要。"))),
        dossier_meta=_render_meta_cards(
            [
                ("当前阶段", dossier.get("theme_state", "暂无")),
                ("主题定义", dossier.get("theme_definition", "暂无")),
                ("跟踪决策", dossier.get("tracking_decision", "暂无")),
            ]
        ),
        chat_agent_shell=_render_chat_agent_shell(report.chat_agent_context),
        page_transition_shell=_render_page_transition_shell(),
    )


def render_dossier_page(report: DailyReport) -> str:
    template = _load_template("dossier.html")
    dossier = report.theme_dossier_brief or {}
    title = dossier.get("primary_theme") or "暂无主专题"
    positions = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in dossier.get("lead_positions", [])
    ) or "<li>暂无</li>"
    return template.substitute(
        title=html.escape(title),
        theme_summary=html.escape(dossier.get("theme_summary", "暂无主题摘要。")),
        theme_state=html.escape(dossier.get("theme_state", "暂无")),
        theme_definition=html.escape(dossier.get("theme_definition", "暂无")),
        company_positions=positions,
        timeline_highlight=html.escape(dossier.get("timeline_highlight", "暂无")),
        tracking_decision=html.escape(dossier.get("tracking_decision", "暂无")),
        chat_agent_shell=_render_chat_agent_shell(report.chat_agent_context),
        page_transition_shell=_render_page_transition_shell(),
    )


def render_archive(reports: list[DailyReport]) -> str:
    template = _load_template("archive.html")
    items = []
    for report in reports:
        items.append(
            "<li>"
            f"<a href='./{html.escape(report.date)}/index.html'>{html.escape(report.date)}</a>"
            f" - {html.escape(report.headline)}"
            "</li>"
        )
    return template.substitute(archive_items="".join(items) or "<li>暂无归档</li>")


def write_site(report: DailyReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    daily_dir = output_dir / report.date
    daily_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "index.html").write_text(render_index(report), encoding="utf-8")
    (daily_dir / "index.html").write_text(render_daily(report), encoding="utf-8")
    (daily_dir / "topic.html").write_text(render_topic_page(report), encoding="utf-8")
    (daily_dir / "dossier.html").write_text(render_dossier_page(report), encoding="utf-8")
    (daily_dir / "report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    archived_reports = load_report_snapshots(output_dir)
    (output_dir / "archive.html").write_text(render_archive(archived_reports), encoding="utf-8")
