# Theme Dossier Agent 实现计划

## 目标

在现有 `专题跟踪 agent` 之上，新增一条 `Theme Dossier Agent` 增强链，用于把当天主专题沉淀成结构化 dossier，并同时输出：

- `theme_dossier.json`
- `theme-dossier.md`
- 日报详情页中的轻量 `主题档案` 区块

## 实施原则

- 先补测试，再改实现
- 保持高内聚、低耦合
- 不改抓取层，不引入外部搜索
- dossier 失败时不影响主日报、跨日观察和专题跟踪
- 规则层负责事实选择，LLM 只用于必要表达层

## 模块拆分

新增：

- `src/tech_daily/theme_dossier_input.py`
- `src/tech_daily/theme_dossier_analysis.py`
- `src/tech_daily/theme_dossier_outputs.py`
- `src/tech_daily/theme_dossier_pipeline.py`

需要接入：

- `src/tech_daily/models.py`
- `src/tech_daily/pipeline.py`
- `src/tech_daily/render.py`
- `templates/daily.html`

## 分阶段执行

### 阶段 A：数据结构与输入层

任务：

- 增加 `ThemeDossierBrief`
- 增加 dossier 输入 dataclass
- 读取最近 N 天：
  - `report.json`
  - `daily_intel_brief.json`
  - `cross_day_intel_brief.json`
  - `theme_tracking_brief.json`

完成标准：

- Python 层能稳定拿到 dossier 所需输入

### 阶段 B：分析层

任务：

- 基于现有主专题与最近几天条目，生成：
  - `theme_definition`
  - `theme_state`
  - `theme_summary`
  - `participating_companies`
  - `company_positions`
  - `timeline_events`
  - `tracking_decision`
  - `next_day_focus`
- 规则层先完成：
  - 状态机初判
  - 代表事件筛选
  - 参与公司选择

完成标准：

- 分析层能输出结构化 `ThemeDossierBrief`

### 阶段 C：输出层

任务：

- 输出 `theme_dossier.json`
- 输出 `theme-dossier.md`
- 生成页面可消费的 dossier block

完成标准：

- dossier 双产物可落盘

### 阶段 D：主链路接入

任务：

- 在 `pipeline.py` 中接入 `theme_dossier_pipeline`
- 保持 dossier 失败时主日报可继续生成
- 在 `render.py` / `daily.html` 中新增轻量 `主题档案` 区块

完成标准：

- 生成当日日报时可同时产出 dossier 和页面入口

### 阶段 E：验证与文档同步

任务：

- 补单元测试：
  - input
  - analysis
  - outputs
  - pipeline
  - render
- 跑全量测试
- 真实生成一次当日日报
- 视情况补 README / roadmap 引用

完成标准：

- 全量测试通过
- 真实产物存在且页面区块可见

## 状态机最小实现策略

第一版先采用规则型状态机：

- `emerging`
  - 近几天只出现 1 次，但已形成主专题
- `active`
  - 近几天持续出现，且参与公司 >= 2
- `fragmenting`
  - 近几天持续出现，参与公司 >= 2，且切入点差异明显
- `cooling`
  - 只在较早日期出现，最近一天未继续升温

后续如果要增强，再考虑把状态机解释层交给 LLM 辅助润色。

## 时间线选择策略

第一版只保留 3-6 条条目，优先级如下：

1. 最近一天的主专题代表条目
2. 第一次出现该主题的条目
3. 来自不同公司的差异化条目
4. 能体现主题转向或升温的条目

## 降级策略

- dossier 分析失败时：
  - `theme_tracking_brief` 仍然保留
  - 页面不渲染 `主题档案`
  - 其余 agent 区块不受影响

## 验收口径

- `theme_dossier.json` 存在
- `theme-dossier.md` 存在
- 页面中出现 `主题档案` 区块
- dossier 中有：
  - 主专题
  - 当前阶段
  - 参与公司
  - 3-6 条关键时间线
- 全量测试通过
