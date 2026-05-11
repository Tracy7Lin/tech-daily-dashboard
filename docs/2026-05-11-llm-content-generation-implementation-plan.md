# 科技日报 LLM 内容生成实施计划

## 目标

为内容表达层引入可配置的 LLM 增强能力，同时保持规则实现作为稳定回退路径。

## 文件范围

- 新增：
  - `src/tech_daily/rule_summarizer.py`
  - `src/tech_daily/rule_editorial.py`
  - `src/tech_daily/llm_client.py`
  - `src/tech_daily/llm_summarizer.py`
  - `src/tech_daily/llm_editorial.py`
- 重构：
  - `src/tech_daily/summarizer.py`
  - `src/tech_daily/editorial.py`
  - `src/tech_daily/settings.py`
- 测试：
  - `tests/test_settings.py`
  - `tests/test_llm_client.py`
  - `tests/test_summarizer.py`
  - `tests/test_editorial.py`

## 步骤

### 1. 先补失败测试

- 设置应支持从环境变量切换模式
- LLM 客户端应能解析结构化 JSON
- 未配置 API key 时，门面应退回规则实现
- LLM 调用失败时，`hybrid` 应回退到规则实现

### 2. 拆出规则实现

- 把现有摘要规则迁移到 `rule_summarizer.py`
- 把现有编辑规则迁移到 `rule_editorial.py`

### 3. 实现 LLM 层

- `llm_client.py`：HTTP + JSON schema 输出解析
- `llm_summarizer.py`：单条新闻 prompt
- `llm_editorial.py`：headline / topic prompt

### 4. 实现门面与配置

- `summarizer.py`：根据 `summary_mode` 决定 rule / llm / hybrid
- `editorial.py`：根据 `editorial_mode` 决定 rule / llm / hybrid
- `settings.py`：统一加载运行时配置

### 5. 验证

- `python -m unittest discover -s tests -v`
- `python run_dashboard.py backfill --end-date 2026-05-11 --days 7 --output-dir build/site`
- 抽查首页和单日详情页
