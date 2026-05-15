# 科技日报跨日追踪 Agent 设计文档

## 1. 文档目的

这份文档用于定义 `tech-daily-dashboard` 的第二版 agent 能力：`跨日追踪 agent`。

第一版最小 agent 已经能够：

- 读取当日日报 `report.json`
- 读取 `health_snapshot.json`
- 生成 `daily_intel_brief`
- 同时输出 Markdown 报告与页面区块

第二版的目标不是引入更重的自主搜索或多工具编排，而是在这条稳定主链上增加“连续观察”能力：

- 读取最近 N 天的日报与健康快照
- 识别主题、公司与信源状态的连续变化
- 生成统一的跨日情报观察结果
- 同时输出 Markdown 报告与页面中的 `跨日观察` 区块

## 2. 背景与动机

当前系统已经完成三层基础能力：

1. `日报主链路`
- 抓取
- 过滤
- 分类
- 摘要
- 主题聚合
- 静态渲染

2. `agent-ready capability layer`
- `brief_generation`
- `topic_comparison`
- `daily_editorial`
- `ops_status_analysis`

3. `第一版最小情报分析 agent`
- `daily_intel_brief.json`
- `agent-brief.md`
- 当日日报中的 `情报判断` 区块

当前缺口不再是“能不能生成日报”，而是：

- 缺少一个基于最近几天数据的连续判断层
- 缺少对“主题升温/降温”“公司持续活跃/单日波动”的解释
- 缺少把内容变化和信源变化统一放到时间维度里观察的能力

因此，第二版 agent 的目标是：
**消费最近 N 天日报与健康快照，输出一份可直接阅读、可归档、可供页面复用的跨日情报观察结果。**

## 3. 设计目标

本轮设计目标如下：

1. 读取最近 N 天的日报与健康快照历史
2. 识别跨日连续变化：
- 主题升温
- 主题降温
- 公司持续活跃
- 公司波动
- 持续性信源风险
- 最近恢复的信源
3. 生成统一的 `cross_day_intel_brief`
4. 同时产出：
- Markdown 报告
- 页面中的 `跨日观察` 区块
5. 保持日报主链路稳定，v2 失败时不影响主日报与 v1 agent
6. 为未来更强的“专题跟踪 / 主动研究型 agent”预留升级空间

## 4. 非目标

本轮明确不做以下事项：

- 不实现自主互联网搜索
- 不实现新信源发现
- 不实现长期记忆
- 不实现多工具编排
- 不实现自动专题 dossier 生成
- 不让 v2 反向驱动抓取或修复抓取器
- 不替代 v1 当日情报判断

第二版仍然是：

**一个消费现有日报产物并提供时间维度判断的最小跨日追踪 agent。**

## 5. 推荐方案

采用 `跨日情报观察器` 方案。

即：

- 读取最近 N 天的日报与健康快照
- 识别持续升温/降温主题
- 识别连续活跃/波动公司
- 识别持续风险/最近恢复信源
- 输出统一的跨日情报观察结果

不采用：

- 只把最近几天结果简单罗列的轻量汇总方案
- 直接上自动专题 dossier 的重型方案

原因：

- 轻量汇总的信息价值不够高，更像时间序列摘要
- 自动专题 dossier 超出 v2 最小范围，会把复杂度抬高过快
- `跨日情报观察器` 已经足够体现 agent 的连续观察能力，同时仍然可控

## 6. Agent 职责边界

第二版 agent 只做五件事：

1. 读取最近 N 天日报
2. 读取最近 N 天 health snapshots
3. 识别连续变化：
- 主题升温/降温
- 公司持续活跃/波动
- 持续风险/持续恢复
4. 生成统一的 `cross_day_intel_brief`
5. 输出两种消费形式：
- `cross-day-brief.md`
- 页面中的 `跨日观察` 区块

它应回答的问题包括：

