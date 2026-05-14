# 科技日报 Agent-Ready Refactor 设计文档

## 1. 文档目的

这份文档用于定义 `tech-daily-dashboard` 的下一阶段重构目标：  
在不引入真正 agent orchestration 的前提下，把当前日报系统中的关键表达与运维分析能力，抽象为未来可直接升级为 agent skill 的稳定能力边界。

这次工作的目标不是“做一个 agent”，而是：

- 保持现有日报产品行为稳定
- 把关键能力从零散门面提升为统一 capability layer
- 让未来的科技情报分析 agent 可以直接复用这些能力

## 2. 背景与动机

当前系统已经具备：

- 稳定的日报生成主链路
- 规则 + LLM 的混合表达层
- 本地自动化与健康检查
- 结构化运维状态产物 `health_snapshot.json`

现状的问题不在“功能缺失”，而在“能力边界还不够正式”：

- `summarizer.py` 和 `editorial.py` 已经接近 skill 门面，但输入输出仍然偏函数式
- `healthcheck.py` 能生成运维状态，但缺少独立的状态分析能力层
- 未来若直接做 agent，很容易把 orchestration、prompt 和业务逻辑再次耦合在一起

因此，这一步需要先做一次 `agent-ready refactor`。

## 3. 设计目标

本次重构的目标如下：

1. 新增正式的 capability layer，收口未来 agent 可复用的 4 个能力边界
2. 保持当前 CLI、页面渲染、日报 JSON、health snapshot 的外部行为稳定
3. 保留 `rule / llm / hybrid` 三种模式，不改变现有模式语义
4. 让旧门面逐步转发到新能力层，而不是一次性替换全部调用路径
5. 为未来 `科技情报分析 agent` 预留稳定输入输出，而不是现在就引入 orchestration

## 4. 非目标

本轮明确不做以下事项：

- 不实现完整 agent runtime
- 不增加 tool orchestration
- 不增加长期记忆
- 不增加新的抓取器体系
- 不改写主日报渲染结构
- 不调整现有 `report.json` 主体格式

## 5. 推荐方案

采用 `正式能力层` 方案。

即：

- 新增独立的 `capabilities` 目录
- 把关键能力定义为结构化输入、结构化输出的模块
- 让现有 `summarizer.py`、`editorial.py`、`healthcheck.py` 逐步转为这些能力层的消费者或适配器

不采用：

- 仅加一层薄包装的方案：后续仍要再次拆分
- 直接实现最小 agent 的方案：当前时机过早，复杂度和调试成本过高

## 6. 能力边界设计

### 6.1 `brief_generation`

职责：

- 负责单条新闻条目的中文表达生成

输入：

- `company`
- `title`
- `summary`
- `tags`
- `category`
- `url`
- `published_at`

输出：

- `summary_cn`
- `angle`
- `confidence`
- `mode_used`

说明：

- `summary_cn` 是最终中文摘要
- `angle` 表示这条内容更偏哪种观察角度，例如产品、客户落地、安全治理等
- `confidence` 用于表达层结果的相对信心，先采用轻量启发式，不要求本轮复杂建模
- `mode_used` 用于标记本次结果来自 `rule / llm / hybrid`

### 6.2 `topic_comparison`

职责：

- 负责主题级 summary / comparison / trend 生成

输入：

- `topic_title`
- `entries`
- `involved_companies`

输出：

- `summary`
- `comparison`
- `trend`
- `mode_used`

说明：

- 这是未来 agent 进行跨公司主题分析的核心能力
- 单公司主题时，仍允许回退到更稳的规则表达

### 6.3 `daily_editorial`

职责：

- 负责日报顶部判断表达

输入：

- `report_date`
- `topic_clusters`
- `company_reports`
- `total_entries`

输出：

- `headline`
- `brief`
- `mode_used`

说明：

- `headline` 面向首页首屏
- `brief` 面向更完整的日报级编辑摘要
- 本轮允许先保留 `brief` 为轻量结果，即使当前前端主要消费 `headline`

### 6.4 `ops_status_analysis`

职责：

- 负责消费 `health_snapshot.json` 并生成结构化运维判断

输入：

- `health_snapshot payload`

输出：

