# Agent-Ready Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce an agent-ready capability layer for brief generation, topic comparison, daily editorial, and ops status analysis without breaking the current dashboard behavior.

**Architecture:** Add four focused capability modules under `src/tech_daily/capabilities`, each with structured input/output and explicit `mode_used`. Keep the current product stable by making existing facades delegate into the new capability layer, and let `ops_status_analysis` consume `health_snapshot.json` without taking over snapshot generation.

**Tech Stack:** Python 3.11, `unittest`, existing rule/LLM runtime modules, JSON health snapshot artifacts

---

## File Structure

### New files

- `src/tech_daily/capabilities/__init__.py`
  - Re-export the four capability modules for internal discovery.
- `src/tech_daily/capabilities/brief_generation.py`
  - Structured single-entry capability wrapping rule/LLM summarization.
- `src/tech_daily/capabilities/topic_comparison.py`
  - Structured topic-level summary/comparison/trend capability.
- `src/tech_daily/capabilities/daily_editorial.py`
  - Structured daily headline/brief capability.
- `src/tech_daily/capabilities/ops_status_analysis.py`
  - Structured health snapshot interpretation capability.
- `tests/test_brief_generation_capability.py`
  - Capability contract tests for single-entry summaries.
- `tests/test_topic_comparison_capability.py`
  - Capability contract tests for topic summary/comparison/trend output.
- `tests/test_daily_editorial_capability.py`
  - Capability contract tests for top-level editorial output.
- `tests/test_ops_status_analysis_capability.py`
  - Capability contract tests for current issues, high priority, recovered issues, and operator brief.

### Modified files

- `src/tech_daily/summarizer.py`
  - Delegate to `brief_generation` while keeping existing public API.
- `src/tech_daily/editorial.py`
  - Delegate to `topic_comparison` and `daily_editorial` while keeping existing public API.
- `src/tech_daily/healthcheck.py`
  - Reuse `ops_status_analysis` to enrich the returned payload and written snapshot without breaking existing fields.
- `src/tech_daily/cli.py`
  - Print any newly added structured ops summary fields if surfaced through `health-check`.
- `tests/test_summarizer.py`
  - Verify the summarizer facade still works while delegating to the new capability.
- `tests/test_editorial.py`
  - Verify the editorial facade still works while delegating to the new capability.
- `tests/test_healthcheck.py`
  - Verify `healthcheck` embeds agent-ready ops analysis in a backward-compatible way.
- `tests/test_cli.py`
  - Verify CLI summary output still includes the old lines and can include new ops brief details safely.
- `README.md`
  - Document the new capability layer in the architecture section.
- `docs/2026-05-13-improvement-roadmap.md`
  - Mark the capability-layer groundwork as the next completed foundation step.

## Task 1: Add `brief_generation` capability

**Files:**
- Create: `src/tech_daily/capabilities/__init__.py`
- Create: `src/tech_daily/capabilities/brief_generation.py`
- Test: `tests/test_brief_generation_capability.py`
- Modify: `tests/test_summarizer.py`

- [ ] **Step 1: Write the failing capability tests**

```python
from tech_daily.capabilities.brief_generation import (
    BriefGenerationCapability,
    BriefGenerationInput,
)
from tech_daily.models import RawEntry


def build_entry() -> RawEntry:
    return RawEntry(
        company_slug="openai",
        company_name="OpenAI",
        source_label="OpenAI News",
        title="OpenAI adds new admin controls",
        summary="OpenAI introduced new admin controls for enterprise teams.",
        url="https://openai.com/news/example",
        published_at="2026-05-14T08:00:00+08:00",
    )


def test_brief_generation_returns_structured_result():
    capability = BriefGenerationCapability(mode="rule")
    result = capability.generate(
        BriefGenerationInput(
            company="OpenAI",
            title=build_entry().title,
            summary=build_entry().summary,
            tags=["developer", "enterprise"],
            category="product",
            url=build_entry().url,
            published_at=build_entry().published_at,
            raw_entry=build_entry(),
        )
    )

    assert result.summary_cn
    assert result.angle
    assert result.confidence == "high"
    assert result.mode_used == "rule"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_brief_generation_capability -v`  
