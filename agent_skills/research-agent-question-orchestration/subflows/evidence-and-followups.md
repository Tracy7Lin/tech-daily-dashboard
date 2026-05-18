# Evidence And Follow-Ups

This subflow defines how evidence attribution and follow-up suggestions should be produced.

## Evidence Policy

Each non-trivial answer should cite the narrowest useful source.

Preferred labels:

- `theme_dossier.json · 专题档案`
- `theme_tracking_brief.json · 专题跟踪`
- `cross_day_intel_brief.json · 跨日观察`
- `daily_intel_brief.json · 当日情报判断`
- `report.json · 当日日报`
- `health_snapshot.json · 运行状态`

Evidence detail should explain *why* the answer was produced, not just where it came from.

## Follow-Up Policy

Follow-up suggestions should depend on the active answer type.

Examples:

- after `dossier_summary`: ask about state or timeline
- after `theme_state`: ask about timeline or company position
- after `company_position`: ask about state or the same company's recent actions
- after `timeline_focus`: ask about dossier summary or state

## Rules

1. Prefer 2-3 useful follow-ups over a long generic list.
2. Use the resolved company or theme when available.
3. Keep suggestions inside the report knowledge boundary.
4. If the answer is already weak or uncertain, suggest a narrower follow-up.
