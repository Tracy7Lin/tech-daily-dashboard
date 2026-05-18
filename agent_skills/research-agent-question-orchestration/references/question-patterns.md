# Question Patterns

This reference captures common question shapes that the runtime research assistant should handle well.

## Daily Framing

Examples:

- `今天最值得关注什么？`
- `今天的主线是什么？`
- `今天有哪些重点？`

Expected handling:

- use daily brief first
- support with report or topic evidence

## Theme Understanding

Examples:

- `这个主专题现在怎么理解？`
- `为什么这个主题还值得跟踪？`
- `这个专题最近在往哪边走？`

Expected handling:

- use dossier first
- support with cross-day and theme tracking

## Theme State

Examples:

- `为什么现在是 emerging？`
- `为什么不是 active？`
- `这个主题已经降温了吗？`

Expected handling:

- use dossier theme state and tracking decision
- support with timeline and cross-day evidence

## Company Position

Examples:

- `Google 在这个专题里处于什么位置？`
- `OpenAI 在这里扮演什么角色？`
- `那 Amazon 呢？`

Expected handling:

- resolve company explicitly or from session memory
- use dossier company positions first

## Timeline Focus

Examples:

- `最近几天关键时间线说明了什么？`
- `最关键的一条是什么？`
- `继续说时间线`

Expected handling:

- use dossier timeline events first
- support with why-it-matters framing

## Follow-Up Forms

Examples:

- `那 Google 呢？`
- `为什么？`
- `继续`
- `还有别的吗？`

Expected handling:

- inspect session memory first
- inherit the last valid theme/company/intent when reasonable
- degrade gracefully if the follow-up target is still ambiguous

## Out-of-Scope

Examples:

- `帮我查一下外网怎么评价这个主题`
- `这个公司股价会怎么走`
- `去搜索其他媒体怎么报道`

Expected handling:

- say the current report knowledge layer cannot support that answer directly
- suggest a narrower report-grounded follow-up
