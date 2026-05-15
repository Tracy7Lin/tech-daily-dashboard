# Theme Tracking Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a third-stage theme-tracking agent that reads recent reports plus existing v1/v2 agent outputs, selects a primary theme from a small candidate pool, produces a unified `theme_tracking_brief`, writes a Markdown report, and renders a `专题跟踪` section into the daily dashboard.

**Architecture:** Extend the existing enhancement chain after the cross-day agent. Add four focused modules: `theme_tracking_input`, `theme_tracking_analysis`, `theme_tracking_outputs`, and `theme_tracking_pipeline`. Use rules to choose candidate themes and factual boundaries, then use existing LLM-facing capability style only where analysis expression adds value. The main report pipeline remains primary; the theme-tracking agent runs afterward as a degradable enhancement and must never break daily report generation.

**Tech Stack:** Python 3.11, `unittest`, existing pipeline/agent architecture, JSON report artifacts, Markdown output, existing static renderer, existing hybrid LLM expression layer

---

## File Structure

### New files

- `src/tech_daily/theme_tracking_input.py`
  - Load recent `report.json`, optional `daily_intel_brief.json`, and optional `cross_day_intel_brief.json` into a normalized input payload.
- `src/tech_daily/theme_tracking_analysis.py`
  - Build the structured `theme_tracking_brief` result from recent reports and existing agent outputs.
- `src/tech_daily/theme_tracking_outputs.py`
  - Persist `theme_tracking_brief.json`, render `theme-tracking-brief.md`, and shape page block data.
- `src/tech_daily/theme_tracking_pipeline.py`
  - Orchestrate theme-tracking input loading, analysis, output writing, and graceful fallback.
- `tests/test_theme_tracking_input.py`
  - Verify recent-day loading and fallback when optional v1/v2 artifacts are missing.
- `tests/test_theme_tracking_analysis.py`
  - Verify candidate themes, primary theme selection, participating companies, and follow-up recommendations.
- `tests/test_theme_tracking_outputs.py`
  - Verify JSON and Markdown output rendering.
- `tests/test_theme_tracking_pipeline.py`
  - Verify orchestration and graceful fallback behavior.

### Modified files

- `src/tech_daily/models.py`
  - Add lightweight dataclasses for `ThemeTrackingBrief` and optional page block data.
- `src/tech_daily/pipeline.py`
  - Invoke `theme_tracking_pipeline` after the cross-day agent and attach result to `DailyReport`.
- `src/tech_daily/render.py`
  - Render the `专题跟踪` block when theme-tracking output is present.
- `templates/daily.html`
  - Add a section placeholder for `专题跟踪`.
- `tests/test_pipeline.py`
  - Verify the dashboard pipeline tolerates theme-tracking augmentation and failure.
- `tests/test_render.py`
  - Verify the daily page includes the new `专题跟踪` section and degrades safely.
- `README.md`
  - Document theme-tracking outputs and architecture.
- `docs/2026-05-13-improvement-roadmap.md`
  - Note that the theme-tracking agent line has started.

## Task 1: Add theme-tracking input loading

**Files:**
- Create: `src/tech_daily/theme_tracking_input.py`
- Test: `tests/test_theme_tracking_input.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.theme_tracking_input import load_theme_tracking_inputs


class ThemeTrackingInputTests(unittest.TestCase):
    def test_load_theme_tracking_inputs_reads_reports_and_optional_agent_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"

            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps(
                        {
                            "date": date_text,
                            "hottest_topics": ["安全与治理"],
                            "active_companies": ["OpenAI"],
                        }
                    ),
                    encoding="utf-8",
                )
                (report_dir / "daily_intel_brief.json").write_text(
                    json.dumps({"report_date": date_text, "top_content_themes": ["安全与治理"]}),
                    encoding="utf-8",
                )
                (report_dir / "cross_day_intel_brief.json").write_text(
                    json.dumps({"date_range": ["2026-05-13", date_text], "warming_themes": ["安全与治理"]}),
                    encoding="utf-8",
                )

            payload = load_theme_tracking_inputs(site_dir, end_date="2026-05-15", days=3)

        self.assertEqual(payload.date_range, ("2026-05-13", "2026-05-15"))
        self.assertEqual(len(payload.reports), 3)
        self.assertEqual(payload.daily_briefs[-1]["report_date"], "2026-05-15")
        self.assertEqual(payload.cross_day_briefs[-1]["warming_themes"], ["安全与治理"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_input.py" -v`  
