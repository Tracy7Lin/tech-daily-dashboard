# 科技日报最小情报分析 Agent 设计文档

## 1. 文档目的

这份文档用于定义 `tech-daily-dashboard` 的第一版情报分析 agent。

目标不是让系统立刻具备完整的自主研究、搜索或多工具编排能力，而是在现有日报主链路稳定、capability layer 已建立的基础上，新增一个可运行的最小 agent 闭环：

- 读取当日日报产物
- 读取运维状态产物
- 生成统一的结构化情报判断
- 同时输出 Markdown 报告和页面分析区块

## 2. 背景与动机

当前系统已经完成两层基础建设：

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

当前缺口不是“能不能再生成日报”，而是：

- 缺少一个站在日报之上的“情报判断层”
- 缺少一个把内容状态和运维状态统一解释的最小 agent
- 缺少一个可归档的运营判断结果，供页面、自动化和未来 agent 升级复用

因此，第一版 agent 的目标是：  
**消费现有日报与 health snapshot，输出一份可直接阅读与复用的情报运营判断。**

## 3. 设计目标

本轮 agent 设计目标如下：

1. 基于现有日报与运维产物，生成一份统一的 `daily_intel_brief`
2. 同时产出：
- Markdown 报告
- 页面中的 agent 分析区块
3. 保持日报主链路稳定，不把抓取、分类、渲染重新耦合进 agent
4. 保持失败可降级：agent 失败时日报仍然可以生成
5. 为未来更强的科技情报分析 agent 预留升级空间

## 4. 非目标

本轮明确不做以下事项：

- 不实现自主互联网搜索
- 不实现新信源发现
- 不实现长期记忆
- 不实现多工具编排
- 不实现自动修复抓取器
- 不替代现有抓取与日报主流程

第一版 agent 只是：

**一个消费现有日报产物并输出高价值判断的最小分析 agent。**

## 5. 推荐方案

采用 `双产物同源` 方案。

即：

- agent 先产出统一的结构化分析结果
- 再由该结果同时渲染：
  - Markdown 报告
  - 页面分析区块

不采用：

- 只做 Markdown、页面仅放链接的方案
- 只做页面区块、报告附带的方案

原因：

- `双产物同源` 更符合当前 capability 架构
- 可以避免两套分析文案独立演化
- 后续前端、自动化、未来 agent 升级都可以消费同一份结果

## 6. Agent 职责边界

第一版 agent 只做四件事：

1. 读取当日日报 `report.json`
2. 读取 `health_snapshot.json`
3. 生成“今日情报运营判断”
4. 输出两种消费形式：
- `agent-brief.md`
- 页面中的分析区块

它应回答的问题包括：

- 今天内容层面最值得注意的主题是什么
- 今天运维层面最值得注意的问题是什么
- 哪些公司或主题值得继续跟踪
- 明天最应该优先关注什么

## 7. 输入设计

第一版 agent 只消费两份现成产物。

### 7.1 日报输入

路径：

- `build/site/<date>/report.json`

用途：

- 读取当天 headline、主题聚合、公司动态、公司覆盖度等信息

### 7.2 运维输入

路径：

- `build/data/health_snapshot.json`

用途：

- 读取当前异常、高优先级问题、最近恢复问题、运维摘要等信息

### 7.3 输入原则

- 不直接读取抓取器中间状态
- 不直接重新抓 HTML / RSS
- 不让 agent 重新构造事实来源

第一版 agent 只站在“已生成的日报结果”之上工作。

## 8. 统一分析结果设计

建议新增统一对象：

- `daily_intel_brief.json`

路径建议：

- `build/site/<date>/daily_intel_brief.json`

结构至少包含：

- `report_date`
- `editorial_signal`
- `ops_signal`
- `top_content_themes`
- `watchlist`
- `source_risks`
- `recoveries`
- `tomorrow_focus`
- `mode_used`

### 字段说明

#### `editorial_signal`

今天内容层面最值得注意的总判断。

#### `ops_signal`

今天运行与信源层面最值得注意的总判断。

#### `top_content_themes`

1-3 个最值得继续关注的内容主题。

#### `watchlist`

值得明天继续盯的公司、主题或问题。

