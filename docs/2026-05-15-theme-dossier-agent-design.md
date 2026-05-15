# Theme Dossier Agent 设计文档

## 1. 文档目的

这份文档用于定义 `Theme Dossier Agent` 的第一版设计。

它位于现有能力链的下一阶段：

- v1：当日情报判断
- v2：跨日观察
- v3：专题跟踪
- v4：主题 dossier

目标不是再增加一个“更长的摘要区块”，而是把当前最值得跟踪的主专题进一步沉淀成一个可持续复用的小型专题档案。

## 2. 为什么需要 Theme Dossier

当前系统已经可以做到：

- 当天知道什么最重要
- 最近几天知道哪些主题在升温
- 每天选出 1 个值得盯的主专题

但当前还缺少一层更像“研究档案”的结构：

- 主题定义是什么
- 这个主题处于什么阶段
- 最近几天最关键的代表事件有哪些
- 哪些公司在持续参与，它们的切入点是否已经稳定
- 明天继续跟踪时，最应该看什么变化

也就是说，当前的 `theme_tracking_brief` 更像“专题跟踪摘要”，还不是“专题档案”。

## 3. 目标

Theme Dossier Agent 第一版要实现：

- 为当天的主专题生成一份结构化 dossier
- 用有限条目的时间线串起最近几天的代表事件
- 给主专题标记一个明确状态
- 沉淀“主题定义 + 参与公司 + 公司切入点 + 时间线 + 下一步关注”
- 输出：
  - `theme_dossier.json`
  - `theme-dossier.md`
  - 日报详情页中的轻量 dossier 入口

## 4. 非目标

第一版不做：

- 多专题 dossier 系统
- 长期无限累积的知识库
- 外部搜索或补充资料抓取
- 运维状态并入 dossier 主体
- 自动修复信源
- 类 Wiki 的可编辑专题空间

这仍然是一个建立在现有日报产物之上的最小专题研究增强层。

## 5. 输入边界

Theme Dossier Agent 只读取现有产物，不直接触碰抓取层。

建议输入：

1. 最近 N 天 `report.json`
2. 最近 N 天 `daily_intel_brief.json`
3. 最近 N 天 `cross_day_intel_brief.json`
4. 最近 N 天 `theme_tracking_brief.json`

其中：

- 主题候选与代表条目主要来自 `report.json`
- 每日主线和跨日趋势主要来自 `daily_intel_brief` / `cross_day_intel_brief`
- 当天主专题与参与公司主要来自 `theme_tracking_brief`

## 6. 核心设计

### 6.1 统一结构化输出

建议新增：

- `theme_dossier.json`

第一版字段建议至少包括：

- `date_range`
- `primary_theme`
- `theme_definition`
- `theme_state`
- `theme_summary`
- `participating_companies`
- `company_positions`
- `timeline_events`
- `tracking_decision`
- `next_day_focus`
- `mode_used`

### 6.2 字段解释

- `date_range`
  - 本次 dossier 覆盖的时间范围

- `primary_theme`
  - 当前主专题名称

- `theme_definition`
  - 这个主题到底在讨论什么
  - 用一段稳定、可复用的定义表达，不依赖单日 headline

- `theme_state`
  - 主题当前阶段
  - 第一版只允许：
    - `emerging`
    - `active`
    - `fragmenting`
    - `cooling`

- `theme_summary`
  - 为什么这个主题现在值得看

- `participating_companies`
  - 持续参与该主题的公司列表

- `company_positions`
  - 每家公司的切入点
  - 强调：
    - 产品化
    - 平台能力
    - 安全治理
    - 客户落地
    - 终端入口
  - 但不强制暴露内部标签名

- `timeline_events`
  - 最近几天中 3-6 条最关键代表事件
  - 每条至少包含：
    - `date`
    - `company`
    - `title`
    - `why_it_matters`

- `tracking_decision`
  - 是否继续跟踪这个主题
  - 不是布尔值，而是一段简短判断

- `next_day_focus`
  - 明天继续盯这个主题时最应该关注什么

- `mode_used`
  - `rule / llm / hybrid`

## 7. 状态机设计

第一版主题状态机建议如下：

- `emerging`
  - 最近刚出现，事件还不多，但已经值得关注

- `active`
  - 最近几天持续出现，且有多家公司参与，主题主线最清晰

