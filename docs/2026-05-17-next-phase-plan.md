# 科技日报项目下一阶段计划

## 1. 文档目的

这份文档用于承接当前已经完成的实现计划，定义项目进入下一阶段后的主线目标、优先级和批次安排。

当前阶段的核心变化是：

- 日报主链路已经稳定
- 运维闭环已经可持续运行
- v1/v2/v3/v4 agent 增强链已经打通
- 网页问答已经从静态 response bank 升级为真实运行时问答
- chat 已经具备基础会话级上下文记忆

因此，下一阶段不再以“补主链路缺口”为目标，而是以：

`把系统从可用 agent 产品雏形，推进到更像研究助理的平台`

为目标。

## 2. 当前阶段结论

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
- dossier-aware 问答
- evidence-backed answers
- session-memory follow-up

## 3. 下一阶段目标

下一阶段的主线目标定为：

`Research Assistant v2`

也就是把现在的日报问答器，继续推进成一个：

- 更会解释
- 更会引用依据
- 更能连续追问
- 更像研究助理

的系统。

## 4. 下一阶段优先级

下一阶段建议优先级如下：

1. `Research Assistant v2`
2. `Theme Dossier 深化`
3. `内容质量第二轮提升`
4. `前端阅读与问答体验精修`
5. `信源可靠性剩余硬点`
6. `兄弟日报与外部扩展`

## 5. 主线批次设计

### 批次 A：Research Assistant v2

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

验收标准：

- 页面和 CLI 都能稳定处理 2-3 轮连续追问
- 证据展示更清晰
- 回答来源边界更明确

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

### 批次 C：内容质量第二轮提升

目标：

- 在 agent 框架稳定后，再回头提升日报文本质量

建议任务：

- 统一 `summary / comparison / trend` 文风
- 压缩 `其他重要动态`
- 继续优化 LLM 提示词和后处理

验收标准：

- 同日不同区块的文风更一致
- 低信息密度主题进一步减少

### 批次 D：前端体验精修

目标：

- 提升长期阅读体验和问答体验

建议任务：

- 对话抽屉内的“结论 / 依据 / 追问建议”视觉层次优化
- 移动端 chat 和 modal 微调
- dossier / theme tracking / cross-day 区块的阅读层次精修

验收标准：

- 页面阅读更轻松
- chat 交互更自然

### 批次 E：信源可靠性剩余硬点

目标：

- 处理剩余但非主线的源问题

建议任务：

- 继续观察 `Tesla / Xiaomi`
- 保持占位策略
- 仅在出现低复杂度可行方案时再接入

验收标准：

- 不因这两家问题破坏主系统节奏
- 前端状态持续可解释

## 6. 暂不优先项

以下方向明确不作为最近一批主线：

- `GitHub 今日 Highlight 日报`
- 多专题 dossier 系统
- 长期数据库记忆
- 外部搜索型 agent
- 为单一公司引入高复杂度抓取器

## 7. 推荐立即执行项

如果按当前状态继续推进，我建议下一步直接进入：

`批次 A：Research Assistant v2`

理由：

- 它能最大化放大已经完成的 dossier、tracking、cross-day、runtime chat 能力
- 它比再做一层新 agent 更能提升实际使用体验
- 它仍然保持在系统框架深化，而不是偏外围修补

## 8. 执行原则

下一阶段继续保持：

- 每个批次必须有明确目标和验收标准
- 先补测试，再改实现
- 保持高内聚、低耦合
- 每个可识别里程碑都要提交并推送到远程
- 不把实验性能力直接耦入日报主链
