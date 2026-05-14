# Minimal Intel Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first minimal intel analysis agent that reads the generated report and health snapshot, produces a unified `daily_intel_brief`, writes a Markdown report, and renders an agent analysis section into the daily dashboard.

**Architecture:** Add four focused modules: `agent_input`, `agent_analysis`, `agent_outputs`, and `agent_pipeline`. The existing dashboard pipeline remains primary; the agent runs afterward as an enhancement step and degrades cleanly if analysis or output generation fails.

**Tech Stack:** Python 3.11, `unittest`, existing capability layer, JSON report artifacts, Markdown output, existing static renderer

---

## File Structure

### New files

- `src/tech_daily/agent_input.py`
  - Load `report.json` and `health_snapshot.json` into structured agent input payloads.
- `src/tech_daily/agent_analysis.py`
  - Build the structured `daily_intel_brief` result from report and health snapshot data.
- `src/tech_daily/agent_outputs.py`
  - Persist `daily_intel_brief.json`, render `agent-brief.md`, and shape page block data.
- `src/tech_daily/agent_pipeline.py`
  - Orchestrate agent input loading, analysis, output writing, and graceful fallback.
- `tests/test_agent_input.py`
  - Verify report and snapshot loading behavior.
- `tests/test_agent_analysis.py`
  - Verify structured analysis output.
- `tests/test_agent_outputs.py`
  - Verify JSON and Markdown outputs.
- `tests/test_agent_pipeline.py`
  - Verify orchestration and graceful failure behavior.

### Modified files

- `src/tech_daily/models.py`
  - Add lightweight dataclasses for `DailyIntelBrief` and optional page block data.
- `src/tech_daily/pipeline.py`
  - Invoke agent pipeline after report generation and attach result to `DailyReport`.
- `src/tech_daily/render.py`
  - Render the agent analysis block when agent output is present.
- `tests/test_pipeline.py`
  - Verify the dashboard pipeline still returns a report and now tolerates agent augmentation.
- `tests/test_render.py`
  - Verify the daily page includes the new agent section and degrades safely.
- `README.md`
  - Document the minimal intel agent outputs and architecture.
- `docs/2026-05-13-improvement-roadmap.md`
  - Note that the minimal intel agent line has started.

## Task 1: Add agent input loading

**Files:**
- Create: `src/tech_daily/agent_input.py`
- Test: `tests/test_agent_input.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.agent_input import load_agent_inputs


class AgentInputTests(unittest.TestCase):
    def test_load_agent_inputs_reads_report_and_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_dir = root / "site" / "2026-05-14"
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(json.dumps({"date": "2026-05-14", "headline": "headline"}), encoding="utf-8")
            snapshot_dir = root / "data"
            snapshot_dir.mkdir(parents=True)
            (snapshot_dir / "health_snapshot.json").write_text(json.dumps({"ops_status_analysis": {"operator_brief": "brief"}}), encoding="utf-8")

            payload = load_agent_inputs(report_dir / "report.json", snapshot_dir / "health_snapshot.json")

        self.assertEqual(payload.report["date"], "2026-05-14")
        self.assertEqual(payload.health_snapshot["ops_status_analysis"]["operator_brief"], "brief")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_agent_input.py" -v`  
Expected: FAIL with missing `tech_daily.agent_input`

- [ ] **Step 3: Write minimal implementation**

```python
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AgentInputs:
    report: dict
    health_snapshot: dict


def load_agent_inputs(report_path: Path, snapshot_path: Path) -> AgentInputs:
    return AgentInputs(
        report=json.loads(report_path.read_text(encoding="utf-8")),
        health_snapshot=json.loads(snapshot_path.read_text(encoding="utf-8")),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p "test_agent_input.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/agent_input.py tests/test_agent_input.py
git commit -m "feat: add agent input loader"
```

## Task 2: Add structured agent analysis

**Files:**
- Create: `src/tech_daily/agent_analysis.py`
- Modify: `src/tech_daily/models.py`
- Test: `tests/test_agent_analysis.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from tech_daily.agent_analysis import analyze_daily_intel


class AgentAnalysisTests(unittest.TestCase):
    def test_analyze_daily_intel_builds_structured_brief(self) -> None:
        report = {
            "date": "2026-05-14",
            "headline": "today headline",
            "hottest_topics": ["安全与治理", "模型与能力发布"],
            "active_companies": ["OpenAI", "Google"],
        }
        snapshot = {
            "ops_status_analysis": {
                "operator_brief": "当前优先处理 tesla；最近已恢复 alibaba。",
                "high_priority": [{"company_slug": "tesla"}],
                "recently_recovered": [{"company_slug": "alibaba"}],
            }
        }

        brief = analyze_daily_intel(report, snapshot)

        self.assertEqual(brief.report_date, "2026-05-14")
        self.assertTrue(brief.editorial_signal)
        self.assertTrue(brief.ops_signal)
        self.assertIn("安全与治理", brief.top_content_themes)
        self.assertIn("tesla", "".join(brief.source_risks))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_agent_analysis.py" -v`  