Expected: FAIL with `ModuleNotFoundError` or missing `BriefGenerationCapability`

- [ ] **Step 3: Write the minimal capability implementation**

```python
from dataclasses import dataclass

from ..llm_runtime import build_llm_client, normalize_generation_mode
from ..llm_summarizer import LLMSummarizer
from ..models import RawEntry
from ..rule_summarizer import RuleSummarizer
from ..settings import DEFAULT_SETTINGS, Settings


@dataclass(slots=True)
class BriefGenerationInput:
    company: str
    title: str
    summary: str
    tags: list[str]
    category: str
    url: str
    published_at: str
    raw_entry: RawEntry


@dataclass(slots=True)
class BriefGenerationOutput:
    summary_cn: str
    angle: str
    confidence: str
    mode_used: str


class BriefGenerationCapability:
    def __init__(self, mode: str | None = None, settings: Settings | None = None, fallback_enabled: bool | None = None):
        runtime = settings or DEFAULT_SETTINGS
        self.mode = normalize_generation_mode(mode or runtime.summary_mode)
        self.rule_summarizer = RuleSummarizer()
        self.llm_summarizer = LLMSummarizer(build_llm_client(runtime))
        self.fallback_enabled = runtime.llm_fallback_enabled if fallback_enabled is None else fallback_enabled

    def generate(self, payload: BriefGenerationInput) -> BriefGenerationOutput:
        summary_cn, mode_used = self._generate_summary(payload)
        angle = payload.tags[0] if payload.tags else payload.category
        return BriefGenerationOutput(summary_cn=summary_cn, angle=angle or "general", confidence="high", mode_used=mode_used)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_brief_generation_capability tests.test_summarizer -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/capabilities/__init__.py src/tech_daily/capabilities/brief_generation.py tests/test_brief_generation_capability.py tests/test_summarizer.py
git commit -m "feat: add brief generation capability"
```

## Task 2: Add `topic_comparison` and `daily_editorial` capabilities

**Files:**
- Create: `src/tech_daily/capabilities/topic_comparison.py`
- Create: `src/tech_daily/capabilities/daily_editorial.py`
- Test: `tests/test_topic_comparison_capability.py`
- Test: `tests/test_daily_editorial_capability.py`
- Modify: `src/tech_daily/editorial.py`
- Modify: `tests/test_editorial.py`

- [ ] **Step 1: Write the failing capability tests**

```python
from tech_daily.capabilities.topic_comparison import TopicComparisonCapability
from tech_daily.capabilities.daily_editorial import DailyEditorialCapability


def test_topic_comparison_returns_structured_summary_comparison_and_trend():
    capability = TopicComparisonCapability(mode="rule")
    result = capability.generate(
        topic_title="安全与治理",
        entries=[entry_one, entry_two],
        involved_companies=["OpenAI", "Google"],
    )
    assert result.summary
    assert result.comparison
    assert result.trend
    assert result.mode_used == "rule"


def test_daily_editorial_returns_headline_and_brief():
    capability = DailyEditorialCapability(mode="rule")
    result = capability.generate(
        report_date="2026-05-14",
        topic_clusters=[topic_cluster],
        company_reports=[company_report],
        total_entries=3,
    )
    assert result.headline
    assert result.brief
    assert result.mode_used == "rule"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_topic_comparison_capability tests.test_daily_editorial_capability -v`  
Expected: FAIL with missing capability modules

- [ ] **Step 3: Write the minimal capability implementations and facade delegation**

