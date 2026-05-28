# 科技日报项目改进路线图

## 1. 文档目的

这份文档用于收束当前 `tech-daily-dashboard` 项目的后续优化方向，避免后续工作继续以零散问题驱动推进。

目标不是一次性规划所有未来能力，而是给出一份可执行、可验收、可迭代的改进路线图，供后续开发按批次落地。

## 2. 当前项目状态

截至当前版本，项目已经具备以下能力：

- 稳定的日报主链路：抓取、过滤、分类、摘要、主题聚合、静态渲染
- LLM-first 研究助理主链：`research_agent_*`
- 混合表达层：规则 + LLM，且具备 fallback
- 本地自动化：`generate-today`、PowerShell 脚本、Windows 定时任务注册
- 基础运维可观测性：`health-check`、`dry-run`、源级配置诊断、最近一次运行诊断、历史运行诊断、高优先级问题摘要、最近恢复问题摘要、结构化 `health_snapshot`
- 杂志化前端信息架构：主刊首页、每日日报页、专题页、档案页、归档页
- 桌面端 `左导航 / 中正文 / 右 Research Assistant` 布局，移动端问答抽屉 fallback
- 对持续不可抓取或低产出的公司提供占位说明，而不是静默空白
- 当日日报、跨日观察、专题跟踪、主题档案、运行时问答五层 agent 增强链已经打通

当前项目已经超出“原型脚本”的阶段，属于：

`可持续迭代的个人情报日报产品雏形`

当前 agent 相关能力采用的总体哲学是：

`AGENT = LLM + SKILLS + TOOLS + RAG + 边界控制`

其中日报知识层承担的是 grounding / evidence layer 的角色，而不是唯一答案来源。

当前代码层也已经明确：

- `research_agent_*` 是运行时研究助理主链
- `chat_agent_*` 仅保留 preview / fallback compatibility 职责

## 3. 已完成的改进线

以下工作已经不再是待办，而是当前基线能力：

### 3.1 自动化与运维基线

- `generate-today`
- `health-check`
- `dry-run`
- `run_daily_report.ps1`
- Windows 定时任务注册/删除脚本
- 运行日志写入 `build/logs`
- 生成后自动追加一次健康检查

### 3.2 内容表达与 agent 基线

- `rule / llm / hybrid` 三种模式
- DeepSeek 兼容接入
- 单条摘要、首页判断、主题对比的 LLM 化表达层
- LLM 输出后处理与 fallback
- agent-ready capability layer 基线：
  - `brief_generation`
  - `topic_comparison`
  - `daily_editorial`
  - `ops_status_analysis`
- v1：当日情报判断
  - `daily_intel_brief.json`
  - `agent-brief.md`
- v2：跨日观察
  - `cross_day_intel_brief.json`
  - `cross-day-brief.md`
- v3：专题跟踪
  - `theme_tracking_brief.json`
  - `theme-tracking-brief.md`
- v4：主题档案
  - `theme_dossier.json`
  - `theme-dossier.md`
- v5：运行时研究助理
  - runtime-first research assistant
  - adaptive research assistant
  - session-memory follow-up
  - LLM-first + daily-intelligence RAG

### 3.3 前端基线

- 杂志化页面结构与统一导航
- 主刊首页 / 每日日报 / 专题页 / 档案页 / 归档页
- 摘要卡片 + modal 展开
- 公司空状态与信源不稳定状态占位
- Research Assistant 侧栏 + 移动端抽屉 fallback
- 页面转场、栏目动效、统一杂志配色体系
- 运行时网页 chat：
  - `/api/chat`
  - `/api/chat-stream`
  - `/api/health`
  - 逐句流式输出
  - 静态 preview response bank fallback

### 3.4 源级诊断基线

- 最近一次运行问题
- 最近几天重复问题
- 高优先级问题摘要
- 已恢复问题不再继续出现在高优先级列表
- 区分“信源稳定但当日无动态”和“信源暂未稳定”

### 3.5 项目内 skill 与工具基线

- 项目内 `research-agent-question-orchestration` skill
- `question understanding`
- `answer synthesis`
- `evidence and follow-ups`
- `rag and boundaries`
- 首批本地 tool 接口与执行：
  - `local_health_check`
  - `report_generation`

## 4. 当前真正未完成的主线

当前主线不再是“把日报做成一个会回答的页面”，而是：

