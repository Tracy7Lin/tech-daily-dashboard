# Cross-Day Intel Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a second-stage cross-day tracking agent that reads recent daily reports and historical health snapshots, produces a unified `cross_day_intel_brief`, writes a Markdown report, and renders a `跨日观察` section into the daily dashboard.

**Architecture:** Extend the existing enhancement chain after the minimal intel agent. First, persist dated health snapshots so runtime history is available as first-class input. Then add four focused modules: `cross_day_input`, `cross_day_analysis`, `cross_day_outputs`, and `cross_day_pipeline`. The main report pipeline remains primary; the cross-day agent runs afterward as a degradable enhancement and must never break daily report generation.

**Tech Stack:** Python 3.11, `unittest`, existing pipeline/agent architecture, JSON report artifacts, Markdown output, existing static renderer

---

## File Structure

### New files

- `src/tech_daily/cross_day_input.py`
  - Load recent `report.json`, optional `daily_intel_brief.json`, and dated `health_snapshot` history into a normalized input payload.
- `src/tech_daily/cross_day_analysis.py`
  - Build the structured `cross_day_intel_brief` result from recent reports and runtime history.
- `src/tech_daily/cross_day_outputs.py`
  - Persist `cross_day_intel_brief.json`, render `cross-day-brief.md`, and shape page block data.
- `src/tech_daily/cross_day_pipeline.py`
  - Orchestrate cross-day input loading, analysis, output writing, and graceful fallback.
- `tests/test_cross_day_input.py`
  - Verify recent-day loading and fallback when optional artifacts are missing.
- `tests/test_cross_day_analysis.py`
  - Verify warming/cooling themes, steady/swing companies, and runtime risk/recovery summaries.
- `tests/test_cross_day_outputs.py`
  - Verify JSON and Markdown output rendering.
- `tests/test_cross_day_pipeline.py`
  - Verify orchestration and graceful fallback behavior.

### Modified files

- `src/tech_daily/models.py`
  - Add lightweight dataclasses for `CrossDayIntelBrief` and optional page block data.
- `src/tech_daily/healthcheck.py`
  - Persist a dated copy of `health_snapshot.json` into `build/data/health_snapshots/<date>.json`.
- `src/tech_daily/pipeline.py`
  - Invoke `cross_day_pipeline` after the v1 agent and attach result to `DailyReport`.
- `src/tech_daily/render.py`
  - Render the `跨日观察` block when cross-day output is present.
- `templates/daily.html`
  - Add a section placeholder for `跨日观察`.
- `tests/test_healthcheck.py`
  - Verify dated health snapshots are persisted.
- `tests/test_pipeline.py`
  - Verify the dashboard pipeline tolerates cross-day augmentation and failure.
- `tests/test_render.py`
  - Verify the daily page includes the new `跨日观察` section and degrades safely.
- `README.md`
  - Document cross-day outputs and dated health snapshot history.
- `docs/2026-05-13-improvement-roadmap.md`
  - Note that the cross-day tracking agent line has started.

## Task 1: Persist dated health snapshots

**Files:**
- Modify: `src/tech_daily/healthcheck.py`
- Test: `tests/test_healthcheck.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.healthcheck import write_health_snapshot


class HealthSnapshotHistoryTests(unittest.TestCase):
    def test_write_health_snapshot_persists_latest_and_dated_copy(self) -> None:
        payload = {
            "generated_at": "2026-05-15T08:30:00+08:00",
            "report_date": "2026-05-15",
            "ops_status_analysis": {"operator_brief": "brief"},
        }

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            latest_path = root / "health_snapshot.json"
            history_dir = root / "health_snapshots"

            write_health_snapshot(payload, latest_path, history_dir)

            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            dated = json.loads((history_dir / "2026-05-15.json").read_text(encoding="utf-8"))

        self.assertEqual(latest["report_date"], "2026-05-15")
        self.assertEqual(dated["ops_status_analysis"]["operator_brief"], "brief")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_healthcheck.py" -v`  
Expected: FAIL because `write_health_snapshot` does not accept a history directory or does not create the dated copy.

- [ ] **Step 3: Write minimal implementation**

```python
def write_health_snapshot(payload: dict, latest_path: Path, history_dir: Path | None = None) -> Path:
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if history_dir is not None:
        report_date = payload.get("report_date")
        if report_date:
            history_dir.mkdir(parents=True, exist_ok=True)
            history_path = history_dir / f"{report_date}.json"
            history_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return latest_path
```

- [ ] **Step 4: Update health-check callers**

