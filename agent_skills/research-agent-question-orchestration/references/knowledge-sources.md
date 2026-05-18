# Knowledge Sources

This reference defines the report knowledge layer that the project-local research assistant is allowed to use.

## Primary Artifacts

### `build/site/<date>/report.json`

Use for:

- same-day company activity
- same-day topic clustering
- source statuses
- verifying what actually made it into the daily report

### `build/site/<date>/daily_intel_brief.json`

Use for:

- same-day editorial judgment
- same-day top signals
- concise daily framing

### `build/site/<date>/cross_day_intel_brief.json`

Use for:

- recent theme warming/cooling
- steady companies
- recent source recoveries
- next-day focus across multiple days

### `build/site/<date>/theme_tracking_brief.json`

Use for:

- candidate themes
- primary tracked theme
- company participation inside the tracked theme
- near-term tracking decision

### `build/site/<date>/theme_dossier.json`

Use for:

- theme definition
- theme state
- company positions
- timeline events
- tracking decision
- dossier-level next-step framing

### `build/data/health_snapshot.json`

Use for:

- runtime availability
- high-priority source issues
- recent recoveries
- operator-facing risk context

## Context Priority

Choose by question type:

- Theme-state or company-position question: dossier first
- Multi-day trend question: cross-day plus dossier
- Same-day question: daily brief plus report
- Runtime/source question: health snapshot plus report source status

## Boundary Rule

These artifacts are the knowledge boundary.

The research assistant should not:

- browse the open web
- scrape live company pages
- infer unsupported facts from page HTML
- answer from general world knowledge when the artifacts are silent
