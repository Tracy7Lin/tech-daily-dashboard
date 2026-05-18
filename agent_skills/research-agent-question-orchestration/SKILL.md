# Research Agent Question Orchestration

## Purpose

This is a project-local skill for the `tech-daily-dashboard` research assistant.

It is not a global Codex skill and should not be treated as a reusable generic chat workflow. It exists to guide this repository's runtime research agent when answering free-form questions against the project's own daily intelligence knowledge layer.

## Scope

Use this skill when a user asks an open-ended or follow-up question about:

- the latest daily report
- cross-day developments
- the primary tracked theme
- the current theme dossier
- company positioning inside the tracked theme
- timeline meaning or next-step interpretation
- source/runtime status when it affects the report

Do not use this skill to:

- search the public internet
- answer from general world knowledge when the report knowledge layer is silent
- invent facts beyond the generated JSON artifacts
- replace source collection, classification, or rendering logic

## Required Workflow

Follow this sequence:

1. Identify the user's intent.
2. Resolve the target object.
3. Select the smallest sufficient context from the report knowledge layer.
4. Synthesize a research-assistant answer.
5. Attach explicit evidence references.
6. Apply fallback behavior if context is weak or missing.

Subflow references:

- `subflows/question-understanding.md`
- `subflows/answer-synthesis.md`
- `subflows/evidence-and-followups.md`

## Step 1: Identify Intent

Classify the question by meaning, not by shallow keyword match.

Common intents include:

- `daily_summary`
- `theme_summary`
- `theme_state`
- `company_position`
- `timeline_focus`
- `comparison`
- `next_step`
- `ops_status`
- `follow_up`
- `out_of_scope`

For follow-up questions such as `那 Google 呢`, `为什么`, `继续说`, first inspect session memory before classifying the new question in isolation.

## Step 2: Resolve the Target Object

Extract or inherit:

- target theme
- target company
- target time window
- requested explanation dimension

Allowed explanation dimensions:

- judgment
- evidence
- evolution
- comparison
- implication
- next-step focus

If the user omits the target but the prior turn makes it clear, inherit it from session memory. If the target is still ambiguous, answer conservatively and say what assumption was used.

## Step 3: Select Context

Read only the relevant knowledge artifacts for the question.

Preferred sources:

1. `theme_dossier.json`
2. `theme_tracking_brief.json`
3. `cross_day_intel_brief.json`
4. `daily_intel_brief.json`
5. `report.json`
6. `health_snapshot.json`

Selection rules:

- Use `theme_dossier.json` first for theme-state, company-position, timeline, and tracking questions.
- Use `cross_day_intel_brief.json` for trend and multi-day evolution.
- Use `daily_intel_brief.json` and `report.json` for same-day specifics.
- Use `health_snapshot.json` only when the question is about availability, missing coverage, or source stability.

Do not pass every artifact blindly. Select the smallest 2-4 relevant context blocks.

## Step 4: Synthesize the Answer

The answer should behave like a research assistant:

- lead with a judgment
- support it with 1-3 concrete pieces of evidence
- stay inside the report knowledge boundary
- suggest a useful next question when appropriate

Preferred answer shape:

1. Short conclusion
2. Why that conclusion follows
3. What to watch next, if useful

Avoid:

- meta phrasing
- generic LLM filler
- pretending certainty when the knowledge layer is sparse
- introducing outside facts

## Step 5: Evidence Attribution

Every non-trivial answer should attach evidence references.

Use source labels such as:

- `theme_dossier.json · 专题档案`
- `theme_tracking_brief.json · 专题跟踪`
- `cross_day_intel_brief.json · 跨日观察`
- `daily_intel_brief.json · 当日情报判断`
- `report.json · 当日日报`
- `health_snapshot.json · 运行状态`

Evidence should point to the specific reason the answer was produced, not just the broad file name.

## Step 6: Fallback Behavior

If dossier-level context is missing:

- fall back to theme tracking
- then cross-day
- then same-day report context

If the question exceeds the knowledge boundary:

- say that the current knowledge layer does not support a confident answer
- offer a narrower follow-up grounded in available artifacts

If the user asks a free-form question that only partially maps to known structures:

- answer the grounded portion
- explicitly mark the remaining uncertainty

## Session Memory Rules

This skill assumes short session memory, not long-term memory.

Use the recent conversation window to inherit:

- theme
- company
- intent
- answer framing

Do not use session memory to invent facts or stretch across unrelated topics.

## Quality Bar

A good answer should feel like:

- it actually read the report artifacts
- it knows the difference between theme, cross-day, and dossier context
- it can explain why a conclusion was reached
- it can support follow-up questioning naturally

If the output feels like a fixed canned answer, the skill was not used correctly.
