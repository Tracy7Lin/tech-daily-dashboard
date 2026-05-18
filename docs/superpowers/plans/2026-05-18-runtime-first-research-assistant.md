# Runtime-First Research Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the web and CLI chat default to a real runtime research assistant that reads daily JSON knowledge artifacts on each question, using the static response bank only as a preview fallback.

**Architecture:** Add a dedicated runtime research assistant pipeline that loads structured daily artifacts, builds question-aware context dynamically, and produces rule/LLM/hybrid answers. Wire both `/api/chat` and CLI `chat` to this pipeline, then demote embedded `response_bank` to a strict fallback path while making runtime mode visible in the UI.

**Tech Stack:** Python, existing `LLMClient`, static HTML templates with embedded JS, `unittest`

---

### Task 1: Add runtime research agent input layer

**Files:**
- Create: `src/tech_daily/research_agent_input.py`
- Modify: `tests/` (new test file below)
- Test: `tests/test_research_agent_input.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_input import load_research_agent_inputs


class ResearchAgentInputTests(unittest.TestCase):
    def test_load_research_agent_inputs_reads_daily_knowledge_files(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir) / "site"
            data_dir = Path(tmpdir) / "data"
            daily_dir = site_dir / "2026-05-18"
            daily_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)

            (daily_dir / "report.json").write_text('{"date":"2026-05-18","headline":"h"}', encoding="utf-8")
            (daily_dir / "daily_intel_brief.json").write_text('{"editorial_signal":"d"}', encoding="utf-8")
            (daily_dir / "cross_day_intel_brief.json").write_text('{"warming_themes":["安全与治理"]}', encoding="utf-8")
            (daily_dir / "theme_tracking_brief.json").write_text('{"primary_theme":"安全与治理"}', encoding="utf-8")
            (daily_dir / "theme_dossier.json").write_text('{"primary_theme":"安全与治理","theme_state":"emerging"}', encoding="utf-8")
            (data_dir / "health_snapshot.json").write_text('{"operator_brief":"ops"}', encoding="utf-8")

            inputs = load_research_agent_inputs(site_dir, data_dir, "2026-05-18")

        self.assertEqual(inputs.report["headline"], "h")
        self.assertEqual(inputs.daily_intel_brief["editorial_signal"], "d")
        self.assertEqual(inputs.cross_day_intel_brief["warming_themes"], ["安全与治理"])
        self.assertEqual(inputs.theme_tracking_brief["primary_theme"], "安全与治理")
        self.assertEqual(inputs.theme_dossier["theme_state"], "emerging")
        self.assertEqual(inputs.health_snapshot["operator_brief"], "ops")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_research_agent_input.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbol for `research_agent_input`

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ResearchAgentInputs:
    report: dict
    daily_intel_brief: dict
    cross_day_intel_brief: dict
    theme_tracking_brief: dict
    theme_dossier: dict
    health_snapshot: dict


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_research_agent_inputs(site_dir: Path, data_dir: Path, report_date: str) -> ResearchAgentInputs:
    daily_dir = site_dir / report_date
    return ResearchAgentInputs(
        report=_load_json(daily_dir / "report.json"),
        daily_intel_brief=_load_json(daily_dir / "daily_intel_brief.json"),
        cross_day_intel_brief=_load_json(daily_dir / "cross_day_intel_brief.json"),
        theme_tracking_brief=_load_json(daily_dir / "theme_tracking_brief.json"),
        theme_dossier=_load_json(daily_dir / "theme_dossier.json"),
        health_snapshot=_load_json(data_dir / "health_snapshot.json"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_research_agent_input.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_research_agent_input.py src/tech_daily/research_agent_input.py
git commit -m "feat: add research agent input loader"
```

### Task 2: Add runtime context builder

**Files:**
- Create: `src/tech_daily/research_agent_context_builder.py`
- Test: `tests/test_research_agent_context_builder.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_context_builder import build_research_context
from tech_daily.research_agent_input import ResearchAgentInputs


class ResearchAgentContextBuilderTests(unittest.TestCase):
    def test_build_research_context_prioritizes_dossier_for_theme_state_questions(self) -> None:
        inputs = ResearchAgentInputs(
            report={"headline": "headline"},
            daily_intel_brief={"editorial_signal": "today"},
            cross_day_intel_brief={"warming_themes": ["安全与治理"]},
            theme_tracking_brief={"primary_theme": "安全与治理"},
            theme_dossier={"primary_theme": "安全与治理", "theme_state": "emerging", "tracking_decision": "继续跟踪"},
            health_snapshot={"operator_brief": "ops"},
        )

        context = build_research_context(
            question="为什么现在是 emerging？",
            question_type="theme_state",
            entity="安全与治理",
            inputs=inputs,
        )

        self.assertEqual(context["primary_source"], "theme_dossier.json")
        self.assertEqual(context["theme_state"], "emerging")
        self.assertEqual(context["tracking_decision"], "继续跟踪")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_research_agent_context_builder.py -v`
Expected: FAIL with missing module or symbol

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from .research_agent_input import ResearchAgentInputs