Expected: FAIL with missing `tech_daily.theme_tracking_input`

- [ ] **Step 3: Write minimal implementation**

```python
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(slots=True)
class ThemeTrackingInputs:
    date_range: tuple[str, str]
    reports: list[dict]
    daily_briefs: list[dict]
    cross_day_briefs: list[dict]


def load_theme_tracking_inputs(site_dir: Path, end_date: str, days: int) -> ThemeTrackingInputs:
    end_day = date.fromisoformat(end_date)
    dates = [(end_day - timedelta(days=offset)).isoformat() for offset in reversed(range(days))]
    reports: list[dict] = []
    daily_briefs: list[dict] = []
    cross_day_briefs: list[dict] = []

    for date_text in dates:
        report_dir = site_dir / date_text
        report_path = report_dir / "report.json"
        if report_path.exists():
            reports.append(json.loads(report_path.read_text(encoding="utf-8")))
        daily_path = report_dir / "daily_intel_brief.json"
        if daily_path.exists():
            daily_briefs.append(json.loads(daily_path.read_text(encoding="utf-8")))
        cross_day_path = report_dir / "cross_day_intel_brief.json"
        if cross_day_path.exists():
            cross_day_briefs.append(json.loads(cross_day_path.read_text(encoding="utf-8")))

    return ThemeTrackingInputs(
        date_range=(dates[0], dates[-1]),
        reports=reports,
        daily_briefs=daily_briefs,
        cross_day_briefs=cross_day_briefs,
    )
```

- [ ] **Step 4: Add fallback coverage for missing optional v1/v2 artifacts**

```python
def test_load_theme_tracking_inputs_tolerates_missing_daily_and_cross_day_briefs(self) -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        site_dir = root / "site"
        report_dir = site_dir / "2026-05-15"
        report_dir.mkdir(parents=True)
        (report_dir / "report.json").write_text(
            json.dumps({"date": "2026-05-15", "hottest_topics": ["安全与治理"]}),
            encoding="utf-8",
        )

        payload = load_theme_tracking_inputs(site_dir, end_date="2026-05-15", days=1)

    self.assertEqual(len(payload.reports), 1)
    self.assertEqual(payload.daily_briefs, [])
    self.assertEqual(payload.cross_day_briefs, [])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_input.py" -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/tech_daily/theme_tracking_input.py tests/test_theme_tracking_input.py
git commit -m "feat: add theme tracking input loader"
```

## Task 2: Add structured theme-tracking analysis

**Files:**
- Create: `src/tech_daily/theme_tracking_analysis.py`
- Modify: `src/tech_daily/models.py`
- Test: `tests/test_theme_tracking_analysis.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from tech_daily.theme_tracking_analysis import analyze_theme_tracking


class ThemeTrackingAnalysisTests(unittest.TestCase):
    def test_analyze_theme_tracking_selects_primary_theme_and_participating_companies(self) -> None:
        reports = [
            {
                "date": "2026-05-13",
                "hottest_topics": ["安全与治理", "模型与能力发布"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "OpenAI"},
                                "comparison_angle": "安全机制前置",
                            }
                        ],
                    }
                ],
            },
            {
                "date": "2026-05-14",
                "hottest_topics": ["安全与治理"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "OpenAI"},
                                "comparison_angle": "平台与安全控制",
                            },
                            {
                                "raw": {"company_name": "Google"},
                                "comparison_angle": "产品功能约束",
                            },
                        ],
                    }
                ],
            },
            {
                "date": "2026-05-15",
                "hottest_topics": ["安全与治理"],
                "topic_clusters": [
                    {
                        "title": "安全与治理",
                        "entries": [
                            {
                                "raw": {"company_name": "Google"},
                                "comparison_angle": "产品功能落地",
                            }
                        ],
                    }
                ],
            },
        ]
        daily_briefs = [
            {"top_content_themes": ["安全与治理"]},
            {"top_content_themes": ["安全与治理"]},
            {"top_content_themes": ["安全与治理"]},
        ]
        cross_day_briefs = [
            {"warming_themes": ["安全与治理"], "steady_companies": ["OpenAI", "Google"]},
        ]

        brief = analyze_theme_tracking(
            date_range=("2026-05-13", "2026-05-15"),
            reports=reports,
            daily_briefs=daily_briefs,
            cross_day_briefs=cross_day_briefs,
        )

        self.assertIn("安全与治理", brief.candidate_themes)
        self.assertEqual(brief.primary_theme, "安全与治理")
        self.assertIn("OpenAI", brief.participating_companies)
        self.assertIn("Google", brief.participating_companies)
        self.assertTrue(brief.continue_tracking)
        self.assertTrue(brief.next_day_theme_focus)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_analysis.py" -v`  