```python
history_dir = snapshot_path.parent / "health_snapshots"
write_health_snapshot(payload, snapshot_path, history_dir)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_healthcheck.py" -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/tech_daily/healthcheck.py tests/test_healthcheck.py
git commit -m "feat: persist dated health snapshots"
```

## Task 2: Add cross-day input loading

**Files:**
- Create: `src/tech_daily/cross_day_input.py`
- Test: `tests/test_cross_day_input.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.cross_day_input import load_cross_day_inputs


class CrossDayInputTests(unittest.TestCase):
    def test_load_cross_day_inputs_reads_recent_reports_and_snapshots(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            data_dir = root / "data" / "health_snapshots"
            data_dir.mkdir(parents=True)

            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps({"date": date_text, "active_companies": ["OpenAI"]}),
                    encoding="utf-8",
                )
                (data_dir / f"{date_text}.json").write_text(
                    json.dumps({"report_date": date_text, "ops_status_analysis": {"operator_brief": f"brief-{date_text}"}}),
                    encoding="utf-8",
                )

            payload = load_cross_day_inputs(site_dir, data_dir, end_date="2026-05-15", days=3)

        self.assertEqual(payload.date_range, ("2026-05-13", "2026-05-15"))
        self.assertEqual(len(payload.reports), 3)
        self.assertEqual(payload.snapshots[-1]["ops_status_analysis"]["operator_brief"], "brief-2026-05-15")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_cross_day_input.py" -v`  
Expected: FAIL with missing `tech_daily.cross_day_input`

- [ ] **Step 3: Write minimal implementation**

```python
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(slots=True)
class CrossDayInputs:
    date_range: tuple[str, str]
    reports: list[dict]
    intel_briefs: list[dict]
    snapshots: list[dict]


def load_cross_day_inputs(site_dir: Path, snapshot_history_dir: Path, end_date: str, days: int) -> CrossDayInputs:
    end_day = date.fromisoformat(end_date)
    dates = [(end_day - timedelta(days=offset)).isoformat() for offset in reversed(range(days))]
    reports: list[dict] = []
    intel_briefs: list[dict] = []
    snapshots: list[dict] = []
    for date_text in dates:
        report_path = site_dir / date_text / "report.json"
        if report_path.exists():
            reports.append(json.loads(report_path.read_text(encoding="utf-8")))
        intel_path = site_dir / date_text / "daily_intel_brief.json"
        if intel_path.exists():
            intel_briefs.append(json.loads(intel_path.read_text(encoding="utf-8")))
        snapshot_path = snapshot_history_dir / f"{date_text}.json"
        if snapshot_path.exists():
            snapshots.append(json.loads(snapshot_path.read_text(encoding="utf-8")))
    return CrossDayInputs(
        date_range=(dates[0], dates[-1]),
        reports=reports,
        intel_briefs=intel_briefs,
        snapshots=snapshots,
    )
```

- [ ] **Step 4: Add fallback coverage for missing optional intel briefs**

```python
def test_load_cross_day_inputs_tolerates_missing_daily_intel_briefs(self) -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        site_dir = root / "site"
        data_dir = root / "data" / "health_snapshots"
        data_dir.mkdir(parents=True)

        report_dir = site_dir / "2026-05-15"
        report_dir.mkdir(parents=True)
        (report_dir / "report.json").write_text(
            json.dumps({"date": "2026-05-15", "active_companies": ["OpenAI"]}),
            encoding="utf-8",
        )
        (data_dir / "2026-05-15.json").write_text(
            json.dumps({"report_date": "2026-05-15"}),
            encoding="utf-8",
        )

        payload = load_cross_day_inputs(site_dir, data_dir, end_date="2026-05-15", days=1)

    self.assertEqual(len(payload.reports), 1)
    self.assertEqual(payload.intel_briefs, [])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_cross_day_input.py" -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/tech_daily/cross_day_input.py tests/test_cross_day_input.py
git commit -m "feat: add cross-day input loader"
```

## Task 3: Add structured cross-day analysis