def build_research_context(question: str, question_type: str, entity: str, inputs: ResearchAgentInputs) -> dict:
    dossier = inputs.theme_dossier or {}
    tracking = inputs.theme_tracking_brief or {}
    cross_day = inputs.cross_day_intel_brief or {}
    report = inputs.report or {}
    health = inputs.health_snapshot or {}
    return {
        "question": question,
        "question_type": question_type,
        "entity": entity,
        "primary_source": "theme_dossier.json" if question_type in {"dossier_summary", "theme_state", "company_position", "timeline_focus"} and dossier else "report.json",
        "report_headline": report.get("headline", ""),
        "editorial_signal": (inputs.daily_intel_brief or {}).get("editorial_signal", ""),
        "primary_theme": dossier.get("primary_theme") or tracking.get("primary_theme", ""),
        "theme_state": dossier.get("theme_state", ""),
        "tracking_decision": dossier.get("tracking_decision", ""),
        "company_positions": dossier.get("company_positions", {}),
        "timeline_events": dossier.get("timeline_events", []),
        "warming_themes": cross_day.get("warming_themes", []),
        "operator_brief": health.get("operator_brief", ""),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_research_agent_context_builder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_research_agent_context_builder.py src/tech_daily/research_agent_context_builder.py
git commit -m "feat: add research agent context builder"
```

### Task 3: Add runtime-first responder and pipeline

**Files:**
- Create: `src/tech_daily/research_agent_response.py`
- Create: `src/tech_daily/research_agent_pipeline.py`
- Modify: `src/tech_daily/chat_agent_pipeline.py`
- Modify: `src/tech_daily/web_chat_server.py`
- Modify: `src/tech_daily/cli.py`
- Test: `tests/test_research_agent_response.py`
- Test: `tests/test_research_agent_pipeline.py`
- Test: `tests/test_web_chat_server.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
import unittest
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_response import ResearchAgentResponder


class ResearchAgentResponseTests(unittest.TestCase):
    def test_responder_uses_llm_for_runtime_first_answer(self) -> None:
        context = {
            "question": "这个主专题现在怎么理解？",
            "question_type": "dossier_summary",
            "primary_theme": "安全与治理",
            "theme_state": "emerging",
            "tracking_decision": "继续跟踪",
            "primary_source": "theme_dossier.json",
        }
        responder = ResearchAgentResponder(mode="hybrid", client=object())

        with patch.object(responder, "_generate_llm_answer", return_value={"answer": "安全与治理仍处萌芽阶段，但值得继续跟踪。", "mode_used": "llm", "evidence_items": []}):
            answer = responder.answer(context)

        self.assertEqual(answer["mode_used"], "llm")
        self.assertIn("萌芽阶段", answer["answer"])
```

```python
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bootstrap import SRC_DIR  # noqa: F401
from tech_daily.research_agent_pipeline import run_research_agent


class ResearchAgentPipelineTests(unittest.TestCase):
    def test_run_research_agent_returns_runtime_answer(self) -> None:
        with TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir) / "site"
            data_dir = Path(tmpdir) / "data"
            daily_dir = site_dir / "2026-05-18"
            daily_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            for name, payload in {
                "report.json": '{"date":"2026-05-18","headline":"h"}',
                "daily_intel_brief.json": '{"editorial_signal":"d"}',
                "cross_day_intel_brief.json": '{"warming_themes":["安全与治理"]}',
                "theme_tracking_brief.json": '{"primary_theme":"安全与治理"}',
                "theme_dossier.json": '{"primary_theme":"安全与治理","theme_state":"emerging","tracking_decision":"继续跟踪"}',
            }.items():
                (daily_dir / name).write_text(payload, encoding="utf-8")
            (data_dir / "health_snapshot.json").write_text('{"operator_brief":"ops"}', encoding="utf-8")

            with patch("tech_daily.research_agent_pipeline._build_responder") as mock_builder:
                mock_builder.return_value.answer.return_value = {
                    "answer": "安全与治理仍处萌芽阶段。",
                    "mode_used": "llm",
                    "question_type": "theme_state",
                    "evidence_items": [],
                }
                result = run_research_agent(site_dir, data_dir, "2026-05-18", "为什么现在是 emerging？")

        self.assertEqual(result["mode_used"], "llm")
        self.assertEqual(result["question_type"], "theme_state")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
- `python -m unittest discover -s tests -p test_research_agent_response.py -v`
- `python -m unittest discover -s tests -p test_research_agent_pipeline.py -v`
Expected: FAIL with missing module/symbols

- [ ] **Step 3: Write minimal implementation**

```python
# src/tech_daily/research_agent_response.py
from __future__ import annotations

from .llm_client import LLMClient, LLMClientError


class ResearchAgentResponder:
    def __init__(self, mode: str, client: LLMClient | None) -> None:
        self.mode = mode
        self.client = client

    def answer(self, context: dict) -> dict:
        rule_answer = self._rule_answer(context)
        if self.mode == "rule" or self.client is None or not self.client.is_available():
            return rule_answer
        try:
            return self._generate_llm_answer(context, rule_answer)
        except (LLMClientError, KeyError, TypeError, ValueError):
            return rule_answer
```