Expected: FAIL with missing `tech_daily.theme_tracking_analysis`

- [ ] **Step 3: Write minimal implementation**

```python
from collections import Counter
from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class ThemeTrackingBrief:
    date_range: tuple[str, str]
    candidate_themes: list[str] = field(default_factory=list)
    primary_theme: str = ""
    theme_summary: str = ""
    participating_companies: list[str] = field(default_factory=list)
    company_angles: dict[str, str] = field(default_factory=dict)
    theme_evolution: str = ""
    continue_tracking: bool = False
    next_day_theme_focus: list[str] = field(default_factory=list)
    mode_used: str = "hybrid"

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_theme_tracking(date_range, reports, daily_briefs, cross_day_briefs) -> ThemeTrackingBrief:
    theme_counts = Counter()
    company_angles: dict[str, str] = {}
    companies_by_theme: dict[str, list[str]] = {}

    for report in reports:
        for theme in report.get("hottest_topics", []):
            theme_counts[theme] += 1
        for cluster in report.get("topic_clusters", []):
            title = cluster.get("title", "")
            if not title:
                continue
            companies_by_theme.setdefault(title, [])
            for entry in cluster.get("entries", []):
                company = entry.get("raw", {}).get("company_name", "")
                angle = entry.get("comparison_angle", "")
                if company and company not in companies_by_theme[title]:
                    companies_by_theme[title].append(company)
                if company and angle and company not in company_angles:
                    company_angles[company] = angle

    for brief in daily_briefs:
        for theme in brief.get("top_content_themes", []):
            theme_counts[theme] += 1
    for brief in cross_day_briefs:
        for theme in brief.get("warming_themes", []):
            theme_counts[theme] += 2

    candidate_themes = [theme for theme, _ in theme_counts.most_common(3)]
    primary_theme = candidate_themes[0] if candidate_themes else ""
    participating_companies = companies_by_theme.get(primary_theme, [])
    next_day_theme_focus = [primary_theme] if primary_theme else []

    return ThemeTrackingBrief(
        date_range=date_range,
        candidate_themes=candidate_themes,
        primary_theme=primary_theme,
        theme_summary=f"{primary_theme} 是最近几天最值得继续跟踪的专题。" if primary_theme else "",
        participating_companies=participating_companies,
        company_angles={company: company_angles.get(company, "") for company in participating_companies},
        theme_evolution="该专题最近几天持续出现，值得继续观察。" if primary_theme else "",
        continue_tracking=bool(primary_theme and len(participating_companies) >= 1),
        next_day_theme_focus=next_day_theme_focus,
        mode_used="hybrid",
    )
```

- [ ] **Step 4: Add candidate-pool coverage**

```python
def test_analyze_theme_tracking_limits_candidate_pool_to_top_three_themes(self) -> None:
    reports = [
        {"date": "2026-05-15", "hottest_topics": ["A", "B", "C", "D"], "topic_clusters": []},
    ]

    brief = analyze_theme_tracking(
        date_range=("2026-05-15", "2026-05-15"),
        reports=reports,
        daily_briefs=[],
        cross_day_briefs=[],
    )

    self.assertEqual(len(brief.candidate_themes), 3)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_analysis.py" -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/tech_daily/theme_tracking_analysis.py src/tech_daily/models.py tests/test_theme_tracking_analysis.py
git commit -m "feat: add theme tracking analysis"
```

## Task 3: Add theme-tracking outputs

