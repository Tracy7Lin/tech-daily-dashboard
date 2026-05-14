# 科技巨头每日情报看板

一个面向个人使用的科技情报日报生成器。

项目会从预设的科技公司官方渠道抓取动态，完成筛选、摘要、主题聚合与横向对比，并输出可归档的静态网页与 JSON 报告。

## Overview

- 官方信源优先，降低噪音与二手转载干扰
- 支持规则模式、LLM 模式与 `hybrid` 混合模式
- 首页以主题对比为核心，而不是简单按公司堆叠新闻
- 输出静态站点，便于本地查看、归档和后续部署

这个仓库现在作为独立项目维护，建议本地放在类似 `<workspace>/tech-daily-dashboard` 的子目录下，而不是与其他实验性内容混放。

## Features

- 可配置的公司观察名单与官方信源
- 面向日报场景的中文摘要生成
- 跨公司主题聚合与差异对比
- 当日首页、详情页与历史归档产物
- LLM 不可用时自动回退到规则表达
- `health-check` 支持最近一次与最近几天的源级运行诊断
- 本地自动化脚本会在生成后追加一次健康检查并写入日志

## Quick Start

### 1. 环境准备

- Python 3.11+
- 可选：兼容 OpenAI API 的 LLM 服务

### 2. 安装与配置

复制配置模板：

```bash
copy .env.example .env
```

然后按需填写：

- `TECH_DAILY_SUMMARY_MODE`
- `TECH_DAILY_EDITORIAL_MODE`
- `TECH_DAILY_LLM_API_URL`
- `TECH_DAILY_LLM_API_KEY`
- `TECH_DAILY_LLM_MODEL`

### 3. 生成单日日报

```bash
python run_dashboard.py generate --date 2026-05-11 --output-dir build/site
```

### 4. 回填最近几天的日报

```bash
python run_dashboard.py backfill --end-date 2026-05-11 --days 7 --output-dir build/site
```

### 5. 生成北京时间“今天”的日报

```bash
python run_dashboard.py generate-today --output-dir build/site
```

### 6. 注册 Windows 定时任务

先手动验证一次脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_report.ps1
```

再注册每天自动运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_task.ps1 -ScheduleTime 08:30
```

如需删除任务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\unregister_daily_task.ps1
```

### 7. 运行健康检查

```bash
python run_dashboard.py health-check
```

该命令当前会输出三层信息：

- 当前环境与配置是否 ready
- 最近一次日报运行中的源问题
- 最近几天重复出现的源问题汇总

### 8. 执行 dry-run 预演

```bash
python run_dashboard.py dry-run --date 2026-05-12
```

或者直接预演北京时间今天：

```bash
python run_dashboard.py dry-run --today
```

## Output

默认生成结果位于：

- `build/site/index.html`
- `build/site/archive.html`
- `build/site/<date>/index.html`
- `build/site/<date>/report.json`
- `build/logs/<date>.log`

## Project Layout

- `config/companies.json`: 公司与信源配置
- `src/tech_daily`: 核心业务代码
- `templates/`: 静态页面模板
- `scripts/`: 本地自动化与定时任务脚本
- `tests/`: 单元测试与回归测试
- `docs/`: 需求、设计与实现文档
- `build/`: 本地生成产物

## Configuration

### LLM 相关配置

- `TECH_DAILY_SUMMARY_MODE`: `rule` / `llm` / `hybrid`
- `TECH_DAILY_EDITORIAL_MODE`: `rule` / `llm` / `hybrid`
- `TECH_DAILY_LLM_API_URL`: LLM API 地址
- `TECH_DAILY_LLM_API_KEY`: LLM API Key
- `TECH_DAILY_LLM_MODEL`: 模型名
- `TECH_DAILY_LLM_TIMEOUT_SECONDS`: 请求超时秒数
- `TECH_DAILY_LLM_FALLBACK_ENABLED`: 是否启用规则回退

推荐默认值：

- `TECH_DAILY_SUMMARY_MODE=hybrid`
- `TECH_DAILY_EDITORIAL_MODE=hybrid`

### 观察名单与信源

默认观察名单和官方信源维护在：

`config/companies.json`

你可以在这里扩展公司、RSS 源、HTML 页面源和过滤规则。

## Architecture

项目保持高内聚、低耦合，职责边界如下：

- `collector.py`: 采集与基础去重
- `normalize.py` / `quality.py`: 归一化与质量过滤
- `classifier.py`: 标签、分类与重要度判定
- `capabilities/brief_generation.py`: 单条摘要能力边界
- `capabilities/topic_comparison.py`: 主题对比能力边界
- `capabilities/daily_editorial.py`: 日报顶部编辑能力边界
- `capabilities/ops_status_analysis.py`: 运维状态分析能力边界
- `summarizer.py`: 单条摘要门面
- `editorial.py`: 首页与主题分析门面
- `healthcheck.py`: 运维状态产出与 snapshot 落盘
- `topics.py`: 主题聚合
- `render.py`: 静态页面渲染
- `pipeline.py`: 日报生成编排

其中 LLM 只用于表达层，不参与抓取、日期判断、去重和基础分类。

## Verification

运行测试：

```bash
python -m unittest discover -s tests -v
```

生成真实日报进行本地验证：

```bash
python run_dashboard.py generate --date 2026-05-11 --output-dir build/site
```

验证自动化入口：

```bash
python run_dashboard.py generate-today --output-dir build/site
```

验证本地运行环境：

```bash
python run_dashboard.py health-check
```

验证自动化脚本会同时完成日报生成与健康检查日志记录：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_report.ps1
```

验证某个日报日期按当前配置是否可执行但不真正抓取或写文件：

```bash
python run_dashboard.py dry-run --date 2026-05-12
```

## Roadmap

- 继续提升摘要与主题分析的稳定性
- 精修不同公司站点的发布时间与正文提取
- 增加更强的历史检索与筛选能力
- 继续增强源级运维观测，例如失败趋势、重复异常与长期低产出提醒
- 为未来的科技情报分析 agent 保留可复用 skill 边界
- 增加兄弟日报：`GitHub 今日 Highlight 日报`，聚焦当天或最近热门的 GitHub 项目、趋势仓库与高讨论度开源动态
