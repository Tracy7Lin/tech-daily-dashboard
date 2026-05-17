# Magazine Front-End Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the front end into a magazine-style publication with a cover homepage, lighter daily issue pages, and dedicated topic/dossier reading pages.

**Architecture:** Keep the existing static generation pipeline and add new rendered pages plus clearer navigation. Move depth content out of the daily issue page into dedicated topic and dossier pages, then redesign visual language and motion so the site reads like a technology intelligence magazine instead of a dashboard.

**Tech Stack:** Python static rendering, HTML templates, inline CSS/JS, unittest, existing agent-generated JSON/Markdown artifacts

---

## File Structure

- Create: `src/tech_daily/magazine_pages.py`
  - Build navigation-oriented derived page payloads for home, topic, and dossier pages.
- Modify: `src/tech_daily/render.py`
  - Add rendering entry points for the new cover homepage and deep-reading pages.
- Modify: `src/tech_daily/pipeline.py`
  - Ensure new page payloads are attached after existing report/agent generation.
- Modify: `src/tech_daily/models.py`
  - Add small typed containers if needed for page payloads and navigation blocks.
- Create: `templates/home_magazine.html`
  - Dedicated cover-style homepage template.
- Create: `templates/topic.html`
  - Dedicated topic page template for cross-day, tracking, and dossier summary.
- Create: `templates/dossier.html`
  - Dedicated dossier page template.
- Modify: `templates/index.html`
  - Either redirect to or re-scope current home rendering so it becomes a magazine cover, not a dashboard.
- Modify: `templates/daily.html`
  - Slim down daily issue layout and add navigation links to topic/dossier pages.
- Test: `tests/test_render.py`
  - Add render assertions for new pages and slimmer daily issue content.
- Test: `tests/test_pipeline.py`
  - Add pipeline assertions for new page payloads and output paths.
- Test: `tests/test_magazine_pages.py`
  - Add focused unit tests for navigation/page payload assembly.

### Task 1: Add page payload builder for magazine navigation

**Files:**
- Create: `src/tech_daily/magazine_pages.py`
- Test: `tests/test_magazine_pages.py`

- [ ] **Step 1: Write the failing tests**

```python
from tech_daily.magazine_pages import build_magazine_pages


def test_build_magazine_pages_returns_cover_topic_and_dossier_blocks(sample_daily_report):
    pages = build_magazine_pages(sample_daily_report)
    assert pages["cover"]["primary_theme"] == "安全与治理"
    assert pages["topic_page"]["title"] == "安全与治理"
    assert pages["dossier_page"]["title"] == "安全与治理"


def test_build_magazine_pages_includes_recent_issue_links(sample_daily_report):
    pages = build_magazine_pages(sample_daily_report)
    assert pages["cover"]["recent_issues"]
    assert pages["cover"]["recent_issues"][0]["href"].endswith("/index.html")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_magazine_pages.py -v`  
Expected: FAIL with `ModuleNotFoundError` or missing `build_magazine_pages`

- [ ] **Step 3: Write minimal implementation**

```python
def build_magazine_pages(report):
    primary_theme = (report.theme_tracking_brief or {}).get("primary_theme") or "暂无主专题"
    return {
        "cover": {
            "primary_theme": primary_theme,
            "recent_issues": [{"href": f"./{report.date}/index.html", "label": report.date}],
        },
        "topic_page": {"title": primary_theme},
        "dossier_page": {"title": primary_theme},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_magazine_pages.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_magazine_pages.py src/tech_daily/magazine_pages.py
git commit -m "feat: add magazine page payload builder"
```

### Task 2: Attach magazine page payloads in the pipeline

**Files:**
- Modify: `src/tech_daily/pipeline.py`
- Modify: `src/tech_daily/models.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
def test_generate_report_attaches_magazine_pages(self):
    report = generate_report(...)
    self.assertIn("cover", report.magazine_pages)
    self.assertIn("topic_page", report.magazine_pages)
    self.assertIn("dossier_page", report.magazine_pages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_pipeline.py -v`  
Expected: FAIL because `magazine_pages` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
# models.py
magazine_pages: dict = field(default_factory=dict)