#### `source_risks`

当前尚未恢复的信源问题。

#### `recoveries`

最近恢复的公司与信源。

#### `tomorrow_focus`

明天优先应该关注什么。

#### `mode_used`

标记这份分析是 `rule / llm / hybrid`。

## 9. 输出设计

### 9.1 Markdown 报告

路径建议：

- `build/site/<date>/agent-brief.md`

结构建议：

- 标题
- 今日核心判断
- 内容主线
- 运维状态
- 需要继续跟踪
- 明日关注点

这是第一版 agent 的完整文本产物，也是最适合后续独立归档和人工 review 的输出。

### 9.2 页面分析区块

建议在当日日报详情页增加：

- `情报判断`

或

- `Agent Brief`

建议只展示高价值短块：

- 今日核心判断
- 运维提示
- 明日关注点
- Markdown 报告入口

页面区块不应塞入整篇长文，而应以快速提取为优先。

## 10. 模块划分

建议新增 4 个模块。

### 10.1 `agent_input.py`

职责：

- 读取 `report.json`
- 读取 `health_snapshot.json`
- 转成内部标准输入

### 10.2 `agent_analysis.py`

职责：

- 基于日报内容与运维状态生成统一分析结果

这是第一版 agent 的核心逻辑层。

### 10.3 `agent_outputs.py`

职责：

- 将统一分析结果输出为：
  - `daily_intel_brief.json`
  - `agent-brief.md`
  - 页面可消费的数据块

### 10.4 `agent_pipeline.py`

职责：

- 编排整个 agent 流程：
  - 读取输入
  - 生成分析
  - 写出 JSON
  - 写出 Markdown
  - 将结果挂到页面渲染输入

## 11. 接入方式

推荐接入点：

- `pipeline.py` 先正常生成日报
- 再调用 `agent_pipeline`
- `render.py` 如果检测到 agent brief 数据，就渲染分析区块
- 如果 agent 结果不存在，则保持现有页面行为

这种接入方式的优点是：

- 风险最小
- 主日报链路不需要为 agent 重写
- agent 可作为上层增强，而不是基础依赖

## 12. 降级策略

agent 失败时必须满足：

- 日报仍然正常生成
- 页面仍然可渲染
- agent 区块允许缺席
- Markdown 报告允许缺失

也就是说：

- `agent_pipeline` 是增强层，不是阻断层

## 13. 模式策略

第一版 agent 建议复用已有 `rule / llm / hybrid` 思路。

推荐默认：

- `hybrid`

原则：

- 事实来自 `report.json` 与 `health_snapshot.json`
- agent 只负责整合与判断
- 即使使用 LLM，也不允许 agent 自行扩展未提供事实

## 14. 测试策略

本轮至少补以下测试：

- `agent_input` 的输入读取测试
- `agent_analysis` 的结构化输出测试
- `agent_outputs` 的 JSON / Markdown 输出测试
- `agent_pipeline` 的编排测试
- `render.py` 的 agent 区块回归测试
- 降级路径测试：agent 失败时日报仍正常生成

## 15. 风险与控制

### 风险 1：agent 与日报主流程耦合过深

控制方式：

- agent 作为后置增强步骤
- 主日报先成功，再跑 agent

### 风险 2：页面分析区块与 Markdown 分析结果不一致

控制方式：

- 坚持双产物同源
- 页面区块只消费统一分析对象

### 风险 3：agent 过早承担太多职责

控制方式：

- 第一版只消费现有产物
- 不做搜索、不做抓取、不做多工具规划

## 16. 完成标准

本轮可视为完成，当满足以下条件：

1. `daily_intel_brief.json` 能被稳定生成
2. `agent-brief.md` 能被稳定生成
3. 页面可显示 agent 分析区块
4. agent 失败时主日报仍可正常生成
5. 全量测试通过
6. README 与路线图后续可同步反映这条新能力线

## 17. 后续衔接

第一版最小 agent 完成后，后续才适合继续考虑：

- 引入跨日跟踪
- 引入专题持续观察
- 引入更主动的运维诊断建议
- 引入更强的科技情报研究能力

但这些都应建立在：

**最小情报分析 agent 先稳定可用**

的前提之上。