```python
@dataclass(slots=True)
class TopicComparisonOutput:
    summary: str
    comparison: str
    trend: str
    mode_used: str


class TopicComparisonCapability:
    def generate(self, topic_title: str, entries, involved_companies: list[str]) -> TopicComparisonOutput:
        return TopicComparisonOutput(
            summary=self.rule_editor.build_topic_summary(topic_title, entries),
            comparison=self.rule_editor.build_topic_comparison(entries),
            trend=self.rule_editor.build_topic_trend(topic_title, entries),
            mode_used="rule",
        )


@dataclass(slots=True)
class DailyEditorialOutput:
    headline: str
    brief: str
    mode_used: str
```

And in `editorial.py`:

```python
from .capabilities.daily_editorial import DailyEditorialCapability
from .capabilities.topic_comparison import TopicComparisonCapability

self.daily_editorial = DailyEditorialCapability(...)
self.topic_comparison = TopicComparisonCapability(...)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_topic_comparison_capability tests.test_daily_editorial_capability tests.test_editorial -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/capabilities/topic_comparison.py src/tech_daily/capabilities/daily_editorial.py src/tech_daily/editorial.py tests/test_topic_comparison_capability.py tests/test_daily_editorial_capability.py tests/test_editorial.py
git commit -m "feat: add editorial capabilities"
```

## Task 3: Add `ops_status_analysis` capability

**Files:**
- Create: `src/tech_daily/capabilities/ops_status_analysis.py`
- Test: `tests/test_ops_status_analysis_capability.py`
- Modify: `src/tech_daily/healthcheck.py`
- Modify: `tests/test_healthcheck.py`

- [ ] **Step 1: Write the failing ops analysis tests**

```python
from tech_daily.capabilities.ops_status_analysis import OpsStatusAnalysisCapability


def test_ops_status_analysis_extracts_operator_brief():
    capability = OpsStatusAnalysisCapability()
    result = capability.analyze(
        {
            "recent_runtime_diagnostics": [{"company_slug": "tesla", "severity": "error", "issues": ["http_403_blocked"]}],
            "high_priority_runtime_issues": [{"company_slug": "tesla", "severity": "error", "issues": ["http_403_blocked"]}],
            "recently_recovered_runtime_issues": [{"company_slug": "alibaba", "issues": ["zero_fetched_entries"]}],
            "runtime_history_summary": [],
        }
    )

    assert result.current_issues[0]["company_slug"] == "tesla"
    assert result.high_priority[0]["company_slug"] == "tesla"
    assert result.recently_recovered[0]["company_slug"] == "alibaba"
    assert "tesla" in result.operator_brief.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_ops_status_analysis_capability -v`  
Expected: FAIL with missing capability module

- [ ] **Step 3: Write the minimal implementation and wire it into `healthcheck.py`**

```python
@dataclass(slots=True)
class OpsStatusAnalysisOutput:
    current_issues: list[dict]
    high_priority: list[dict]
    recently_recovered: list[dict]
    operator_brief: str


class OpsStatusAnalysisCapability:
    def analyze(self, snapshot: dict) -> OpsStatusAnalysisOutput:
        current_issues = snapshot.get("recent_runtime_diagnostics", [])
        high_priority = snapshot.get("high_priority_runtime_issues", [])
        recently_recovered = snapshot.get("recently_recovered_runtime_issues", [])
        operator_brief = self._build_operator_brief(current_issues, high_priority, recently_recovered)
        return OpsStatusAnalysisOutput(
            current_issues=current_issues,
            high_priority=high_priority,
            recently_recovered=recently_recovered,
            operator_brief=operator_brief,
        )
```

And in `healthcheck.py`:

```python
ops_analysis = OpsStatusAnalysisCapability().analyze(snapshot)
snapshot["ops_status_analysis"] = asdict(ops_analysis)
result["ops_status_analysis"] = asdict(ops_analysis)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_ops_status_analysis_capability tests.test_healthcheck -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/capabilities/ops_status_analysis.py src/tech_daily/healthcheck.py tests/test_ops_status_analysis_capability.py tests/test_healthcheck.py
git commit -m "feat: add ops status analysis capability"
```