- 这几天哪些主题持续在升温
- 哪些主题明显降温或回落
- 哪些公司是连续活跃，而不是单日波动
- 哪些信源问题仍在持续，哪些刚恢复
- 明天应该优先盯哪些主题和公司

## 7. 输入设计

第二版读取最近 N 天的两类历史产物。

### 7.1 日报输入

路径：

- `build/site/<date>/report.json`

用途：

- 提取每天的主题聚合、公司覆盖、总条数、活跃公司等内容状态

### 7.2 v1 agent 输入

路径：

- `build/site/<date>/daily_intel_brief.json`

用途：

- 复用已有的当日判断结果，减少 v2 对原始日报细节的重复理解

这份输入不是强依赖。
如果某日缺失，v2 仍可退回直接使用 `report.json`。

### 7.3 运维输入

路径：

- `build/data/health_snapshots/<date>.json`

用途：

- 提取某日的：
  - `recent_runtime_diagnostics`
  - `high_priority_runtime_issues`
  - `recently_recovered_runtime_issues`
  - `runtime_history_summary`
  - `ops_status_analysis`

### 7.4 输入原则

- 不直接读取抓取器内部状态
- 不直接重抓 HTML / RSS
- 不让 v2 agent 重新构造事实来源
- 只消费已经生成并落盘的日报与健康状态产物

## 8. 健康快照历史化要求

为了稳定支持跨日运维分析，当前系统需要保证每天健康快照按日期归档保存。

推荐路径：

- `build/data/health_snapshots/<date>.json`

保留：

- `build/data/health_snapshot.json`

作为“最新快照”快捷入口。

历史化要求的目的不是复制存储，而是保证跨日 agent 能稳定读取真实的每日运维状态，而不是被迫从当前最新文件逆推历史。

## 9. 统一分析结果设计

建议新增统一对象：

- `cross_day_intel_brief.json`

推荐路径：

- `build/site/<date>/cross_day_intel_brief.json`

结构至少包含：

- `date_range`
- `warming_themes`
- `cooling_themes`
- `steady_companies`
- `swing_companies`
- `persistent_source_risks`
- `recent_source_recoveries`
- `watchlist`
- `next_day_focus`
- `mode_used`

### 字段说明

#### `date_range`

跨日观察覆盖的日期范围，例如最近 3 天、5 天或 7 天。

#### `warming_themes`

最近几天持续升温、持续出现或重要度提升的主题。

#### `cooling_themes`

最近几天明显减少、回落或热度下降的主题。

#### `steady_companies`

连续多天保持活跃的公司，用于区分“持续活跃”与“单日爆发”。

#### `swing_companies`

波动明显、单日活跃但不稳定的公司。

#### `persistent_source_risks`

连续存在、尚未恢复的信源问题。

#### `recent_source_recoveries`

最近刚恢复稳定的公司或信源。

#### `watchlist`

值得继续跟踪的主题、公司或运维问题。

#### `next_day_focus`

下一天优先应该关注的主题、公司或信源。

#### `mode_used`

标记这份跨日观察是 `rule / llm / hybrid`。

## 10. 输出设计

### 10.1 Markdown 报告

路径建议：

- `build/site/<date>/cross-day-brief.md`

结构建议：

- 标题
- 最近几天主线
- 升温主题
- 降温主题
- 连续活跃公司
- 持续风险与恢复
- 明日观察清单

这是第二版 agent 的完整跨日观察文本产物，适合归档与人工 review。

### 10.2 页面区块

建议在当日日报详情页新增：

- `跨日观察`

建议只展示短块式高价值信息：

- 最近几天主线
- 连续活跃公司
- 持续风险
- 最近恢复
- 明日关注
- Markdown 报告入口

页面区块不应塞长文，而应保持“扫一眼就能抓到趋势”的节奏。

## 11. 模块划分

建议新增四个模块。

### 11.1 `cross_day_input.py`

职责：

