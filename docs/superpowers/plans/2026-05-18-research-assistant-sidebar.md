# Research Assistant Sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the runtime research assistant into a desktop-first right sidebar, keep mobile drawer fallback, and further consolidate answer synthesis plus evidence/follow-up policy into shared agent helpers.

**Architecture:** Keep `chat_agent_response.py` and `research_agent_response.py` separate, but move more shared answer-shaping behavior into `src/tech_daily/research_assistant_policy.py`. Update the magazine page templates and `render.py` so desktop pages render a shared three-region shell (`left rail / main body / right assistant rail`) while mobile keeps the existing drawer flow.

**Tech Stack:** Python 3, dataclass-style report models, static HTML templates, inline CSS/JS, unittest, git

---

## File Map

- Create: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_research_assistant_policy.py`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\research_assistant_policy.py`
  - Shared answer synthesis, evidence policy, and follow-up generation
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\chat_agent_response.py`
  - Delegate more rule-answer shaping to shared policy
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\research_agent_response.py`
  - Delegate more runtime research synthesis to shared policy
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\render.py`
  - Build shared assistant rail data and split desktop/mobile shells
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\home_magazine.html`
  - Desktop three-column shell, embedded assistant rail styling
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\daily.html`
  - Desktop three-column shell, embedded assistant rail styling
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\topic.html`
  - Desktop three-column shell, embedded assistant rail styling
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\dossier.html`
  - Desktop three-column shell, embedded assistant rail styling
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\archive.html`
  - Keep navigation connectivity and shared style in the new shell
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_render.py`
  - Assert desktop sidebar shell and mobile drawer fallback markers
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\README.md`
  - Document desktop sidebar + mobile drawer runtime assistant behavior

### Task 1: Extend shared research assistant policy

**Files:**
- Create: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_research_assistant_policy.py`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\research_assistant_policy.py`

- [ ] **Step 1: Write the failing policy tests**

```python
import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_assistant_policy import (
    build_company_position_answer,
    build_theme_state_answer,
    finalize_answer_payload,
)


class ResearchAssistantPolicyTests(unittest.TestCase):
    def test_build_theme_state_answer_includes_state_summary_and_decision(self) -> None:
        answer = build_theme_state_answer(
            primary_theme="安全与治理",
            theme_state="emerging",
            summary="这个主题已经形成持续信号。",
            tracking_decision="建议继续跟踪。",
        )
        self.assertIn("emerging", answer)
        self.assertIn("持续信号", answer)
        self.assertIn("建议继续跟踪", answer)

    def test_build_company_position_answer_mentions_theme_and_position(self) -> None:
        answer = build_company_position_answer(
            primary_theme="安全与治理",
            company="Google",
            position="更偏产品功能约束",
            tracking_decision="建议继续跟踪。",
        )
        self.assertIn("Google", answer)
        self.assertIn("安全与治理", answer)
        self.assertIn("更偏产品功能约束", answer)

    def test_finalize_answer_payload_rebuilds_evidence_points_from_items(self) -> None:
        payload = finalize_answer_payload(
            answer="结论",
            question_type="theme_state",
            resolved_theme="安全与治理",
            resolved_company="",
            sources_used=["theme_dossier.json"],
            evidence_items=[
                {
                    "source": "theme_dossier.json",
                    "label": "专题档案",
                    "detail": "当前主题阶段为 emerging。",
                    "reference": "theme-dossier",
                }
            ],
            follow_up_suggestions=["为什么现在是 emerging？"],
            mode_used="rule",
        )
        self.assertEqual(payload["evidence_points"], ["当前主题阶段为 emerging。"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest discover -s tests -p test_research_assistant_policy.py -v
```

Expected: FAIL with import or missing helper errors for the new policy functions.

- [ ] **Step 3: Add the shared answer synthesis helpers**