**Files:**
- Create: `src/tech_daily/theme_tracking_outputs.py`
- Test: `tests/test_theme_tracking_outputs.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.models import ThemeTrackingBrief
from tech_daily.theme_tracking_outputs import write_theme_tracking_outputs


class ThemeTrackingOutputsTests(unittest.TestCase):
    def test_write_theme_tracking_outputs_persists_json_and_markdown(self) -> None:
        brief = ThemeTrackingBrief(
            date_range=("2026-05-13", "2026-05-15"),
            candidate_themes=["安全与治理", "模型与能力发布"],
            primary_theme="安全与治理",
            theme_summary="安全与治理仍是最近几天最值得继续跟踪的专题。",
            participating_companies=["OpenAI", "Google"],
            company_angles={"OpenAI": "平台与安全机制前置", "Google": "产品功能落地"},
            theme_evolution="专题正在从单点更新演化为多家公司持续参与。",
            continue_tracking=True,
            next_day_theme_focus=["安全与治理", "Google"],
            mode_used="hybrid",
        )

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = write_theme_tracking_outputs(brief, output_dir)
            brief_json = json.loads((output_dir / "theme_tracking_brief.json").read_text(encoding="utf-8"))
            brief_md = (output_dir / "theme-tracking-brief.md").read_text(encoding="utf-8")

        self.assertEqual(result["json_path"].name, "theme_tracking_brief.json")
        self.assertEqual(brief_json["primary_theme"], "安全与治理")
        self.assertIn("主专题", brief_md)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_outputs.py" -v`  
Expected: FAIL with missing `tech_daily.theme_tracking_outputs`

- [ ] **Step 3: Write minimal implementation**

```python
import json
from pathlib import Path


def render_theme_tracking_markdown(brief) -> str:
    companies = "\n".join(f"- {company}" for company in brief.participating_companies) or "- 暂无"
    focus = "\n".join(f"- {item}" for item in brief.next_day_theme_focus) or "- 暂无"
    return (
        f"# {brief.date_range[0]} 至 {brief.date_range[1]} 专题跟踪\n\n"
        f"## 主专题\n{brief.primary_theme}\n\n"
        f"## 为什么今天值得继续看\n{brief.theme_summary}\n\n"
        f"## 参与公司\n{companies}\n\n"
        f"## 明日关注点\n{focus}\n"
    )


def build_theme_tracking_page_block(brief) -> dict:
    return {
        "candidate_themes": brief.candidate_themes,
        "primary_theme": brief.primary_theme,
        "theme_summary": brief.theme_summary,
        "participating_companies": brief.participating_companies,
        "company_angles": brief.company_angles,
        "theme_evolution": brief.theme_evolution,
        "continue_tracking": brief.continue_tracking,
        "next_day_theme_focus": brief.next_day_theme_focus,
    }


def write_theme_tracking_outputs(brief, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "theme_tracking_brief.json"
    markdown_path = output_dir / "theme-tracking-brief.md"
    json_path.write_text(json.dumps(brief.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_theme_tracking_markdown(brief), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": markdown_path, "page_block": build_theme_tracking_page_block(brief)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_outputs.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/theme_tracking_outputs.py tests/test_theme_tracking_outputs.py
git commit -m "feat: add theme tracking outputs"
```

## Task 4: Add theme-tracking pipeline and page integration

**Files:**
- Create: `src/tech_daily/theme_tracking_pipeline.py`
- Modify: `src/tech_daily/pipeline.py`
- Modify: `src/tech_daily/render.py`
- Modify: `templates/daily.html`
- Test: `tests/test_theme_tracking_pipeline.py`
- Modify: `tests/test_pipeline.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write the failing pipeline test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tech_daily.theme_tracking_pipeline import run_theme_tracking_pipeline


class ThemeTrackingPipelineTests(unittest.TestCase):
    def test_run_theme_tracking_pipeline_writes_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_dir = root / "site"

            for date_text in ("2026-05-13", "2026-05-14", "2026-05-15"):
                report_dir = site_dir / date_text
                report_dir.mkdir(parents=True)
                (report_dir / "report.json").write_text(
                    json.dumps(
                        {
                            "date": date_text,
                            "hottest_topics": ["安全与治理"],
                            "topic_clusters": [],
                        }
                    ),
                    encoding="utf-8",
                )
                (report_dir / "daily_intel_brief.json").write_text(
                    json.dumps({"report_date": date_text, "top_content_themes": ["安全与治理"]}),
                    encoding="utf-8",
                )
                (report_dir / "cross_day_intel_brief.json").write_text(
                    json.dumps({"date_range": ["2026-05-13", date_text], "warming_themes": ["安全与治理"]}),
                    encoding="utf-8",
                )

            result = run_theme_tracking_pipeline(site_dir, report_date="2026-05-15", days=3)

        self.assertEqual(result["json_path"].name, "theme_tracking_brief.json")
        self.assertIn("page_block", result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_pipeline.py" -v`  
