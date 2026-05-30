# 科技日报项目下一阶段计划

## 1. 文档目的

这份文档用于承接当前已经完成的实现计划，定义项目进入下一阶段后的主线目标、优先级和批次安排。

当前阶段的核心变化是：

- 日报主链路已经稳定
- 运维闭环已经可持续运行
- v1/v2/v3/v4 agent 增强链已经打通
- 网页问答已经从静态 response bank 升级为真实运行时问答
- `Runtime-First Research Assistant` 基线已经落地
- `Adaptive Research Assistant` 已具备“日报依据 + 模型补充 + 通用知识回答”的基础链路
- chat 已经具备基础会话级上下文记忆
- 项目内 `research-agent-question-orchestration` skill 已落地
- `chat_agent_*` 已降级为 preview / fallback compatibility layer，不再作为并行主链维护

因此，下一阶段不再以“补主链路缺口”为目标，而是以：

`把系统从可用 agent 产品雏形，推进到更像研究助理的平台`

为目标。

这条主线采用的总体哲学是：

`AGENT = LLM + SKILLS + TOOLS + RAG + 边界控制`

其中：

- `LLM` 是问题理解、推理与表达的核心
- `SKILLS` 负责约束研究流程和回答规范
- `TOOLS` 负责执行动作，后续可扩展到联网搜索与更多诊断能力
- `RAG` 负责从日报 JSON 知识层里提供 grounding
- `边界控制` 负责区分日报依据、模型补充判断与通用知识回答

## 2. 当前阶段基线

以下能力已经可以视为当前基线：

### 2.1 主日报能力

- 官方信源抓取、过滤、分类、摘要、主题聚合、静态渲染
- 规则 / LLM / hybrid 表达模式
- 首页、详情页、历史归档

### 2.2 运维与自动化能力

- `generate-today`
- `health-check`
- `dry-run`
- 本地定时任务脚本
- 运行日志
- `health_snapshot` 与历史快照

### 2.3 Agent 增强链

- v1：`daily_intel_brief`
- v2：`cross_day_intel_brief`
- v3：`theme_tracking_brief`
- v4：`theme_dossier`

### 2.4 Chat 能力

- CLI `chat`
- 页面右下角运行时 chat
- `/api/chat`
- `/api/health`
- dossier-aware 问答
- evidence-backed answers
- session-memory follow-up
- runtime-first JSON knowledge answering
- 项目内 research orchestration skill

## 3. 为什么进入下一阶段

到当前版本为止，`Research Assistant v2` 的主线已经基本完成，具体包括：

- `runtime-first research assistant`
- `adaptive research assistant`
- `session-memory` 多轮追问
- `LLM-first + daily-intelligence RAG` 回答链
- `local tools` 接口与首批本地工具执行
- `research-agent-question-orchestration` 项目内 skill
- `chat_agent_*` 已降级为 preview / fallback compatibility layer

因此，下一阶段不再以“把 chat 做得更像研究助理”为主目标，而是进入：

- 提高研究助理自由提问质量
- 继续增强高质量官方信源广度
- 为未来 tools 扩展留出更稳的接入边界

## 4. 下一阶段目标

下一阶段的主线目标定为：

`Research Assistant v3`

也就是把当前已经成形的研究助理，继续推进成一个：

- 更自由提问
- 更自然选择上下文
- 更清楚区分日报依据与通用知识补充
- 更容易接入未来 tools

的系统。

## 5. 当前状态总览

基于当前仓库状态，下一阶段相关主线应按下面的状态理解：

- `Research Assistant v3`：进行中，仍是当前第一主线
- `信源广度与信息量增强`：进行中，当前第二主线
- `Theme Dossier 深化`：部分完成，待继续深化
- `项目内 research orchestration skill 对齐`：已完成第一阶段，后续并入 `Research Assistant v3`
- `内容质量第二轮提升`：未启动
- `前端阅读与问答体验精修`：暂停，待重新定义首页与整站视觉方向
- `信源可靠性剩余硬点`：低优先级待观察
- `兄弟日报与外部扩展`：中期扩展，未启动

## 6. 下一阶段优先级

下一阶段建议优先级如下：

1. `Research Assistant v3`
2. `信源广度与信息量增强`
3. `Theme Dossier 深化`
4. `内容质量第二轮提升`
5. `前端阅读与问答体验精修（待重设）`
7. `信源可靠性剩余硬点`
8. `兄弟日报与外部扩展`

## 7. 主线批次设计

### 批次 A：Research Assistant v2（已完成）

目标：

- 把 chat 从“可连续追问”提升到“更像研究助理”

建议任务：

- 为回答增加更细的证据归因
  - 区分来源于：
    - `report.json`
    - `cross_day_intel_brief.json`
    - `theme_tracking_brief.json`
    - `theme_dossier.json`
    - `health_snapshot.json`
- 优化 follow-up 解析
  - 支持更多自然追问：
    - `那 OpenAI 呢`
    - `为什么`
    - `继续`
    - `还有别的吗`
- 让页面问答在 UI 上更清楚地区分：
  - 结论
  - 回答依据
  - 下一步建议问题