```python
def build_theme_state_answer(*, primary_theme: str, theme_state: str, summary: str, tracking_decision: str) -> str:
    return f"{primary_theme or '这个主题'} 当前处于 {theme_state or '观察期'}。{summary} {tracking_decision}".strip()


def build_company_position_answer(*, primary_theme: str, company: str, position: str, tracking_decision: str) -> str:
    resolved_position = position or "持续参与但位置尚未完全稳定"
    return f"{company} 在 {primary_theme or '当前主专题'} 里目前更偏向 {resolved_position}。{tracking_decision}".strip()
```

- [ ] **Step 4: Run policy test to verify it passes**

Run:

```bash
python -m unittest discover -s tests -p test_research_assistant_policy.py -v
```

Expected: PASS for all new policy tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_research_assistant_policy.py src/tech_daily/research_assistant_policy.py
git commit -m "test: extend research assistant policy coverage"
```

### Task 2: Delegate more chat answer synthesis to shared policy

**Files:**
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\chat_agent_response.py`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\research_agent_response.py`
- Test: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_chat_agent_response.py`
- Test: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_research_agent_response.py`

- [ ] **Step 1: Write the failing synthesis-focused tests**

```python
def test_answer_chat_question_theme_state_uses_shared_policy_wording(self) -> None:
    answer = answer_chat_question("为什么现在是 emerging？", self.context)
    self.assertIn("当前处于", answer["answer"])
    self.assertIn("建议继续跟踪", answer["answer"])


def test_runtime_research_responder_company_position_uses_shared_policy_shape(self) -> None:
    response = self.responder._rule_answer(self.company_position_context)
    self.assertIn("目前更偏向", response["answer"])
```

- [ ] **Step 2: Run the targeted tests to verify failure**

Run:

```bash
python -m unittest discover -s tests -p test_chat_agent_response.py -v
python -m unittest discover -s tests -p test_research_agent_response.py -v
```

Expected: FAIL because the responders still use ad-hoc string assembly.

- [ ] **Step 3: Replace duplicated string assembly with policy helpers**

```python
from .research_assistant_policy import (
    build_company_position_answer,
    build_theme_state_answer,
    build_timeline_focus_answer,
)

# in chat_agent_response.py
answer = build_theme_state_answer(
    primary_theme=dossier.get("primary_theme", "") or context.get("theme_tracking", {}).get("primary_theme", ""),
    theme_state=state,
    summary=summary,
    tracking_decision=decision,
)

# in research_agent_response.py
answer = build_company_position_answer(
    primary_theme=primary_theme,
    company=entity,
    position=position,
    tracking_decision=tracking_decision,
)
```

- [ ] **Step 4: Run the targeted tests again**

Run:

```bash
python -m unittest discover -s tests -p test_chat_agent_response.py -v
python -m unittest discover -s tests -p test_research_agent_response.py -v
```

Expected: PASS, with unchanged question routing but more consistent answer wording.

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/chat_agent_response.py src/tech_daily/research_agent_response.py tests/test_chat_agent_response.py tests/test_research_agent_response.py
git commit -m "feat: share research assistant answer synthesis"
```

### Task 3: Add assistant rail rendering helpers and desktop shell

**Files:**
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\render.py`
- Test: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_render.py`

- [ ] **Step 1: Write the failing render assertions for the sidebar shell**

```python
self.assertIn("page-shell", html)
self.assertIn("content-grid", html)
self.assertIn("assistant-rail", html)
self.assertIn("assistant-conversation", html)
self.assertIn("assistant-evidence-rail", html)
```

- [ ] **Step 2: Run the render tests to confirm failure**

Run:

```bash
python -m unittest discover -s tests -p test_render.py -v
```

Expected: FAIL because the templates still render full-width shells plus floating launcher-first behavior.

- [ ] **Step 3: Add shared render helpers for sidebar content**

```python
def _render_assistant_rail(context: dict, page_label: str) -> str:
    return (
        "<aside class='assistant-rail'>"
        "<section class='assistant-header'>...</section>"
        "<section class='assistant-prompts'>...</section>"
        "<section class='assistant-conversation'>...</section>"
        "<section class='assistant-evidence-rail'>...</section>"
        "</aside>"
    )
```