```python
# src/tech_daily/research_agent_pipeline.py
from __future__ import annotations

from pathlib import Path

from .llm_client import LLMClient
from .research_agent_context_builder import build_research_context
from .research_agent_input import load_research_agent_inputs
from .chat_agent_analysis import classify_chat_question
from .settings import DEFAULT_SETTINGS
from .research_agent_response import ResearchAgentResponder


def _build_responder() -> ResearchAgentResponder:
    client = LLMClient(
        api_url=DEFAULT_SETTINGS.llm_api_url,
        api_key=DEFAULT_SETTINGS.llm_api_key,
        model=DEFAULT_SETTINGS.llm_model,
        timeout_seconds=DEFAULT_SETTINGS.llm_timeout_seconds,
    )
    return ResearchAgentResponder(mode=DEFAULT_SETTINGS.editorial_mode, client=client)


def run_research_agent(site_dir: Path, data_dir: Path, report_date: str, question: str) -> dict:
    question_type, entity = classify_chat_question(question, [])
    inputs = load_research_agent_inputs(site_dir, data_dir, report_date)
    context = build_research_context(question, question_type, entity, inputs)
    response = _build_responder().answer(context)
    response.setdefault("question_type", question_type)
    return response
```

Then update existing consumers so:
- `handle_chat_request` calls `run_research_agent`
- CLI `chat` calls `run_research_agent`
- `chat_agent_pipeline.build_embedded_chat_context` still builds `response_bank`, but only with `mode="rule"`

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:
- `python -m unittest discover -s tests -p test_research_agent_response.py -v`
- `python -m unittest discover -s tests -p test_research_agent_pipeline.py -v`
- `python -m unittest discover -s tests -p test_web_chat_server.py -v`
- `python -m unittest discover -s tests -p test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/research_agent_response.py src/tech_daily/research_agent_pipeline.py src/tech_daily/chat_agent_pipeline.py src/tech_daily/web_chat_server.py src/tech_daily/cli.py tests/test_research_agent_response.py tests/test_research_agent_pipeline.py tests/test_web_chat_server.py tests/test_cli.py
git commit -m "feat: add runtime-first research assistant"
```

### Task 4: Make embedded chat explicit fallback only

**Files:**
- Modify: `src/tech_daily/render.py`
- Modify: `src/tech_daily/chat_agent_response.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
def test_render_daily_chat_shell_explains_static_preview_mode(self) -> None:
    report = DailyReport(
        date="2026-05-18",
        headline="headline",
        hottest_topics=[],
        total_entries=0,
        companies_covered=0,
        chat_agent_context={
            "report_date": "2026-05-18",
            "runtime_chat": {
                "endpoint": "/api/chat",
                "health_endpoint": "/api/health",
                "serve_hint": "使用 python run_dashboard.py serve --port 8080 启动实时问答服务。",
            },
            "response_bank": {},
        },
    )
    html = render_daily(report)
    assert "静态预览模式" in html
    assert "/api/health" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_render.py -v`
Expected: FAIL on missing explicit runtime-first preview wording

- [ ] **Step 3: Write minimal implementation**

Update:
- `render.py` status copy to explicitly say:
  - runtime-first when health succeeds
  - static preview fallback when health fails or `file://`
- `chat_agent_response.py` context builder to expose runtime metadata only, not imply that `response_bank` is the primary path

Use copy like:

```javascript
setStatus(`当前处于静态预览模式，正在使用内嵌回答。${runtimeServeHint}`, 'fallback');
```

and

```javascript
setStatus(payload.runtime_hint || '实时增强问答已连接。', 'enhanced');
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_render.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/render.py src/tech_daily/chat_agent_response.py tests/test_render.py
git commit -m "fix: demote embedded chat to preview fallback"
```

### Task 5: Verify end-to-end and update docs

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-05-17-next-phase-plan.md`
- Test: full suite

- [ ] **Step 1: Update runtime usage docs**

Add to `README.md`:

```md
### Real-time Research Assistant

To use the runtime-first chat instead of static preview fallback:

```powershell
python run_dashboard.py generate-today --output-dir build/site
python run_dashboard.py serve --port 8080
```

Then open `http://127.0.0.1:8080`.
```

Also note:
- `file://` pages are preview mode only
- `/api/health` exposes whether runtime LLM is available

- [ ] **Step 2: Update next-phase status**

Mark `Runtime-First Research Assistant` as implemented in `docs/2026-05-17-next-phase-plan.md`.

- [ ] **Step 3: Run full verification**

Run:
- `python -m unittest discover -s tests -v`
- `python run_dashboard.py generate-today --output-dir build/site`
- `python run_dashboard.py chat --date 2026-05-18 --question "这个主专题现在怎么理解？"`

Expected:
- All tests PASS
- Site generation succeeds
- CLI chat returns runtime answer with `mode_used=llm` or `rule` depending on runtime settings, but through the new research assistant path

- [ ] **Step 4: Commit**

```bash
git add README.md docs/2026-05-17-next-phase-plan.md
git commit -m "docs: document runtime-first research assistant"
```

- [ ] **Step 5: Push milestone**

```bash
git push
```