- 读取最近 N 天的：
  - `report.json`
  - `daily_intel_brief.json`
  - `health_snapshots/<date>.json`
- 转成统一的跨日输入

### 11.2 `cross_day_analysis.py`

职责：

- 识别：
  - 升温/降温主题
  - 连续活跃/波动公司
  - 持续风险/最近恢复
  - 下一日重点关注

这是第二版 agent 的核心逻辑层。

### 11.3 `cross_day_outputs.py`

职责：

- 输出：
  - `cross_day_intel_brief.json`
  - `cross-day-brief.md`
  - 页面区块可消费数据

### 11.4 `cross_day_pipeline.py`

职责：

- 编排整个 v2：
  - 读取输入
  - 执行分析
  - 写出结构化结果
  - 写出 Markdown 报告
  - 把页面区块数据挂入日报渲染输入

## 12. 接入方式

推荐接法：

1. `pipeline.py` 生成主日报
2. `agent_pipeline.py` 生成 v1 当日情报判断
3. `cross_day_pipeline.py` 生成 v2 跨日观察
4. `render.py` 检测到跨日产物时，渲染 `跨日观察` 区块

这样做的好处：

- 不破坏当前日报主链路
- v2 失败时，主日报和 v1 agent 仍然可用
- 跨日逻辑不会反向污染日报生成逻辑
- 后续若增加专题跟踪，也可以继续挂在这条增强链之后

## 13. 降级与兼容策略

### 13.1 主链路兼容

- `generate`
- `generate-today`
- `backfill`
- 自动化脚本

这些外部入口都不应因 v2 失败而中断主日报。

### 13.2 输入降级

- 缺少部分 `daily_intel_brief.json` 时，退回只读 `report.json`
- 缺少部分历史 `health_snapshot` 时，保留内容跨日分析，弱化运维跨日判断
- 历史窗口天数不足时，输出保守判断而不是强行写趋势

### 13.3 页面降级

- 若 v2 未成功生成，页面不渲染 `跨日观察`
- 仍保留现有 `情报判断` 与日报主体内容

## 14. 测试策略

本轮建议至少覆盖：

1. `cross_day_input`
- 正常读取最近 N 天输入
- 某些天缺少 `daily_intel_brief` 时仍可继续

2. `cross_day_analysis`
- 能识别升温主题
- 能识别降温主题
- 能识别连续活跃与波动公司
- 能识别持续风险与最近恢复

3. `cross_day_outputs`
- 正确生成 JSON
- 正确生成 Markdown
- 页面区块数据结构稳定

4. `cross_day_pipeline`
- 成功写出产物
- 失败时不破坏主日报

5. `render`
- 有跨日产物时出现 `跨日观察`
- 无跨日产物时页面仍正常

## 15. 风险与控制

### 风险 1：历史窗口过短导致趋势判断失真

控制：

- 对样本量不足的情况采用保守输出
- 不从 1 天或 2 天数据里写过重结论

### 风险 2：把单日波动误判成持续趋势

控制：

- 明确区分 `steady_companies` 与 `swing_companies`
- 对主题升温要求至少在多个日期内重复出现

### 风险 3：运维历史不完整导致分析偏差

控制：

- 引入 `health_snapshots/<date>.json`
- 缺失时降级，不假装有完整历史

### 风险 4：v2 输出过长，重新把页面拉回长文

控制：

- 页面区块只放短块摘要
- 长文本保留在 Markdown 报告中

## 16. 完成标准

这轮完成的判断标准是：

1. 能稳定读取最近 N 天日报与健康快照历史
2. 能生成 `cross_day_intel_brief.json`
3. 能生成 `cross-day-brief.md`
4. 当日日报详情页能展示 `跨日观察` 区块
5. v2 失败时主日报仍然正常生成
6. 测试覆盖关键跨日判断与降级路径

达到以上条件后，可以认为第二版跨日追踪 agent 的基础闭环已经建立。