- [ ] **Step 4: Run the render tests again**

Run:

```bash
python -m unittest discover -s tests -p test_render.py -v
```

Expected: PASS for the new shell markers in rendered pages.

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/render.py tests/test_render.py
git commit -m "feat: add research assistant rail rendering"
```

### Task 4: Convert desktop pages to left / main / right structure

**Files:**
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\home_magazine.html`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\daily.html`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\topic.html`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\dossier.html`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\templates\archive.html`
- Test: `E:\Jarvis_fun\tech-daily-dashboard\tests\test_render.py`

- [ ] **Step 1: Write the failing layout coverage assertions**

```python
self.assertIn("left-rail", html)
self.assertIn("main-column", html)
self.assertIn("right-rail", html)
self.assertIn("assistant-rail", html)
```

- [ ] **Step 2: Run the render tests to confirm failure**

Run:

```bash
python -m unittest discover -s tests -p test_render.py -v
```

Expected: FAIL because the templates do not yet expose the new three-region desktop shell.

- [ ] **Step 3: Update the templates for desktop shell + mobile fallback**

```html
<main class="page-shell">
  <aside class="left-rail">...</aside>
  <section class="main-column">...</section>
  <aside class="right-rail">
    $assistant_rail
  </aside>
</main>
```

And keep media queries that collapse the right rail and preserve:

```css
@media (max-width: 960px) {
  .right-rail { display: none; }
  .chat-launcher { display: inline-flex; }
}
```

- [ ] **Step 4: Run the render tests again**

Run:

```bash
python -m unittest discover -s tests -p test_render.py -v
```

Expected: PASS, with all pages exposing the new desktop shell and mobile fallback markers.

- [ ] **Step 5: Commit**

```bash
git add templates/home_magazine.html templates/daily.html templates/topic.html templates/dossier.html templates/archive.html tests/test_render.py
git commit -m "feat: add research assistant sidebar layout"
```

### Task 5: Wire interaction behavior and update docs

**Files:**
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\src\tech_daily\render.py`
- Modify: `E:\Jarvis_fun\tech-daily-dashboard\README.md`

- [ ] **Step 1: Write the failing integration expectations**

```python
self.assertIn("data-open-chat", html)
self.assertIn("Research Assistant", html)
self.assertIn("drawer fallback", readme_text)
```

- [ ] **Step 2: Run the affected tests or assertions to confirm failure**

Run:

```bash
python -m unittest discover -s tests -p test_render.py -v
```

Expected: FAIL until the shell and docs reflect sidebar-first behavior.

- [ ] **Step 3: Update JS copy and README wording**

```python
# render.py script text
"当前为桌面端研究侧栏模式；窄屏下会自动回退到抽屉式问答。"
```

```md
## Research Assistant

- Desktop: persistent right sidebar
- Mobile: drawer fallback
- Runtime-first chat remains the primary answer path
```

- [ ] **Step 4: Run final verification**

Run:

```bash
python -m unittest discover -s tests -v
python run_dashboard.py generate-today --output-dir build/site
```

Expected:

- all tests PASS
- report generation prints a summary line such as `report_date=2026-05-18 ...`

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/render.py README.md
git commit -m "docs: document research assistant sidebar mode"
```

## Self-Review

- **Spec coverage:** This plan covers shared answer synthesis, evidence/follow-up reuse, desktop sidebar layout, mobile drawer fallback, and runtime agent prominence. No spec section is left without a task.
- **Placeholder scan:** No `TBD`, `TODO`, or “similar to above” shortcuts remain. Each task includes concrete files, commands, and code direction.
- **Type consistency:** The plan consistently uses `research_assistant_policy.py`, `assistant-rail`, and desktop `left-rail / main-column / right-rail` naming across tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-18-research-assistant-sidebar.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