Expected: FAIL with missing `tech_daily.theme_tracking_pipeline`

- [ ] **Step 3: Write minimal pipeline implementation**

```python
from pathlib import Path

from tech_daily.theme_tracking_analysis import analyze_theme_tracking
from tech_daily.theme_tracking_input import load_theme_tracking_inputs
from tech_daily.theme_tracking_outputs import write_theme_tracking_outputs


def run_theme_tracking_pipeline(site_dir: Path, report_date: str, days: int = 3) -> dict:
    inputs = load_theme_tracking_inputs(site_dir, end_date=report_date, days=days)
    brief = analyze_theme_tracking(
        date_range=inputs.date_range,
        reports=inputs.reports,
        daily_briefs=inputs.daily_briefs,
        cross_day_briefs=inputs.cross_day_briefs,
    )
    outputs = write_theme_tracking_outputs(brief, site_dir / report_date)
    return {
        "brief": brief,
        "outputs": outputs,
        "json_path": outputs["json_path"],
        "markdown_path": outputs["markdown_path"],
        "page_block": outputs["page_block"],
    }
```

- [ ] **Step 4: Integrate into the main pipeline with graceful fallback**

```python
try:
    theme_tracking_result = run_theme_tracking_pipeline(destination, report.date, days=3)
    report = replace(report, theme_tracking_brief=theme_tracking_result["page_block"])
    write_site(report, destination)
except Exception:
    pass
```

- [ ] **Step 5: Add render support**

```python
def _render_theme_tracking_brief(brief: dict) -> str:
    if not brief:
        return ""
    companies = "、".join(brief.get("participating_companies", [])) or "暂无"
    next_focus = "、".join(brief.get("next_day_theme_focus", [])) or "暂无"
    continue_tracking = "建议继续跟踪" if brief.get("continue_tracking") else "可暂缓继续跟踪"
    return (
        "<section class='section'>"
        "<h2>专题跟踪</h2>"
        f"<p class='section-copy'><strong>主专题：</strong>{brief.get('primary_theme', '')}</p>"
        f"<p class='section-copy'><strong>主题摘要：</strong>{brief.get('theme_summary', '')}</p>"
        f"<p class='section-copy'><strong>参与公司：</strong>{companies}</p>"
        f"<p class='section-copy'><strong>是否继续跟踪：</strong>{continue_tracking}</p>"
        f"<p class='section-copy'><strong>明日关注：</strong>{next_focus}</p>"
        "<p><a class='inline-link' href='./theme-tracking-brief.md'>查看完整专题 Markdown 报告</a></p>"
        "</section>"
    )
```

```html
$theme_tracking_brief_section
```

- [ ] **Step 6: Add render regression tests**

```python
def test_render_daily_includes_theme_tracking_brief_block_when_present(self) -> None:
    report = DailyReport(
        date="2026-05-15",
        headline="headline",
        hottest_topics=[],
        total_entries=0,
        companies_covered=0,
        topic_clusters=[],
        company_reports=[],
        source_statuses=[],
        theme_tracking_brief={
            "primary_theme": "安全与治理",
            "theme_summary": "安全与治理仍是最近几天最值得继续跟踪的专题。",
            "participating_companies": ["OpenAI", "Google"],
            "continue_tracking": True,
            "next_day_theme_focus": ["安全与治理"],
        },
    )
    html = render_daily(report)
    self.assertIn("专题跟踪", html)
    self.assertIn("主专题", html)
    self.assertIn("查看完整专题 Markdown 报告", html)
```

- [ ] **Step 7: Add pipeline fallback coverage**

```python
@patch("tech_daily.pipeline.run_theme_tracking_pipeline")
@patch("tech_daily.pipeline.run_cross_day_pipeline")
@patch("tech_daily.pipeline.run_agent_pipeline")
...
def test_generate_daily_report_keeps_working_when_theme_tracking_pipeline_fails(...):
    mock_run_theme_tracking_pipeline.side_effect = RuntimeError("theme boom")
    report = generate_daily_report("2026-05-15", output_dir=Path(temp_dir))
    self.assertEqual(report.theme_tracking_brief, {})
```

- [ ] **Step 8: Run focused tests**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_pipeline.py" -v`  
Expected: PASS

Run: `python -m unittest discover -s tests -p "test_render.py" -v`  
Expected: PASS