# pipeline.py
from .magazine_pages import build_magazine_pages
report.magazine_pages = build_magazine_pages(report)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_pipeline.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tech_daily/models.py src/tech_daily/pipeline.py tests/test_pipeline.py
git commit -m "feat: attach magazine page payloads"
```

### Task 3: Render the new cover homepage

**Files:**
- Create: `templates/home_magazine.html`
- Modify: `src/tech_daily/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
def test_render_home_magazine_outputs_cover_navigation(self):
    render_report_site(report, output_dir)
    html = (output_dir / "index.html").read_text(encoding="utf-8")
    self.assertIn("当前主专题", html)
    self.assertIn("进入专题页", html)
    self.assertIn("查看最新日报", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: FAIL because the old homepage does not render the new cover structure

- [ ] **Step 3: Write minimal implementation**

```python
# render.py
home_template = _load_template("home_magazine.html")
home_html = home_template.substitute(...)
(output_dir / "index.html").write_text(home_html, encoding="utf-8")
```

```html
<!-- home_magazine.html -->
<main class="cover-shell">
  <section class="cover-hero">
    <p class="cover-kicker">Current Topic</p>
    <h1>$primary_theme</h1>
    <p>$cover_summary</p>
    <nav class="cover-actions">
      <a href="$topic_href">进入专题页</a>
      <a href="$daily_href">查看最新日报</a>
    </nav>
  </section>
</main>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add templates/home_magazine.html src/tech_daily/render.py tests/test_render.py
git commit -m "feat: render magazine-style homepage"
```

### Task 4: Split deep-reading content into topic and dossier pages

**Files:**
- Create: `templates/topic.html`
- Create: `templates/dossier.html`
- Modify: `src/tech_daily/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
def test_render_outputs_topic_and_dossier_pages(self):
    render_report_site(report, output_dir)
    self.assertTrue((output_dir / report.date / "topic.html").exists())
    self.assertTrue((output_dir / report.date / "dossier.html").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: FAIL because the new pages do not exist

- [ ] **Step 3: Write minimal implementation**

```python
topic_template = _load_template("topic.html")
dossier_template = _load_template("dossier.html")
(daily_dir / "topic.html").write_text(topic_template.substitute(...), encoding="utf-8")
(daily_dir / "dossier.html").write_text(dossier_template.substitute(...), encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add templates/topic.html templates/dossier.html src/tech_daily/render.py tests/test_render.py
git commit -m "feat: add topic and dossier pages"
```

### Task 5: Slim down the daily issue page and add navigation

**Files:**
- Modify: `templates/daily.html`
- Modify: `src/tech_daily/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
def test_daily_issue_links_to_topic_and_dossier_pages(self):
    render_report_site(report, output_dir)
    html = (output_dir / report.date / "index.html").read_text(encoding="utf-8")
    self.assertIn("进入专题页", html)
    self.assertIn("查看主题档案", html)
    self.assertNotIn("查看完整 dossier Markdown", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: FAIL because the old daily page still inlines deep content blocks

- [ ] **Step 3: Write minimal implementation**

```html
<section class="issue-nav">
  <a href="./topic.html">进入专题页</a>
  <a href="./dossier.html">查看主题档案</a>
</section>
```

```python
# render.py
# reduce inline deep blocks to shorter summaries plus links
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add templates/daily.html src/tech_daily/render.py tests/test_render.py
git commit -m "feat: slim daily issue layout"
```

### Task 6: Apply magazine visual language and motion

**Files:**
- Modify: `templates/home_magazine.html`
- Modify: `templates/daily.html`
- Modify: `templates/topic.html`
- Modify: `templates/dossier.html`
- Modify: `templates/index.html` (if retained for shared chat shell behavior)
- Test: `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
def test_homepage_contains_magazine_navigation_and_motion_hooks(self):
    render_report_site(report, output_dir)
    html = (output_dir / "index.html").read_text(encoding="utf-8")
    self.assertIn("cover-hero", html)
    self.assertIn("section-rail", html)
    self.assertIn("data-reveal", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: FAIL because the new classes and motion hooks do not exist yet

- [ ] **Step 3: Write minimal implementation**

```html
<section class="cover-hero" data-reveal="hero">...</section>
<section class="section-rail" data-reveal="rail">...</section>
```

```css
.cover-hero { /* cover composition */ }
.section-rail { /* editorial navigation strip */ }
[data-reveal] { animation: fadeLift 420ms ease both; }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s tests -p test_render.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add templates/home_magazine.html templates/daily.html templates/topic.html templates/dossier.html tests/test_render.py
git commit -m "feat: add magazine motion and visual hierarchy"
```

### Task 7: Full verification and docs sync

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-05-17-next-phase-plan.md`

- [ ] **Step 1: Update usage docs**

```markdown
- Homepage is now the magazine cover
- Daily issues live at `build/site/<date>/index.html`
- Topic pages live at `build/site/<date>/topic.html`
- Dossier pages live at `build/site/<date>/dossier.html`
```

- [ ] **Step 2: Run full tests**

Run: `python -m unittest discover -s tests -v`  
Expected: `OK`

- [ ] **Step 3: Generate a fresh site build**

Run: `python run_dashboard.py generate-today --output-dir build/site`  
Expected: exit code 0 and new `topic.html` / `dossier.html` files under today’s directory

- [ ] **Step 4: Commit**

```bash
git add README.md docs/2026-05-17-next-phase-plan.md build/site src/tech_daily templates tests
git commit -m "feat: complete magazine front-end redesign"
```

## Self-Review

- Spec coverage: The plan covers homepage cover conversion, daily issue simplification, deep-reading page split, magazine motion, and docs sync.
- Placeholder scan: No `TODO`/`TBD` markers remain. Each task includes files, tests, commands, and code direction.
- Type consistency: `magazine_pages`, `topic_page`, and `dossier_page` are referenced consistently across payload, pipeline, and render tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-17-magazine-front-end-redesign.md`.  
Execution mode selected: **Inline Execution**.