- 补一轮 chat 相关回归测试矩阵
  - 歧义追问
  - dossier 追问
  - 公司追问
  - 时间线追问

当前状态：

- 页面和 CLI 已能稳定处理 2-3 轮连续追问
- 证据展示已经结构化
- 回答来源边界已经明确到 dossier / cross-day / report / health snapshot
- runtime-first research assistant 已经取代旧的静态优先问答路径
- 项目内 `research-agent-question-orchestration` skill 已作为统一流程规范落库
- 当前这条批次可以视为完成，后续增强已转移到 `Research Assistant v3`

### 批次 A2：Research Assistant v3

目标：

- 让研究助理更接近 `LLM + SKILLS + TOOLS + RAG + 边界控制`

建议任务：

- 继续弱化硬分类感，让问题理解更粗粒度、更 LLM-first
- 继续增强自由提问场景下的上下文选择
- 在不依赖日报时，允许更自然的通用知识回答，但保留边界提示
- 为未来 `web_search` 等工具接入保留清晰的工具编排边界

验收标准：

- 对开放式问题不再显得像固定问答器
- 对日报相关问题仍保持 grounding
- 对通用知识问题不错误挂载日报证据
- tools / rag / llm 的边界在实现和 UI 上都更清楚

当前状态：

- 进行中
- `runtime-first`、`adaptive`、`LLM-first + RAG` 已经落地
- 当前剩余重点是进一步减少兼容层心智、增强自由提问与后续 tool orchestration

### 批次 B：Theme Dossier 深化

目标：

- 把当前 dossier 从“结构化档案”推进到“研究型档案”

建议任务：

- 优化 `theme_definition`
- 优化 `company_positions`
- 优化 `timeline_events[].why_it_matters`
- 增强 `tracking_decision`
- 让 dossier 与 chat 的联动更直接
  - chat 可以更自然解释：
    - 为什么是 `emerging / active / fragmenting / cooling`
    - 某家公司在专题中的角色

验收标准：

- dossier Markdown 更像研究简报
- chat 对 dossier 的消费更自然

当前状态：

- 第一阶段已完成
- 第二阶段未完成，仍需继续推进 `theme_definition / company_positions / why_it_matters / tracking_decision`

### 批次 C：信源广度与信息量增强

目标：

- 在维持“官方信源优先”的前提下，提高信息量与主题形成能力

建议任务：

- 为高价值公司继续补第二、第三官方入口
- 提高单日有效内容密度，而不是只追求抓取成功率
- 为低产出但稳定的公司增加更丰富的官方栏目覆盖

验收标准：

- 连续多天日报不再因为低产出显得过空
- 更容易形成 2-3 个值得阅读的主线主题

当前状态：

- 进行中
- 已经开始为高价值公司补第二官方入口
- 但“单日信息密度偏低”的问题还没有真正解决

### 批次 D：内容质量第二轮提升

目标：

- 在 agent 框架稳定后，再回头提升日报文本质量

建议任务：

- 统一 `summary / comparison / trend` 文风
- 压缩 `其他重要动态`
- 继续优化 LLM 提示词和后处理

验收标准：

- 同日不同区块的文风更一致
- 低信息密度主题进一步减少

### 批次 E：前端体验精修

目标：

- 提升长期阅读体验和问答体验

建议任务：

- 对话抽屉内的“结论 / 依据 / 追问建议”视觉层次优化
- 移动端 chat 和 modal 微调
- dossier / theme tracking / cross-day 区块的阅读层次精修

验收标准：

- 页面阅读更轻松
- chat 交互更自然

当前状态：

- 暂停
- 当前首页与整站视觉方向仍未稳定，不适合继续按旧的前端计划线推进
- 后续需要先重新定义首页与杂志化风格，再进入新的前端实现计划

### 批次 F：信源可靠性剩余硬点

目标：

- 处理剩余但非主线的源问题

建议任务：

- 继续观察 `Tesla / Xiaomi`
- 保持占位策略
- 仅在出现低复杂度可行方案时再接入

验收标准：

- 不因这两家问题破坏主系统节奏
- 前端状态持续可解释

## 8. 暂不优先项

以下方向明确不作为最近一批主线：

- `GitHub 今日 Highlight 日报`
- 多专题 dossier 系统
- 长期数据库记忆
- 外部搜索型 agent
- 为单一公司引入高复杂度抓取器

## 9. 推荐立即执行项

如果按当前状态继续推进，我建议下一步直接进入：

`批次 A2：Research Assistant v3`

理由：

- 它能继续巩固 `LLM-first` 设计哲学
- 它比继续堆规则更能提升研究助理真实能力
- 它和未来 tools / web search 接入最直接相关
- 同时建议并行推进 `批次 C：信源广度与信息量增强`

## 10. 执行原则

下一阶段继续保持：

- 每个批次必须有明确目标和验收标准
- 先补测试，再改实现
- 保持高内聚、低耦合
- 每个可识别里程碑都要提交并推送到远程
- 不把实验性能力直接耦入日报主链
- 研究助理优先遵循 `LLM + SKILLS + TOOLS + RAG + 边界控制`
- 不把日报知识层误当成唯一答案来源，而应把它作为 grounding / evidence layer
