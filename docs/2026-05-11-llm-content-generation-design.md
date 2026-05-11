# 科技日报 LLM 内容生成设计

## 目标

在不破坏当前事实抽取稳定性的前提下，引入 LLM 提升：

- 单条新闻中文摘要质量
- 首页总览的编辑表达
- 主题对比的解释力

本轮只替换 `表达层`，不替换：

- 抓取
- 日期判断
- 去重
- 高噪音过滤
- 基础标签与重要度

## 架构原则

- 高内聚低耦合
- 规则层保底，LLM 层增强
- 表达层可切换：`rule / llm / hybrid`
- LLM 失败必须可回退
- 不把 API 调用逻辑塞进 `pipeline.py`、`topics.py`、`classifier.py`

## 模块拆分

新增或重构模块：

- `src/tech_daily/rule_summarizer.py`
  - 保留现有规则摘要逻辑
- `src/tech_daily/rule_editorial.py`
  - 保留现有规则编辑逻辑
- `src/tech_daily/llm_client.py`
  - 统一 LLM HTTP 调用与 JSON 输出解析
- `src/tech_daily/llm_summarizer.py`
  - 单条新闻 LLM 摘要
- `src/tech_daily/llm_editorial.py`
  - 首页 headline 与主题对比 LLM 表达
- `src/tech_daily/summarizer.py`
  - 统一门面，根据配置选择 `rule / llm / hybrid`
- `src/tech_daily/editorial.py`
  - 统一门面，根据配置选择 `rule / llm / hybrid`

## 配置方案

通过 `settings.py` 引入运行时配置：

- `summary_mode`: `rule | llm | hybrid`
- `editorial_mode`: `rule | llm | hybrid`
- `llm_api_url`
- `llm_api_key`
- `llm_model`
- `llm_timeout_seconds`
- `llm_fallback_enabled`

默认策略：

- `summary_mode = hybrid`
- `editorial_mode = hybrid`
- `llm_fallback_enabled = true`

也就是说：

- 有可用 LLM 配置时，先尝试 LLM
- LLM 报错、超时或输出无效时，回退到规则实现
- 没有配置密钥时，系统自然退化为规则模式

## Prompt 边界

### 单条新闻摘要

输入：

- 公司名
- 标题
- 原始摘要
- 标签
- 分类

输出 JSON：

- `summary_cn`

约束：

- 1-3 句
- 不能发明未出现事实
- 必须解释“为什么值得看”
- 用中文简报口吻，而不是研究报告口吻

### 编辑层

输入：

- 主题标题
- 主题内代表事件的公司名、标题、摘要、标签、分类
- 当日热点主题与活跃公司

输出 JSON：

- `headline`
- `summary`
- `comparison`
- `trend`

约束：

- 偏轻量行业分析博客
- 不暴露内部标签名
- 不输出“根据提供信息”“无法判断”之类元话术

## Fallback 机制

以下情况强制回退到规则实现：

- 未配置 API key
- HTTP 请求失败
- 超时
- 返回非 JSON
- JSON 缺字段
- 生成文本为空

门面层负责回退，不让上层模块关心失败细节。

## 成本控制策略

- 单条摘要仅传：
  - 标题
  - 简短摘要
  - 标签 / 分类
- 编辑层仅传：
  - 热点主题
  - 每个主题前 3-4 条代表事件
- 不把整天所有原文全文交给 LLM
- 不在渲染层重复调用 LLM
- 一次构建期间不重复生成相同文本

本轮不实现复杂缓存，只确保门面结构允许未来增加缓存。

## 验收标准

- 未配置 LLM 时，系统行为与当前原型兼容
- 配置 LLM 后，`summarizer` 与 `editorial` 可以切到 `llm/hybrid`
- LLM 失败时能自动回退
- 现有测试继续通过，并新增：
  - 设置加载测试
  - LLM 客户端解析测试
  - hybrid 回退测试

## 非目标

- 本轮不引入数据库缓存
- 本轮不改抓取器
- 本轮不做批量并发优化
- 本轮不强绑定特定云厂商 SDK
