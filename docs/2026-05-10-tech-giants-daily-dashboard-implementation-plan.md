# 科技巨头每日情报看板 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个配置驱动的静态日报生成器，能够采集官方来源、规范化内容、生成摘要与主题对比，并输出可归档的静态网页。

**Architecture:** 采用 Python 标准库优先的单仓结构。按 `配置`、`领域模型`、`采集器`、`处理流水线`、`渲染器`、`输出产物` 分层，模块之间通过显式数据对象传递，避免把抓取、业务判断和页面生成耦合在一起。

**Tech Stack:** Python 3.12、标准库 `urllib` / `xml.etree.ElementTree` / `html.parser` / `json` / `dataclasses` / `zoneinfo`、Node 仅作为可选静态预览环境

---

### Task 1: 建立项目骨架与运行入口

**Files:**
- Create: `src/tech_daily/__init__.py`
- Create: `src/tech_daily/cli.py`
- Create: `src/tech_daily/settings.py`
- Create: `src/tech_daily/paths.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 写 CLI 失败用例**

```python
from tech_daily.cli import build_parser


def test_build_parser_supports_generate_command():
    parser = build_parser()
    args = parser.parse_args(["generate", "--date", "2026-05-10"])
    assert args.command == "generate"
    assert args.date == "2026-05-10"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_cli.py -q`
Expected: FAIL with `ModuleNotFoundError` or missing `build_parser`

- [ ] **Step 3: 实现最小 CLI 与路径配置**

```python
from argparse import ArgumentParser


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="tech-daily")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--date", required=True)
    return parser
```

- [ ] **Step 4: 再跑测试，确认通过**

Run: `python -m pytest tests/test_cli.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tech_daily tests/test_cli.py
git commit -m "feat: scaffold cli entrypoint"
```

### Task 2: 定义核心领域模型

**Files:**
- Create: `src/tech_daily/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 写模型失败用例**

```python
from tech_daily.models import Company, Source, RawEntry


def test_company_contains_multiple_sources():
    company = Company(
        slug="openai",
        name="OpenAI",
        region="us",
        sources=[Source(kind="rss", url="https://openai.com/news/rss.xml")],
    )
    assert company.slug == "openai"
    assert company.sources[0].kind == "rss"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_models.py -q`
Expected: FAIL because models do not exist

- [ ] **Step 3: 实现领域对象**

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    kind: str
    url: str
    label: str = ""


@dataclass(frozen=True)
class Company:
    slug: str
    name: str
    region: str
    sources: list[Source] = field(default_factory=list)
```

- [ ] **Step 4: 再跑测试**

Run: `python -m pytest tests/test_models.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tech_daily/models.py tests/test_models.py
git commit -m "feat: add core domain models"
```

### Task 3: 实现配置加载与默认观察名单

**Files:**
- Create: `config/companies.json`
- Create: `src/tech_daily/config_loader.py`
- Create: `tests/test_config_loader.py`

- [ ] **Step 1: 写配置加载失败用例**

```python
from tech_daily.config_loader import load_companies


def test_load_companies_returns_default_watchlist():
    companies = load_companies()
    assert len(companies) == 15
    assert companies[0].slug
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_config_loader.py -q`
Expected: FAIL because loader/config does not exist

- [ ] **Step 3: 添加默认名单与加载器**

```json
[
  {"slug": "openai", "name": "OpenAI", "region": "us", "sources": []}
]
```

```python
def load_companies() -> list[Company]:
    data = json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))
    return [Company(... ) for ... in data]
```

- [ ] **Step 4: 再跑测试**

Run: `python -m pytest tests/test_config_loader.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add config/companies.json src/tech_daily/config_loader.py tests/test_config_loader.py
git commit -m "feat: add company watchlist config"
```

### Task 4: 实现采集层与源适配边界

**Files:**
- Create: `src/tech_daily/fetchers/base.py`
- Create: `src/tech_daily/fetchers/rss.py`
- Create: `src/tech_daily/fetchers/http.py`
- Create: `src/tech_daily/collector.py`
- Create: `tests/test_rss_fetcher.py`

- [ ] **Step 1: 写 RSS 解析失败用例**

```python
from tech_daily.fetchers.rss import parse_rss_entries


