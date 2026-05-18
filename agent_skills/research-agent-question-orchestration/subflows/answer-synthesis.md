# Answer Synthesis

This subflow defines how the project research assistant should turn selected report context into an answer.

## Goal

Produce a research-assistant answer that:

- leads with a judgment
- cites concrete evidence
- stays inside the report knowledge boundary
- suggests a useful next question

## Preferred Structure

1. Conclusion
2. Why that conclusion follows
3. What to watch next

## Rules

1. Do not echo raw JSON fields mechanically.
2. Prefer concise analytical wording over long summary prose.
3. If dossier context is present, use dossier framing first.
4. If dossier context is missing, degrade to theme tracking, then cross-day, then same-day report context.
5. If evidence is weak, say so rather than pretending certainty.

## Output Expectations

- `answer`
- `evidence_items`
- `follow_up_suggestions`
- `mode_used`

## Anti-Patterns

- meta narration
- unsupported forecasting
- external facts
- fixed canned answers that ignore the selected context