Run: `python -m unittest discover -s tests -p "test_pipeline.py" -v`  
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add src/tech_daily/theme_tracking_pipeline.py src/tech_daily/pipeline.py src/tech_daily/render.py templates/daily.html tests/test_theme_tracking_pipeline.py tests/test_pipeline.py tests/test_render.py
git commit -m "feat: integrate theme tracking agent"
```

## Task 5: Refine theme-tracking analysis expression with hybrid boundaries

**Files:**
- Modify: `src/tech_daily/theme_tracking_analysis.py`
- Test: `tests/test_theme_tracking_analysis.py`

- [ ] **Step 1: Write the failing test for bounded expression fields**

```python
def test_analyze_theme_tracking_populates_expression_fields_without_rebuilding_facts(self) -> None:
    reports = [
        {
            "date": "2026-05-15",
            "hottest_topics": ["安全与治理"],
            "topic_clusters": [
                {
                    "title": "安全与治理",
                    "entries": [
                        {
                            "raw": {"company_name": "OpenAI"},
                            "comparison_angle": "平台与安全机制前置",
                        }
                    ],
                }
            ],
        }
    ]

    brief = analyze_theme_tracking(
        date_range=("2026-05-15", "2026-05-15"),
        reports=reports,
        daily_briefs=[],
        cross_day_briefs=[],
    )

    self.assertTrue(brief.theme_summary)
    self.assertTrue(brief.theme_evolution)
    self.assertEqual(brief.participating_companies, ["OpenAI"])
```

- [ ] **Step 2: Run test to verify it fails for the right reason**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_analysis.py" -v`  
Expected: FAIL because summary/evolution are too weak or missing for the new assertion

- [ ] **Step 3: Refine the analysis while keeping factual selection rule-driven**

```python
theme_summary = (
    f"{primary_theme} 是最近几天最值得继续跟踪的专题，"
    f"当前重点集中在 {'、'.join(participating_companies[:3]) or '相关公司'} 的持续参与。"
    if primary_theme
    else ""
)
theme_evolution = (
    "这个专题最近几天持续出现，且参与公司开始形成差异化切入。"
    if len(participating_companies) >= 2
    else "这个专题最近几天持续出现，但目前仍以单一公司动作为主。"
    if primary_theme
    else ""
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_theme_tracking_analysis.py" -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/theme_tracking_analysis.py tests/test_theme_tracking_analysis.py
git commit -m "feat: refine theme tracking analysis expression"
```

## Task 6: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-05-13-improvement-roadmap.md`

- [ ] **Step 1: Update README outputs and architecture**

```markdown
- `build/site/<date>/theme_tracking_brief.json`
- `build/site/<date>/theme-tracking-brief.md`
```

```markdown
- `theme_tracking_pipeline.py`: builds the primary tracked theme brief from recent reports plus v1/v2 agent artifacts
```

- [ ] **Step 2: Update roadmap**

```markdown
- Theme-tracking agent baseline:
  - `theme_tracking_brief.json`
  - `theme-tracking-brief.md`
  - daily page `专题跟踪` block
```

- [ ] **Step 3: Run the full test suite**

Run: `python -m unittest discover -s tests -v`  
Expected: PASS with all existing and new tests passing

- [ ] **Step 4: Generate a real report and verify artifacts**

Run: `python run_dashboard.py generate-today --output-dir build/site`  
Expected:
- Daily report still generates successfully
- `build/site/<today>/theme_tracking_brief.json` exists
- `build/site/<today>/theme-tracking-brief.md` exists

- [ ] **Step 5: Inspect rendered page output**

Run: `Get-Content build/site/<today>/index.html | Select-String -Pattern "专题跟踪|跨日观察|情报判断"`  
Expected: `专题跟踪` appears alongside the existing v1/v2 sections when enough data is present

- [ ] **Step 6: Commit**

```bash
git add README.md docs/2026-05-13-improvement-roadmap.md
git commit -m "docs: document theme tracking agent"
```

## Self-Review

- Spec coverage: this plan covers theme-tracking inputs, rule-driven candidate and primary theme selection, bounded expression fields, outputs, pipeline integration, degradation behavior, page rendering, and docs updates from the approved spec.
- Placeholder scan: no `TODO`, `TBD`, or vague “handle appropriately” language remains in the task steps.
- Type consistency: the plan uses the same names throughout: `ThemeTrackingBrief`, `theme_tracking_brief.json`, `theme-tracking-brief.md`, `theme_tracking_brief`, and `theme_tracking_pipeline`.