**Files:**
- Create: `src/tech_daily/cross_day_analysis.py`
- Modify: `src/tech_daily/models.py`
- Test: `tests/test_cross_day_analysis.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from tech_daily.cross_day_analysis import analyze_cross_day_intel


class CrossDayAnalysisTests(unittest.TestCase):
    def test_analyze_cross_day_intel_builds_structured_brief(self) -> None:
        reports = [
            {"date": "2026-05-13", "hottest_topics": ["安全与治理"], "active_companies": ["OpenAI", "Google"]},
            {"date": "2026-05-14", "hottest_topics": ["安全与治理", "模型与能力发布"], "active_companies": ["OpenAI"]},
            {"date": "2026-05-15", "hottest_topics": ["模型与能力发布"], "active_companies": ["OpenAI", "Anthropic"]},
        ]
        snapshots = [
            {"report_date": "2026-05-13", "high_priority_runtime_issues": [{"company_slug": "tesla"}], "recently_recovered_runtime_issues": []},
            {"report_date": "2026-05-14", "high_priority_runtime_issues": [{"company_slug": "tesla"}], "recently_recovered_runtime_issues": [{"company_slug": "alibaba"}]},
            {"report_date": "2026-05-15", "high_priority_runtime_issues": [{"company_slug": "tesla"}], "recently_recovered_runtime_issues": [{"company_slug": "xiaomi"}]},
        ]

        brief = analyze_cross_day_intel(
            date_range=("2026-05-13", "2026-05-15"),
            reports=reports,
            intel_briefs=[],
            snapshots=snapshots,
        )

        self.assertEqual(brief.date_range, ("2026-05-13", "2026-05-15"))
        self.assertIn("安全与治理", brief.warming_themes)
        self.assertIn("OpenAI", brief.steady_companies)
        self.assertIn("tesla", brief.persistent_source_risks)
        self.assertTrue(brief.next_day_focus)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_cross_day_analysis.py" -v`  
Expected: FAIL with missing `tech_daily.cross_day_analysis`

- [ ] **Step 3: Write minimal implementation**

```python
from collections import Counter
from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class CrossDayIntelBrief:
    date_range: tuple[str, str]
    warming_themes: list[str] = field(default_factory=list)
    cooling_themes: list[str] = field(default_factory=list)
    steady_companies: list[str] = field(default_factory=list)
    swing_companies: list[str] = field(default_factory=list)
    persistent_source_risks: list[str] = field(default_factory=list)
    recent_source_recoveries: list[str] = field(default_factory=list)
    watchlist: list[str] = field(default_factory=list)
    next_day_focus: list[str] = field(default_factory=list)
    mode_used: str = "hybrid"

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_cross_day_intel(date_range, reports, intel_briefs, snapshots) -> CrossDayIntelBrief:
    theme_counts = Counter(theme for report in reports for theme in report.get("hottest_topics", []))
    company_counts = Counter(company for report in reports for company in report.get("active_companies", []))
    persistent_risks = Counter(
        issue.get("company_slug", "")
        for snapshot in snapshots
        for issue in snapshot.get("high_priority_runtime_issues", [])
    )
    recoveries = []
    for snapshot in snapshots:
        for issue in snapshot.get("recently_recovered_runtime_issues", []):
            slug = issue.get("company_slug", "")
            if slug and slug not in recoveries:
                recoveries.append(slug)
    steady_companies = [name for name, count in company_counts.items() if count >= 2]
    swing_companies = [name for name, count in company_counts.items() if count == 1]
    warming_themes = [name for name, count in theme_counts.items() if count >= 2]
    cooling_themes = [name for name, count in theme_counts.items() if count == 1]
    persistent_source_risks = [name for name, count in persistent_risks.items() if name and count >= 2]
    watchlist = list(dict.fromkeys(warming_themes + steady_companies + persistent_source_risks))[:5]
    return CrossDayIntelBrief(
        date_range=date_range,
        warming_themes=warming_themes[:3],
        cooling_themes=cooling_themes[:3],
        steady_companies=steady_companies[:4],
        swing_companies=swing_companies[:4],
        persistent_source_risks=persistent_source_risks[:4],
        recent_source_recoveries=recoveries[:4],
        watchlist=watchlist,
        next_day_focus=watchlist[:3],
        mode_used="hybrid",
    )
```

- [ ] **Step 4: Add cooling/swing-specific coverage**

```python
def test_analyze_cross_day_intel_marks_single_day_entities_as_cooling_or_swing(self) -> None:
    reports = [
        {"date": "2026-05-14", "hottest_topics": ["安全与治理"], "active_companies": ["OpenAI"]},
        {"date": "2026-05-15", "hottest_topics": ["客户落地案例"], "active_companies": ["Anthropic"]},
    ]

    brief = analyze_cross_day_intel(
        date_range=("2026-05-14", "2026-05-15"),
        reports=reports,
        intel_briefs=[],
        snapshots=[],
    )

    self.assertIn("客户落地案例", brief.cooling_themes)
    self.assertIn("Anthropic", brief.swing_companies)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_cross_day_analysis.py" -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/tech_daily/cross_day_analysis.py src/tech_daily/models.py tests/test_cross_day_analysis.py
git commit -m "feat: add cross-day intel analysis"
```

