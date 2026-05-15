# Dossier-Aware Chat 设计文档

## 1. 文档目的

这份文档用于定义 `dossier-aware chat` 的第一版设计。

它不是一条新的聊天系统，而是在现有前端对话 agent 基础上，正式把 `theme_dossier.json` 纳入问答能力边界，让 chat 从“日报问答器”提升为“专题研究助理雏形”。

## 2. 为什么需要 Dossier-Aware Chat

当前系统已经具备：

- 当日情报判断
- 跨日观察
- 专题跟踪
- 主题 dossier
- 页面内问答入口

但现有 chat 仍主要围绕：

- 今天最值得关注什么
- 某家公司最近几天在做什么
- 主专题是什么
- 当前信源状态如何

也就是说，`theme_dossier` 已经生成出来了，但还没有被前端问答和 CLI 问答真正消费起来。

## 3. 目标

`dossier-aware chat v1` 要实现：

- 让 chat 直接读取并使用 `theme_dossier.json`
- 支持围绕 dossier 的研究助理式问题
- 回答风格从“快速问答”升级为“先给判断，再给依据”
- 保持现有页面壳层和 CLI 入口不变

## 4. 非目标

这轮不做：

- 多轮记忆
- 会话状态持久化
- 向量检索
- 外部搜索
- 新的后端服务层
- 单独的新 UI 容器

这仍然是现有 `chat_agent_*` 链路的一次能力增强。

## 5. 输入边界

chat 输入在现有基础上新增：

- `theme_dossier.json`

因此 chat 输入现在包括：

1. `report.json`
2. `daily_intel_brief.json`
3. `cross_day_intel_brief.json`
4. `theme_tracking_brief.json`
5. `theme_dossier.json`
6. `health_snapshot.json`

其中：

- `theme_tracking_brief` 负责“当前主专题是谁”
- `theme_dossier` 负责“这个主专题当前处于什么状态、公司位置如何、时间线说明了什么”

## 6. 内部上下文结构

当前 chat context 已经有：

- `daily_summary`
- `theme_tracking`
- `ops_status`
- `company_answers`

建议新增：

- `theme_dossier`

字段建议至少包括：

- `primary_theme`
- `theme_definition`
- `theme_state`
- `theme_summary`
- `company_positions`
- `timeline_events`
- `tracking_decision`
- `next_day_focus`

这样页面和 CLI 都不需要直接理解 dossier 文件本身的结构。

## 7. 新增问题类型

建议在 `chat_agent_analysis` 中新增：

### 7.1 `dossier_summary`

示例问题：

- “这个主专题现在怎么理解？”
- “为什么这个专题还值得跟踪？”

### 7.2 `theme_state`

示例问题：

- “为什么现在是 emerging？”
- “这个主题为什么不是 active？”

### 7.3 `company_position`

示例问题：

- “Google 在这个专题里处于什么位置？”
- “OpenAI 在这个 dossier 里的角色是什么？”

### 7.4 `timeline_focus`

示例问题：

- “最近几天这个专题是怎么演化的？”
- “时间线里最关键的事件是什么？”

现有问题类型继续保留：

- `daily_summary`
- `company_focus`
- `theme_focus`
- `ops_status`
- `out_of_scope`

## 8. 回答风格

这轮 chat 的回答风格明确偏向：

- `研究助理`

要求：

- 先给判断
- 再给 1-2 个依据
- 语言仍保持简洁
- 不引入 dossier 之外的新事实

也就是说，它不追求长答案，而追求“研究视角的短答案”。

## 9. 输出对象

统一回答对象结构保持不变：

- `answer`
- `question_type`
- `sources_used`
- `follow_up_suggestions`
- `mode_used`

但现在：

- `sources_used` 允许出现 `theme_dossier.json`
- `follow_up_suggestions` 要更 dossier-aware，例如：
  - “为什么这个主题现在是 emerging？”
  - “Google 在这个专题里的位置是什么？”
  - “最近几天关键时间线说明了什么？”

## 10. 页面嵌入上下文

建议在 `response_bank` 中新增：

- `dossier_summary`
- `theme_state`
- `timeline_focus`
- `company_position_answers`

其中：

- `company_position_answers` 按公司生成
- 页面仍然不直接调用 Python，只消费预生成 response bank

这样页面 chat drawer 仍然保持：

- 轻前端
- 重逻辑在 Python

## 11. 规则层与 LLM 层边界

这条线继续保持当前系统原则：

- 规则层负责：
  - dossier 问题分类
  - 结构化上下文选取
  - 基础回答保底

- LLM 层负责：
  - 回答表达增强
  - 把 dossier 内容组织成更像研究助理的回答

LLM 不应：

- 发明 dossier 外的新事件
- 发明未出现的公司位置
- 自主修改主题状态

## 12. 模块划分

这轮不新增新的 `dossier_chat_*` 模块，而是增强现有：

- `chat_agent_input.py`
- `chat_agent_analysis.py`
- `chat_agent_response.py`
- `chat_agent_pipeline.py`

职责变化如下：

### 12.1 `chat_agent_input.py`

- 新增读取 `theme_dossier.json`

### 12.2 `chat_agent_analysis.py`

- 新增 dossier 问题类型识别

### 12.3 `chat_agent_response.py`

- 新增 dossier-aware 回答路径
- 支持：
  - `dossier_summary`
  - `theme_state`
  - `company_position`
  - `timeline_focus`

### 12.4 `chat_agent_pipeline.py`

- 把 dossier 注入 chat context
- 生成 dossier-aware response bank

## 13. 页面与 CLI 接入方式

### CLI

CLI 入口保持不变：

```bash
python run_dashboard.py chat --date YYYY-MM-DD --question "..."
```

只是可回答的问题范围扩大。

### 页面

页面仍然使用现有：

- 右下角浮动入口
- 右侧抽屉式聊天面板

这轮不增加新 UI 容器，只增强：

- 快捷问题
- dossier-aware 回答
- follow-up 建议

## 14. 快捷问题升级建议

为了让 dossier 的价值更快显现，建议加入：

- “这个主专题现在怎么理解？”
- “为什么这个主题现在是 emerging？”
- “最近几天关键时间线说明了什么？”

如果当天 dossier 中有多个参与公司，也可以加入：

- “Google 在这个专题里的位置是什么？”

## 15. 降级策略

如果 `theme_dossier.json` 缺失：

- chat 仍正常工作
- 新增 dossier 问题类型回退到：
  - `theme_tracking_brief`
  - `cross_day_intel_brief`
  - 或更保守的规则回答

如果 LLM 不可用：

- dossier-aware chat 仍然使用规则回答

## 16. 验收标准

这一版完成时，应满足：

- `theme_dossier.json` 被 chat 输入层读取
- chat 能识别 dossier 新问题类型
- CLI 能回答 dossier 问题
- 页面 response bank 包含 dossier-aware 项
- 快捷问题中出现 dossier 导向问题
- 页面与 CLI 仍然共享同一条 Python 回答链
- LLM 失败时能够规则回退
- 全量测试通过

## 17. 推荐顺序

建议下一步执行顺序：

1. 先写实现计划
2. 先补 dossier-aware chat 测试
3. 再增强 input / analysis / response / pipeline
4. 最后更新页面快捷问题与 response bank

这样最稳，也最容易看清 dossier 是否真正被系统消费起来。
