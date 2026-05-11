# 科技巨头每日情报看板

一个面向个人使用的静态日报生成器。它读取公司与信源配置，抓取官方动态，进行规则或 LLM 混合摘要与主题归类，并输出可归档的静态网页。

## 当前目标

- 配置驱动的公司观察名单
- 官方来源优先
- 中文速览摘要
- 主题对比优先的首页
- 静态 HTML 与 JSON 产物

## 目录结构

- `config/companies.json`: 默认观察名单与信源配置
- `src/tech_daily`: 核心代码
- `templates/`: 静态页面模板
- `docs/`: 需求、设计、计划文档
- `build/`: 运行产物

## 运行方式

```bash
python run_dashboard.py generate --date 2026-05-10
```

如果希望指定输出目录：

```bash
python run_dashboard.py generate --date 2026-05-10 --output-dir build/site
```

如果希望回填最近几天的日报归档：

```bash
python run_dashboard.py backfill --end-date 2026-05-10 --days 7 --output-dir build/site
```

## 当前实现边界

首版使用 Python 标准库实现，重点是保留高内聚、低耦合结构：

- `collector.py` 只负责采集
- `classifier.py` / `summarizer.py` 只负责内容理解
- `topics.py` 只负责主题聚合
- `render.py` 只负责静态站点输出
- `pipeline.py` 只负责编排

后续可扩展方向：

- 替换为更强的 LLM 摘要器
- 为不同站点添加更精准的源适配器
- 引入历史归档索引
- 将站点升级为动态看板

## LLM 表达层配置

当前实现只把 LLM 用在内容表达层，不用在抓取、日期判断、去重和基础分类上。

建议先将 `.env.example` 复制为 `.env`，再填入你自己的模型地址和密钥。`.env` 已加入忽略，不会进入版本控制。

- `TECH_DAILY_SUMMARY_MODE`: `rule` / `llm` / `hybrid`
- `TECH_DAILY_EDITORIAL_MODE`: `rule` / `llm` / `hybrid`
- `TECH_DAILY_LLM_API_URL`: 默认 `https://api.openai.com/v1/responses`
- `TECH_DAILY_LLM_API_KEY`: LLM API Key
- `TECH_DAILY_LLM_MODEL`: 默认 `deepseekv4`
- `TECH_DAILY_LLM_TIMEOUT_SECONDS`: 默认 `20`
- `TECH_DAILY_LLM_FALLBACK_ENABLED`: 默认 `true`

推荐默认值：

- `TECH_DAILY_SUMMARY_MODE=hybrid`
- `TECH_DAILY_EDITORIAL_MODE=hybrid`

这意味着：

- 有可用 LLM 时，用 LLM 生成单条中文简报和首页/主题分析文案
- LLM 不可用或调用失败时，自动退回现有规则表达