- `fragmenting`
  - 仍有热度，但参与公司的切入点开始明显分化，主题不再单一

- `cooling`
  - 最近几天热度和代表事件明显回落，不再是主线

状态机的职责是帮助后续 agent 直接回答：

- 这个主题是刚冒头，还是已经形成主线
- 它还值得继续跟踪，还是正在退潮

## 8. 时间线设计

第一版 dossier 中的时间线不应试图收录所有事件。

建议原则：

- 只保留 3-6 条代表事件
- 优先保留：
  - 第一次明显出现该主题的事件
  - 让主题升温的事件
  - 体现公司差异化切入点的事件
  - 让主题转向或降温的事件

时间线的价值是：

- 让 dossier 看起来像“研究视角”
- 而不是只把最近几天条目重新列一遍

## 9. 规则层与 LLM 层边界

这条线仍然保持和前面几版 agent 相同的原则：

- 规则层负责：
  - 主专题识别
  - 参与公司识别
  - 候选事件筛选
  - 状态机初始判断

- LLM 层只用于必要的分析表达：
  - `theme_definition`
  - `theme_summary`
  - `company_positions`
  - `tracking_decision`
  - `next_day_focus`
  - `timeline_events[].why_it_matters`

LLM 不应：

- 发明未在输入里出现的公司或事件
- 引入站外新事实
- 自主重写主题状态机

## 10. 输出形态

### 10.1 JSON

输出：

- `build/site/<date>/theme_dossier.json`

它是后续页面、CLI、对话 agent、未来更强研究 agent 的统一结构化输入。

### 10.2 Markdown

输出：

- `build/site/<date>/theme-dossier.md`

建议结构：

- 标题
- 主专题定义
- 当前阶段
- 为什么值得看
- 参与公司与切入点
- 关键时间线
- 是否继续跟踪
- 明日关注点

### 10.3 页面轻接入

当日日报详情页只增加一个轻量区块，例如：

- `主题档案`

页面里只放：

- 主专题
- 当前阶段
- 一句话 dossier 判断
- 查看完整 dossier Markdown

不在详情页里直接展开整条时间线，避免把日报页面重新做重。

## 11. 模块划分

建议新增：

- `theme_dossier_input.py`
- `theme_dossier_analysis.py`
- `theme_dossier_outputs.py`
- `theme_dossier_pipeline.py`

职责：

- `theme_dossier_input`
  - 读取最近 N 天日报与已有 agent 产物

- `theme_dossier_analysis`
  - 识别主专题
  - 计算主题状态
  - 选择代表事件
  - 组织公司切入点

- `theme_dossier_outputs`
  - 写出 JSON 与 Markdown
  - 产出页面区块可消费数据

- `theme_dossier_pipeline`
  - 编排整个 dossier 链

## 12. 接入方式

建议接入顺序：

1. `pipeline.py` 生成主日报
2. `agent_pipeline.py` 生成 v1 当日情报判断
3. `cross_day_pipeline.py` 生成 v2 跨日观察
4. `theme_tracking_pipeline.py` 生成 v3 专题跟踪
5. `theme_dossier_pipeline.py` 生成 v4 主题 dossier
6. `render.py` 如果检测到 dossier 产物，就渲染 `主题档案` 轻入口

这样仍然保持：

- 主链稳定
- 增强层逐层失败可降级
- dossier 不反向污染日报主链

## 13. 降级策略

- dossier 生成失败时，主日报仍然正常生成
- v3 `专题跟踪` 不受影响
- 页面 `主题档案` 区块可缺席
- `theme_dossier.json` 缺失时，对话 agent 与后续能力不应崩溃

## 14. 验收标准

Theme Dossier Agent 第一版完成时，应满足：

- 能为当天主专题生成结构化 dossier
- 能输出 `theme_dossier.json`
- 能输出 `theme-dossier.md`
- 页面中有轻量 dossier 入口
- dossier 中有明确主题状态
- dossier 中有 3-6 条代表事件时间线
- LLM 只在必要表达层使用
- 全量测试与真实生成通过

## 15. 推荐顺序

建议下一步顺序：

1. 写实现计划
2. 先补测试
3. 先落 JSON / Markdown
4. 最后接页面轻入口

这样最稳，也最容易验证 dossier 本身是否有真实价值。