- 继续提高 research assistant 的自由提问质量
- 继续增强高质量官方信源广度与内容密度
- 继续把 `LLM + SKILLS + TOOLS + RAG + 边界控制` 收敛成稳定架构

换句话说，后续工作的重点已经从“补链路”切到：

`让系统从可用 agent 产品雏形，推进到更像研究助理的平台`

## 5. 当前仍值得推进的改进方向

### 5.1 Research Assistant v3

目标：

- 把当前 research assistant 从“已可用”推进到“更像真正研究助理”

当前问题：

- 仍残留部分兼容层与旧分类心智
- 自由提问能力还有提升空间
- tools 已有接口，但编排能力仍偏初级
- 一般知识回答、日报 grounding、工具结果三者的融合还可以更自然

说明：

这是当前最重要的主线，应当排在最前。

### 5.2 信源广度与信息量增强

目标：

- 在维持官方信源优先的前提下，提高日报的内容密度与主题形成能力

当前问题：

- 当前部分公司虽然“稳定”，但单日有效内容偏少
- 主刊和日报在低产出日期容易显得过空
- 现有信源更偏单入口，覆盖广度不足

说明：

这条线和“信源可靠性”不同。它不是先修报错，而是增强高质量内容供给，应当作为当前的第二主线。

### 5.3 主题研究深化

目标：

- 把现有 `theme_dossier` 与 `theme tracking` 继续推向研究型产物

当前问题：

- `theme_dossier` 已经存在，但仍可继续深化为更强的研究型档案
- dossier 与 chat 的联动已经建立，但仍可继续增强为更强的研究助理体验

说明：

这条线仍然重要，但现在的重点从“启动 dossier”转为“深化 dossier + chat 联动”。

### 5.4 运维与可观测性

目标：

- 让系统更像可维护的长期运行产品，而不是一次性任务

当前问题：

- 当前主链已基本补齐
- 后续若继续推进，重点不再是补底层运维能力，而是消费这些运维产物

说明：

这条线已经达到可持续运行的基线，短期内不再是最高优先级。

### 5.5 信源可靠性

目标：

- 提高真实抓取成功率和稳定产出能力

当前问题：

- `Tesla` 官方源持续 `403`
- `Xiaomi` 官方 Discover 页主要依赖动态渲染，当前静态抓取器无法稳定拿到文章链接
- 仍有部分公司需要长期观察，防止源结构变化后重新退化

说明：

这条线仍然重要，但当前应按“低风险增量修复”推进，不适合为单一公司引入高复杂度抓取方案。

### 5.6 内容质量

目标：

- 提升日报可读性和长期阅读价值

当前问题：

- 单条摘要质量仍有波动
- 主题 `summary / comparison / trend` 的文风还可以更统一
- `其他重要动态` 仍可继续压缩
- LLM 生成内容仍有少量“分析力度不足”或“判断略平”的情况

说明：

这条线价值高，但当前不作为最近一批优先事项。

### 5.7 前端体验收尾

目标：

- 提升长期阅读舒适度和交互完成度

当前问题：

- 研究侧栏仍可继续做得更像研究工作台
- dossier / tracking / cross-day 的阅读层次仍可继续精修
- 移动端问答与深读页仍有细节优化空间

说明：

这条线当前属于可选精修，而不是主线缺口。

### 5.8 兄弟日报与未来扩展

目标：

- 在主日报成熟后，拓展新的 sibling pipeline

当前状态：

- `GitHub 今日 Highlight 日报` 已有概念文档
- 还未进入正式需求设计与实现

说明：

这条线属于中期扩展，不应抢占主日报当前的稳定性改进资源。

## 6. 推荐优先级

基于当前项目状态，推荐优先级如下：

1. `Research Assistant v3`
2. `信源广度与信息量增强`
3. `主题研究深化`
4. `运维与可观测性`
5. `信源可靠性`
6. `内容质量`
7. `前端体验收尾`
8. `兄弟日报与未来扩展`

## 7. 下一阶段推荐批次

后续优化按批次推进，每批次都应满足：

- 有明确目标
- 有清晰验收口径
- 尽量低耦合
- 改动后必须回归测试

### 批次 A：Research Assistant v3

目标：

- 继续把研究助理往 `LLM + SKILLS + TOOLS + RAG + 边界控制` 收口

建议任务：

- 继续弱化旧 question-type 心智
- 让 runtime assistant 更自由地使用日报 RAG 与通用 LLM 能力
- 继续把 `chat_agent_*` 压成 preview / fallback 兼容层
- 提高 tool orchestration 能力，为未来 `web_search` 预留稳定边界
- 优化 evidence / note / follow-up 的自然呈现