Expected: FAIL with missing `tech_daily.agent_analysis`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, asdict, field


@dataclass(slots=True)
class DailyIntelBrief:
    report_date: str
    editorial_signal: str
    ops_signal: str
    top_content_themes: list[str] = field(default_factory=list)
    watchlist: list[str] = field(default_factory=list)
    source_risks: list[str] = field(default_factory=list)
    recoveries: list[str] = field(default_factory=list)
    tomorrow_focus: list[str] = field(default_factory=list)
    mode_used: str = "rule"

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_daily_intel(report: dict, health_snapshot: dict) -> DailyIntelBrief:
    ops = health_snapshot.get("ops_status_analysis", {})
    themes = report.get("hottest_topics", [])[:3]
    source_risks = [item.get("company_slug", "") for item in ops.get("high_priority", [])[:3]]
    recoveries = [item.get("company_slug", "") for item in ops.get("recently_recovered", [])[:3]]
    watchlist = list(dict.fromkeys(themes + source_risks))[:4]
    return DailyIntelBrief(
        report_date=report.get("date", ""),
        editorial_signal=report.get("headline", ""),
        ops_signal=ops.get("operator_brief", "当前无额外运维判断。"),
        top_content_themes=themes,
        watchlist=watchlist,
        source_risks=source_risks,
        recoveries=recoveries,
        tomorrow_focus=watchlist[:3],
        mode_used="hybrid",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p "test_agent_analysis.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/agent_analysis.py src/tech_daily/models.py tests/test_agent_analysis.py
git commit -m "feat: add daily intel analysis"
```

## Task 3: Add agent outputs

**Files:**
- Create: `src/tech_daily/agent_outputs.py`
- Test: `tests/test_agent_outputs.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.agent_analysis import DailyIntelBrief
from tech_daily.agent_outputs import write_agent_outputs


class AgentOutputsTests(unittest.TestCase):
    def test_write_agent_outputs_persists_json_and_markdown(self) -> None:
        brief = DailyIntelBrief(
            report_date="2026-05-14",
            editorial_signal="内容判断",
            ops_signal="运维判断",
            top_content_themes=["安全与治理"],
            watchlist=["tesla"],
            source_risks=["tesla"],
            recoveries=["alibaba"],
            tomorrow_focus=["安全与治理"],
            mode_used="hybrid",
        )
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_agent_outputs(brief, output_dir)

            brief_json = json.loads((output_dir / "daily_intel_brief.json").read_text(encoding="utf-8"))
            brief_md = (output_dir / "agent-brief.md").read_text(encoding="utf-8")

        self.assertEqual(result["json_path"].name, "daily_intel_brief.json")
        self.assertEqual(brief_json["report_date"], "2026-05-14")
        self.assertIn("今日核心判断", brief_md)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_agent_outputs.py" -v`  
Expected: FAIL with missing `tech_daily.agent_outputs`

- [ ] **Step 3: Write minimal implementation**

```python
import json
from pathlib import Path


def render_agent_markdown(brief) -> str:
    return (
        f"# {brief.report_date} 情报判断\n\n"
        f"## 今日核心判断\n{brief.editorial_signal}\n\n"
        f"## 运维状态\n{brief.ops_signal}\n\n"
        f"## 明日关注点\n- " + "\n- ".join(brief.tomorrow_focus)
    )


def write_agent_outputs(brief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "daily_intel_brief.json"
    md_path = output_dir / "agent-brief.md"
    json_path.write_text(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_agent_markdown(brief), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": md_path}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p "test_agent_outputs.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/agent_outputs.py tests/test_agent_outputs.py
git commit -m "feat: add agent outputs"
```

## Task 4: Add agent pipeline and graceful fallback

**Files:**
- Create: `src/tech_daily/agent_pipeline.py`
- Test: `tests/test_agent_pipeline.py`
- Modify: `src/tech_daily/pipeline.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.agent_pipeline import run_agent_pipeline


class AgentPipelineTests(unittest.TestCase):
    def test_run_agent_pipeline_generates_brief_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_dir = root / "2026-05-14"
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(json.dumps({"date": "2026-05-14", "headline": "headline", "hottest_topics": []}), encoding="utf-8")
            snapshot_path = root / "health_snapshot.json"
            snapshot_path.write_text(json.dumps({"ops_status_analysis": {"operator_brief": "ops"}}), encoding="utf-8")

            result = run_agent_pipeline(report_dir / "report.json", snapshot_path)

        self.assertTrue(result["brief"])
        self.assertTrue(result["outputs"]["json_path"].exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_agent_pipeline.py" -v`  
Expected: FAIL with missing `tech_daily.agent_pipeline`

- [ ] **Step 3: Write minimal implementation and dashboard integration**

```python
def run_agent_pipeline(report_path: Path, snapshot_path: Path) -> dict:
    inputs = load_agent_inputs(report_path, snapshot_path)
    brief = analyze_daily_intel(inputs.report, inputs.health_snapshot)
    outputs = write_agent_outputs(brief, report_path.parent)
    return {"brief": brief, "outputs": outputs}
```

And in `pipeline.py`:

```python
report = build_daily_report(date_str)
write_site(report, destination)
report_json_path = destination / report.date / "report.json"
snapshot_path = Path(DEFAULT_SETTINGS.data_output_dir) / "health_snapshot.json"
try:
    agent_result = run_agent_pipeline(report_json_path, snapshot_path)
except Exception:
    agent_result = None
return report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p "test_agent_pipeline.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/agent_pipeline.py src/tech_daily/pipeline.py tests/test_agent_pipeline.py tests/test_pipeline.py
git commit -m "feat: add agent pipeline orchestration"
```

## Task 5: Render the agent block in the daily page

**Files:**
- Modify: `src/tech_daily/render.py`
- Modify: `templates/daily.html`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
def test_render_daily_includes_agent_brief_block_when_present(self) -> None:
    report = build_report_with_agent_brief()
    html = render_daily(report)
    self.assertIn("情报判断", html)
    self.assertIn("今日核心判断", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_render.py" -v`  
Expected: FAIL because no agent block is rendered yet

- [ ] **Step 3: Write minimal implementation**

```python
def _render_agent_brief(brief: dict | None) -> str:
    if not brief:
        return ""
    return (
        "<section class='card agent-brief-card'>"
        "<h2>情报判断</h2>"
        f"<p class='section-copy'><strong>今日核心判断：</strong>{html.escape(brief['editorial_signal'])}</p>"
        f"<p class='section-copy'><strong>运维提示：</strong>{html.escape(brief['ops_signal'])}</p>"
        f"<p class='section-copy'><strong>明日关注：</strong>{html.escape('、'.join(brief['tomorrow_focus']))}</p>"
        f"<p><a class='inline-link' href='./agent-brief.md'>查看完整 Markdown 报告</a></p>"
        "</section>"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p "test_render.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/render.py templates/daily.html tests/test_render.py
git commit -m "feat: render agent brief section"
```

## Task 6: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-05-13-improvement-roadmap.md`

- [ ] **Step 1: Write the documentation assertions**

```python
def test_readme_mentions_agent_brief_outputs():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "agent-brief.md" in text
    assert "daily_intel_brief.json" in text
```

- [ ] **Step 2: Run focused checks for the new agent modules**

Run: `python -m unittest discover -s tests -p "test_agent_*.py" -v`  
Expected: PASS

- [ ] **Step 3: Update documentation**

```markdown
- `build/site/<date>/daily_intel_brief.json`
- `build/site/<date>/agent-brief.md`
- `agent_pipeline.py`: 最小情报分析 agent 编排入口
```

- [ ] **Step 4: Run full verification**

Run: `python -m unittest discover -s tests -v`  
Expected: PASS with all tests green

Run: `python run_dashboard.py generate-today --output-dir build/site`  
Expected: exit `0` and `build/site/<today>/daily_intel_brief.json` plus `agent-brief.md` exist

Run: `python run_dashboard.py health-check`  
Expected: exit `0` and `build/data/health_snapshot.json` still contains `ops_status_analysis`

- [ ] **Step 5: Commit**

```bash
git add README.md docs/2026-05-13-improvement-roadmap.md
git commit -m "docs: document minimal intel agent outputs"
```

## Self-Review

### Spec coverage

- Read report and snapshot: Task 1
- Build unified structured brief: Task 2
- Output JSON + Markdown: Task 3
- Orchestrate after dashboard generation: Task 4
- Render page analysis block: Task 5
- Degrade safely and preserve health snapshot behavior: Tasks 4 and 6

### Placeholder scan

- No `TODO` or `TBD` markers remain
- Every task contains explicit files, commands, and code blocks

### Type consistency

- `DailyIntelBrief` is the single structured object used across analysis and output
- `ops_status_analysis` remains the source for ops interpretation
- Page block consumes the same structured brief that Markdown and JSON use