## Task 4: Complete facade compatibility and CLI output

**Files:**
- Modify: `src/tech_daily/summarizer.py`
- Modify: `src/tech_daily/editorial.py`
- Modify: `src/tech_daily/cli.py`
- Modify: `tests/test_summarizer.py`
- Modify: `tests/test_editorial.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing compatibility tests**

```python
def test_summarizer_returns_summary_text_from_brief_generation_capability():
    service = Summarizer(mode="rule")
    result = service.summarize(entry, ["developer"], "product")
    assert isinstance(result, str)


def test_health_check_cli_can_print_operator_brief_without_breaking_existing_summary():
    result = main(["health-check"])
    assert result == 0
    assert "high_priority_runtime" in output
    assert "operator_brief=" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_summarizer tests.test_editorial tests.test_cli -v`  
Expected: FAIL on missing delegated behavior or missing `operator_brief`

- [ ] **Step 3: Write the minimal compatibility implementation**

```python
def summarize(self, entry: RawEntry, tags: list[str], category: str) -> str:
    payload = BriefGenerationInput(
        company=entry.company_name,
        title=entry.title,
        summary=entry.summary,
        tags=tags,
        category=category,
        url=entry.url,
        published_at=entry.published_at or "",
        raw_entry=entry,
    )
    return self.capability.generate(payload).summary_cn
```

And in `cli.py`:

```python
ops_analysis = result.get("ops_status_analysis", {})
if ops_analysis.get("operator_brief"):
    print(f"operator_brief={ops_analysis['operator_brief']}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_summarizer tests.test_editorial tests.test_cli -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/summarizer.py src/tech_daily/editorial.py src/tech_daily/cli.py tests/test_summarizer.py tests/test_editorial.py tests/test_cli.py
git commit -m "refactor: delegate facades to capabilities"
```

## Task 5: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-05-13-improvement-roadmap.md`

- [ ] **Step 1: Write the failing documentation assertions**

```python
def test_readme_mentions_capabilities_layer():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "capabilities" in text
    assert "ops_status_analysis" in text
```

- [ ] **Step 2: Run the focused checks to verify the docs are stale**

Run: `python -m unittest tests.test_cli -v`  
Expected: PASS for CLI only; documentation updates still pending and will be verified by manual diff review

- [ ] **Step 3: Update documentation**

```markdown
- `capabilities/brief_generation.py`: 单条摘要能力边界
- `capabilities/topic_comparison.py`: 主题对比能力边界
- `capabilities/daily_editorial.py`: 日报顶部编辑能力边界
- `capabilities/ops_status_analysis.py`: 运维状态分析能力边界
```

- [ ] **Step 4: Run full verification**

Run: `python -m unittest discover -s tests -v`  
Expected: PASS with all tests green

Run: `python run_dashboard.py health-check`  
Expected: exit `0` and output includes `snapshot_path=` plus `operator_brief=`

Run: `powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_report.ps1`  
Expected: exit `0` and `build/data/health_snapshot.json` remains present after the run

- [ ] **Step 5: Commit**

```bash
git add README.md docs/2026-05-13-improvement-roadmap.md
git commit -m "docs: document agent-ready capability layer"
```

## Self-Review

### Spec coverage

- Capability layer creation: covered by Tasks 1-3
- Old facade delegation: covered by Task 4
- `ops_status_analysis` consuming `health_snapshot`: covered by Task 3
- Compatibility requirements: covered by Tasks 4-5
- README and roadmap sync: covered by Task 5

### Placeholder scan

- No `TODO` or `TBD` placeholders remain
- Each task contains explicit file paths, commands, and concrete code snippets

### Type consistency

- `mode_used` is present across all capability outputs
- `ops_status_analysis` is introduced as a named payload block in both result and snapshot paths
- `BriefGenerationInput` carries `raw_entry` so existing summarizer behavior can delegate without reconstructing missing fields