## Task 4: Add cross-day outputs

**Files:**
- Create: `src/tech_daily/cross_day_outputs.py`
- Test: `tests/test_cross_day_outputs.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.cross_day_analysis import CrossDayIntelBrief
from tech_daily.cross_day_outputs import write_cross_day_outputs


class CrossDayOutputsTests(unittest.TestCase):
    def test_write_cross_day_outputs_persists_json_and_markdown(self) -> None:
        brief = CrossDayIntelBrief(
            date_range=("2026-05-13", "2026-05-15"),
            warming_themes=["安全与治理"],
            cooling_themes=["客户落地案例"],
            steady_companies=["OpenAI"],
            swing_companies=["Anthropic"],
            persistent_source_risks=["tesla"],
            recent_source_recoveries=["alibaba"],
            watchlist=["安全与治理", "tesla"],
            next_day_focus=["安全与治理"],
            mode_used="hybrid",
        )

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_cross_day_outputs(brief, output_dir)
            brief_json = json.loads((output_dir / "cross_day_intel_brief.json").read_text(encoding="utf-8"))
            brief_md = (output_dir / "cross-day-brief.md").read_text(encoding="utf-8")

        self.assertEqual(result["json_path"].name, "cross_day_intel_brief.json")
        self.assertEqual(brief_json["steady_companies"], ["OpenAI"])
        self.assertIn("最近几天主线", brief_md)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_cross_day_outputs.py" -v`  
Expected: FAIL with missing `tech_daily.cross_day_outputs`

- [ ] **Step 3: Write minimal implementation**

```python
import json
from pathlib import Path


def render_cross_day_markdown(brief) -> str:
    return (
        f"# {brief.date_range[0]} 至 {brief.date_range[1]} 跨日观察\n\n"
        "## 最近几天主线\n"
        + ("\n".join(f"- {item}" for item in brief.warming_themes) or "- 暂无明显升温主题")
        + "\n\n## 明日观察清单\n"
        + ("\n".join(f"- {item}" for item in brief.next_day_focus) or "- 暂无额外观察项")
    )


def build_cross_day_page_block(brief) -> dict:
    return {
        "title": "跨日观察",
        "date_range": list(brief.date_range),
        "warming_themes": brief.warming_themes,
        "steady_companies": brief.steady_companies,
        "persistent_source_risks": brief.persistent_source_risks,
        "recent_source_recoveries": brief.recent_source_recoveries,
        "next_day_focus": brief.next_day_focus,
    }


def write_cross_day_outputs(brief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cross_day_intel_brief.json"
    md_path = output_dir / "cross-day-brief.md"
    json_path.write_text(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_cross_day_markdown(brief), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": md_path, "page_block": build_cross_day_page_block(brief)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_cross_day_outputs.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/cross_day_outputs.py tests/test_cross_day_outputs.py
git commit -m "feat: add cross-day outputs"
```

## Task 5: Add cross-day pipeline and page integration

**Files:**
- Create: `src/tech_daily/cross_day_pipeline.py`
- Modify: `src/tech_daily/pipeline.py`
- Modify: `src/tech_daily/render.py`
- Modify: `templates/daily.html`
- Test: `tests/test_cross_day_pipeline.py`
- Modify: `tests/test_pipeline.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing pipeline test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.cross_day_pipeline import run_cross_day_pipeline


class CrossDayPipelineTests(unittest.TestCase):
    def test_run_cross_day_pipeline_writes_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"
            snapshot_dir = root / "data" / "health_snapshots"
            snapshot_dir.mkdir(parents=True)

            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps({"date": date_text, "hottest_topics": ["安全与治理"], "active_companies": ["OpenAI"]}),
                    encoding="utf-8",
                )
                (snapshot_dir / f"{date_text}.json").write_text(
                    json.dumps({"report_date": date_text, "high_priority_runtime_issues": []}),
                    encoding="utf-8",
                )

            result = run_cross_day_pipeline(site_dir, snapshot_dir, report_date="2026-05-15", days=3)

        self.assertEqual(result["json_path"].name, "cross_day_intel_brief.json")
        self.assertIn("page_block", result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_cross_day_pipeline.py" -v`  
Expected: FAIL with missing `tech_daily.cross_day_pipeline`

- [ ] **Step 3: Write minimal pipeline implementation**