def test_parse_rss_entries_extracts_title_and_link():
    xml_text = """<rss><channel><item><title>Launch</title><link>https://example.com/a</link></item></channel></rss>"""
    entries = parse_rss_entries(xml_text)
    assert entries[0].title == "Launch"
    assert entries[0].url == "https://example.com/a"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_rss_fetcher.py -q`
Expected: FAIL because RSS parser does not exist

- [ ] **Step 3: 实现 fetcher 抽象与 RSS 解析**

```python
def parse_rss_entries(xml_text: str) -> list[RawEntry]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    return [RawEntry(title=item.findtext("title", default=""), url=item.findtext("link", default="")) for item in items]
```

- [ ] **Step 4: 再跑测试**

Run: `python -m pytest tests/test_rss_fetcher.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tech_daily/fetchers src/tech_daily/collector.py tests/test_rss_fetcher.py
git commit -m "feat: add rss collection pipeline"
```

### Task 5: 实现过滤、标签与摘要边界

**Files:**
- Create: `src/tech_daily/classifier.py`
- Create: `src/tech_daily/summarizer.py`
- Create: `tests/test_classifier.py`

- [ ] **Step 1: 写分类失败用例**

```python
from tech_daily.classifier import classify_entry
from tech_daily.models import RawEntry


def test_classify_entry_marks_ai_product_news():
    entry = RawEntry(title="OpenAI launches new agent tooling", url="https://example.com", summary="New agent APIs for developers")
    result = classify_entry(entry)
    assert "ai" in result.tags
    assert "product" in result.tags
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_classifier.py -q`
Expected: FAIL because classifier does not exist

- [ ] **Step 3: 实现规则型分类与摘要接口**

```python
KEYWORDS = {
    "ai": {"ai", "model", "agent"},
    "product": {"launch", "product", "release"},
}
```

```python
class Summarizer:
    def summarize(self, entry: NormalizedEntry) -> Summary:
        ...
```

- [ ] **Step 4: 再跑测试**

Run: `python -m pytest tests/test_classifier.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tech_daily/classifier.py src/tech_daily/summarizer.py tests/test_classifier.py
git commit -m "feat: add classification and summarization interfaces"
```

### Task 6: 实现主题聚合与对比生成

**Files:**
- Create: `src/tech_daily/topics.py`
- Create: `tests/test_topics.py`

- [ ] **Step 1: 写主题聚合失败用例**

```python
from tech_daily.topics import group_entries_by_topic


def test_group_entries_by_topic_clusters_shared_tags():
    grouped = group_entries_by_topic([...])
    assert "ai-agent" in grouped
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_topics.py -q`
Expected: FAIL because topics module does not exist

- [ ] **Step 3: 实现主题分组与对比草案生成**

```python
def group_entries_by_topic(entries: list[EnrichedEntry]) -> dict[str, list[EnrichedEntry]]:
    ...
```

- [ ] **Step 4: 再跑测试**

Run: `python -m pytest tests/test_topics.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tech_daily/topics.py tests/test_topics.py
git commit -m "feat: add topic comparison pipeline"
```

### Task 7: 实现静态页面渲染

**Files:**
- Create: `src/tech_daily/render.py`
- Create: `templates/index.html`
- Create: `templates/daily.html`
- Create: `templates/archive.html`
- Create: `tests/test_render.py`

- [ ] **Step 1: 写渲染失败用例**

```python
from tech_daily.render import render_index


def test_render_index_contains_topic_section():
    html = render_index(...)
    assert "主题对比" in html
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_render.py -q`
Expected: FAIL because render module does not exist

- [ ] **Step 3: 实现模板渲染与产物写入**

```python
def render_index(report: DailyReport) -> str:
    template = INDEX_TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{ date }}", report.date)
```

- [ ] **Step 4: 再跑测试**

Run: `python -m pytest tests/test_render.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tech_daily/render.py templates tests/test_render.py
git commit -m "feat: add static site rendering"
```

### Task 8: 串起生成流水线并验证

**Files:**
- Create: `src/tech_daily/pipeline.py`
- Create: `README.md`
- Modify: `src/tech_daily/cli.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: 写端到端失败用例**

```python
from tech_daily.pipeline import generate_daily_report


def test_generate_daily_report_returns_report_object(tmp_path):
    report = generate_daily_report("2026-05-10", output_dir=tmp_path)
    assert report.date == "2026-05-10"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_pipeline.py -q`
Expected: FAIL because pipeline does not exist

- [ ] **Step 3: 实现流水线编排并接入 CLI**

```python
def generate_daily_report(date_str: str, output_dir: Path) -> DailyReport:
    companies = load_companies()
    raw_entries = collect_entries(companies, date_str)
    enriched_entries = enrich_entries(raw_entries)
    report = build_report(enriched_entries, date_str)
    write_site(report, output_dir)
    return report
```

- [ ] **Step 4: 运行核心测试集合**

Run: `python -m pytest tests -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add README.md src/tech_daily tests
git commit -m "feat: wire daily report pipeline"
```