验收口径：

- 对开放式问题不再显得像固定问答器
- 一般知识回答不会错误挂日报证据
- runtime assistant 与 preview fallback 的边界清楚
- tools / rag / llm 的作用分工在实现上清晰

状态：

- 进行中，当前是主线

### 批次 B：信源广度与信息量增强

目标：

- 在维持官方信源优先的前提下，提高信息量与主题形成能力

建议任务：

- 为高价值公司补第二、第三官方入口
- 优先补高信号、低噪音源，而不是盲目堆数量
- 解决“稳定但内容过少”的问题，提高主刊与日报的内容密度
- 优先关注能明显增加主题形成能力的源

验收口径：

- 连续多天日报不再因为低产出显得过空
- 更容易形成 2-3 个值得阅读的主线主题
- 内容密度提升不以明显增加噪音为代价

### 批次 C：主题研究深化

目标：

- 把现有 `theme_dossier` 与 `theme tracking` 进一步推向研究型产物

建议任务：

- 继续深化 `theme_definition`
- 深化 `company_positions`
- 深化 `timeline_events[].why_it_matters`
- 强化 dossier 与 research assistant 的联动质量

验收口径：

- dossier 更像研究简报
- chat 对主题档案的消费更自然

状态：

- 进行中，但让位于 Research Assistant v3 与信源广度

### 批次 D：运维与可观测性延伸

目标：

- 保持当前运维基线，同时把其更多变成 agent / UI 可消费资产

建议任务：

- 继续精炼 `health_snapshot`
- 为未来 tool use 和 agent 诊断提供更清晰输入
- 保持历史问题与恢复问题的可追溯性

验收口径：

- 运维信息更容易直接进入 research assistant 与 UI
- 不新增复杂运维分支

状态：

- 当前不是最高优先级

### 批次 E：内容质量第二轮提升

目标：

- 把日报从“可读原型”继续推向“高质量研究型日报”

建议任务：

- 统一 `summary / comparison / trend` 文风
- 压缩 `其他重要动态`
- 优化 LLM 提示词与输出后处理
- 强化“为什么重要”的表达稳定性

验收口径：

- 同一天不同区块的文风更统一
- 低信息密度主题减少
- 用户主观阅读体验明显改善

状态：

- 当前让位于 agent 与信源主线

### 批次 F：前端体验收尾

目标：

- 提升长期阅读效率与交互完成度

建议任务：

- 继续精修 Research Assistant 侧栏
- 继续精修结论 / 证据 / follow-up 的阅读层次
- 移动端细节优化
- 深读页阅读节奏继续优化

验收口径：

- 页面阅读更轻松
- 研究助理更像研究工作台，而不是附属工具

### 批次 G：信源持续巡检

目标：

- 避免历史修好的公司再次退化

建议任务：

- 对已修好的 `ByteDance / Alibaba / Huawei / Tencent / xAI` 做持续观察
- 增加简单的“连续 3 天低产出提醒”
- 明确 `Tesla / Xiaomi` 维持占位策略，除非出现低复杂度可行官方替代源

验收口径：

- 已修好的公司不会因旧历史噪音继续占据高优先级
- 低产出风险能被更早发现

状态：

- 进行中，但短期保持低复杂度增量维护

### 批次 H：兄弟日报启动

目标：

- 在主日报稳定的前提下，启动新的 sibling pipeline

建议任务：

- 将 `GitHub 今日 Highlight 日报` 从概念文档推进到需求文档
- 定义热度信号、入选标准、主题体系、页面结构

验收口径：

- 输出一套独立需求与设计文档
- 不与现有科技日报主链路耦合

## 8. 当前推荐立即执行项

如果后续继续按这份文档推进，我建议下一步直接进入：

`批次 A：Research Assistant v3`

也就是：

1. 继续让 runtime assistant 更 LLM-first
2. 继续让 RAG 成为 grounding layer 而不是唯一答案边界
3. 让 tool orchestration 进入真正可扩展状态

## 9. 执行原则

后续每一批改进都遵循下面的原则：

- 先补测试，再改实现
- 优先保持高内聚、低耦合
- 优先在现有边界内演进，而不是扩散新层
- 不因为个别边缘问题引入高复杂度方案
- 每次改动都要能独立回滚、独立验证、独立理解

这份文档后续应作为项目改进的统一参考入口。