- `current_issues`
- `high_priority`
- `recently_recovered`
- `operator_brief`

说明：

- 这不是替代 `healthcheck.py`
- `healthcheck.py` 继续负责环境检查、最近运行分析和 snapshot 落盘
- `ops_status_analysis` 只负责“理解这些状态意味着什么”

## 7. 建议目录结构

建议新增：

```text
src/tech_daily/capabilities/
  __init__.py
  brief_generation.py
  topic_comparison.py
  daily_editorial.py
  ops_status_analysis.py
```

原则：

- 每个模块只负责一个能力边界
- 不直接依赖 CLI 或模板渲染
- 不在 capability 层拼装抓取逻辑

## 8. 迁移方式

采用 `增量迁移 + 双层兼容`。

### 第一阶段：新增 capability layer

- 先新增 4 个 capability 模块
- 只引入结构化输入输出，不删除现有门面

### 第二阶段：旧门面委托给新层

- `summarizer.py` 委托到 `brief_generation`
- `editorial.py` 委托到 `topic_comparison` 与 `daily_editorial`
- `healthcheck.py` 保留 snapshot 生成职责，逐步把状态理解委托到 `ops_status_analysis`

### 第三阶段：上游逐步切换

后续再视稳定性逐步调整：

- `pipeline.py`
- `render.py`
- `cli.py`
- 自动化脚本输出

本轮不要求一次性全部切换。

## 9. 兼容策略

### 9.1 外部接口兼容

保持以下接口稳定：

- 现有 CLI 命令
- 现有日报主链路
- 现有 `report.json` 结构
- 现有 `health_snapshot.json` 结构

本轮对 `health_snapshot.json` 允许只增不减。

### 9.2 调用路径兼容

- 现有调用方仍然可以继续通过 `summarizer.py` 与 `editorial.py` 使用表达能力
- capability layer 先作为内部正式能力边界存在
- 不强制当前所有模块立即改成直接依赖 capability layer

### 9.3 模式兼容

继续保留：

- `rule`
- `llm`
- `hybrid`

每个 capability 的结构化输出都应透出 `mode_used`。

这样后面无论是：

- 前端
- 自动化
- 运维分析
- 未来 agent

都能明确知道当前结果是如何生成的。

## 10. 测试策略

本轮遵循测试先行。

至少补以下测试：

- capability layer 的结构化输出测试
- 旧门面委托到新能力层的兼容测试
- `ops_status_analysis` 基于 `health_snapshot` 的状态判断测试
- `mode_used` 的透传测试
- 回归测试，确保现有 `pipeline`、`cli`、`health-check` 外部行为不被破坏

## 11. 风险与控制

### 风险 1：抽象过度

风险：

- 这一步可能为了“未来 agent”而引入过多复杂度

控制方式：

- 本轮只抽象 4 个最清晰的能力边界
- 不引入 provider registry、tool routing、memory 等额外层

### 风险 2：旧调用链被打断

风险：

- 现有 `pipeline` 与页面生成可能因重构受影响

控制方式：

- 保留旧门面
- 先委托再迁移
- 先做局部重构，再跑全量回归

### 风险 3：运维状态与表达状态边界混淆

风险：

- `ops_status_analysis` 可能与 `healthcheck.py` 责任重叠

控制方式：

- 明确 `healthcheck.py` 负责“产出状态”
- `ops_status_analysis` 负责“解释状态”

## 12. 完成标准

本轮可视为完成，当满足以下条件：

1. capability layer 已建立
2. `brief_generation / topic_comparison / daily_editorial / ops_status_analysis` 均有稳定输入输出
3. 旧门面已开始委托到新能力层
4. `health_snapshot` 可被 `ops_status_analysis` 直接消费
5. 全量测试通过
6. README 与路线文档已同步反映新的 capability 边界

## 13. 后续衔接

这轮完成后，下一步才适合考虑：

- 进一步把 capability layer 包装成 future skill-like modules
- 增加最小 `科技情报分析 agent`

该 agent 的第一版建议只做：

- 读取当日日报
- 读取 `health_snapshot`
- 生成运营判断与跟踪建议

而不是直接承担完整抓取、研究和多工具编排职责。
