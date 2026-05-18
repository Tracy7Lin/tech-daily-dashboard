# Question Understanding

This subflow is responsible for turning a free-form user question into a structured research intent.

## Goal

Resolve:

- intent
- target theme
- target company
- explanation dimension

The output should be richer than a single label, even if downstream compatibility still maps it back to a legacy `question_type`.

## Expected Output Shape

- `intent`
- `resolved_theme`
- `resolved_company`
- `explanation_dimension`
- `question_type`
- `assumption_used`

## Rules

1. Prefer semantic intent over keyword counting.
2. Inherit target theme/company from recent session memory when a follow-up is incomplete.
3. Treat questions like `为什么`, `那 Google 呢`, `继续说` as incomplete until memory resolution is attempted.
4. If the question mentions a company and asks about position/role inside a theme, prefer `company_position`.
5. If the question asks about state, maturity, or why a theme is `emerging/active/fragmenting/cooling`, prefer `theme_state`.
6. If the question asks for meaning or framing of the primary topic, prefer `dossier_summary`.

## Explanation Dimensions

Use one of:

- `judgment`
- `evidence`
- `evolution`
- `comparison`
- `implication`
- `next_step`

## Fallback

If the target remains ambiguous:

- answer conservatively
- note the assumption if needed
- do not invent a target company or theme without basis