```python
from pathlib import Path

from tech_daily.cross_day_analysis import analyze_cross_day_intel
from tech_daily.cross_day_input import load_cross_day_inputs
from tech_daily.cross_day_outputs import write_cross_day_outputs


def run_cross_day_pipeline(site_dir: Path, snapshot_history_dir: Path, report_date: str, days: int = 3) -> dict:
    inputs = load_cross_day_inputs(site_dir, snapshot_history_dir, end_date=report_date, days=days)
    brief = analyze_cross_day_intel(
        date_range=inputs.date_range,
        reports=inputs.reports,
        intel_briefs=inputs.intel_briefs,
        snapshots=inputs.snapshots,
    )
    output_dir = site_dir / report_date
    return write_cross_day_outputs(brief, output_dir)
```

- [ ] **Step 4: Integrate into the main pipeline with graceful fallback**

```python
try:
    cross_day_result = run_cross_day_pipeline(
        destination,
        Path(DEFAULT_SETTINGS.data_output_dir) / "health_snapshots",
        report.date,
        days=3,
    )
    report = replace(report, cross_day_brief=cross_day_result["page_block"])
except Exception:
    pass
```

- [ ] **Step 5: Add render support**

```python
def _render_cross_day_brief(brief: dict) -> str:
    if not brief:
        return ""
    return (
        "<section class='cross-day-brief'>"
        "<div class='section-topline'>跨日观察</div>"
        f"<h2>{escape(' / '.join(brief.get('warming_themes', [])[:2]) or '最近几天主线')}</h2>"
        "</section>"
    )
```

```html
$cross_day_brief_section
```

- [ ] **Step 6: Add render regression tests**

```python
def test_render_daily_includes_cross_day_brief_section(self) -> None:
    report = build_report_fixture(cross_day_brief={"warming_themes": ["安全与治理"], "steady_companies": ["OpenAI"]})
    html = render_daily(report)
    self.assertIn("跨日观察", html)
    self.assertIn("安全与治理", html)
```

- [ ] **Step 7: Run focused tests**

Run: `python -m unittest discover -s tests -p "test_cross_day_pipeline.py" -v`  
Expected: PASS

Run: `python -m unittest discover -s tests -p "test_render.py" -v`  
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/tech_daily/cross_day_pipeline.py src/tech_daily/pipeline.py src/tech_daily/render.py templates/daily.html tests/test_cross_day_pipeline.py tests/test_pipeline.py tests/test_render.py
git commit -m "feat: integrate cross-day intel agent"
```

## Task 6: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-05-13-improvement-roadmap.md`

- [ ] **Step 1: Update README outputs and architecture**

```markdown
- `build/data/health_snapshots/<date>.json`
- `build/site/<date>/cross_day_intel_brief.json`
- `build/site/<date>/cross-day-brief.md`
```

```markdown
- `cross_day_pipeline.py`: builds recent-day tracking outputs and page data from report history and dated health snapshots
```

- [ ] **Step 2: Update roadmap**

```markdown
- Cross-day tracking agent baseline:
  - `cross_day_intel_brief.json`
  - `cross-day-brief.md`
  - daily page `跨日观察` block
```

- [ ] **Step 3: Run the full test suite**

Run: `python -m unittest discover -s tests -v`  
Expected: PASS with all existing and new tests passing

- [ ] **Step 4: Generate a real report and verify artifacts**

Run: `python run_dashboard.py generate-today --output-dir build/site`  
Expected:
- Daily report still generates successfully
- `build/data/health_snapshots/<today>.json` exists
- `build/site/<today>/cross_day_intel_brief.json` exists
- `build/site/<today>/cross-day-brief.md` exists

- [ ] **Step 5: Inspect rendered page output**

Run: `Get-Content build/site/<today>/index.html | Select-String -Pattern "跨日观察|情报判断"`  
Expected: `跨日观察` appears alongside the existing `情报判断` content when enough data is present

- [ ] **Step 6: Commit**

```bash
git add README.md docs/2026-05-13-improvement-roadmap.md
git commit -m "docs: document cross-day intel agent"
```

## Self-Review

- Spec coverage: this plan covers historical health snapshot persistence, cross-day inputs, analysis, outputs, pipeline integration, degradation behavior, page rendering, and docs updates from the approved spec.
- Placeholder scan: no `TODO`, `TBD`, or vague “handle appropriately” language remains in the task steps.
- Type consistency: the plan uses the same names throughout: `CrossDayIntelBrief`, `cross_day_intel_brief.json`, `cross-day-brief.md`, `cross_day_brief`, and `build/data/health_snapshots/<date>.json`.
