# Dossier-Aware Chat 实现计划

## 目标

在现有前端对话 agent 基础上，正式接入 `theme_dossier.json`，让 chat 能回答更偏研究助理风格的问题，同时保持：

- 页面 chat drawer 不变
- CLI `chat` 入口不变
- 规则 / LLM / hybrid 模式不变
- 主日报主链路稳定

## 实施原则

- 先补测试，再改实现
- 保持高内聚、低耦合
- 不新建独立聊天系统
- dossier 失败或缺失时必须安全回退
- 回答先给判断，再给 1-2 个依据

## 模块范围

本轮只增强现有模块：

- `src/tech_daily/chat_agent_input.py`
- `src/tech_daily/chat_agent_analysis.py`
- `src/tech_daily/chat_agent_response.py`
- `src/tech_daily/chat_agent_pipeline.py`

并视需要接：

- `templates/index.html`
- `templates/daily.html`
- `src/tech_daily/render.py`
- `tests/test_chat_agent_input.py`
- `tests/test_chat_agent_response.py`
- `tests/test_chat_agent_pipeline.py`
- `tests/test_render.py`

## 分阶段执行

### 阶段 A：输入层接 dossier

任务：

- `chat_agent_input` 读取 `theme_dossier.json`
- 输入 dataclass 增加 dossier 字段
- dossier 缺失时保持兼容

完成标准：

- chat 输入层能稳定读取 dossier，且缺失不报错

### 阶段 B：问题分类增强

任务：

- 在 `chat_agent_analysis` 中新增：
  - `dossier_summary`
  - `theme_state`
  - `company_position`
  - `timeline_focus`
- 保持旧问题类型兼容

完成标准：

- Python 层能正确把 dossier 导向问题归类

### 阶段 C：回答层增强

任务：

- 在 `chat_agent_response` 中新增 dossier-aware 回答逻辑
- 回答时优先使用：
  - `theme_state`
  - `theme_definition`
  - `company_positions`
  - `timeline_events`
  - `tracking_decision`
- LLM 不可用时回退到规则回答

完成标准：

- CLI 能回答 dossier 类问题

### 阶段 D：response bank 与页面快捷问题增强

任务：

- 在 `chat_agent_pipeline` 中把 dossier 注入 context
- 新增 response bank：
  - `dossier_summary`
  - `theme_state`
  - `timeline_focus`
  - `company_position_answers`
- 页面快捷问题增加 dossier 导向问题

完成标准：

- 页面 chat drawer 能直接消费 dossier-aware 问答结果

### 阶段 E：验证与收尾

任务：

- 补单元测试
- 跑全量测试
- 真实生成日报
- 真实运行 CLI `chat`
- 检查页面已包含 dossier 导向快捷问题

完成标准：

- 全量测试通过
- 真实 CLI 回答 dossier 问题
- 页面可见 dossier 导向问答入口

## 问题分类规则

建议最小规则：

- `dossier_summary`
  - 命中：`怎么理解`、`为什么值得跟踪`、`这个主专题`
- `theme_state`
  - 命中：`为什么是 emerging`、`为什么不是 active`、`阶段`
- `company_position`
  - 命中：`在这个专题里处于什么位置`、`角色是什么`
- `timeline_focus`
  - 命中：`时间线`、`最近几天怎么演化`、`关键事件`

## 回答结构

保持现有统一对象：

- `answer`
- `question_type`
- `sources_used`
- `follow_up_suggestions`
- `mode_used`

新增要求：

- `sources_used` 允许包含 `theme_dossier.json`
- `follow_up_suggestions` 中加入 dossier 导向追问

## 降级策略

- `theme_dossier.json` 缺失：
  - 回退到 `theme_tracking_brief` / `cross_day_intel_brief`
- LLM 不可用：
  - 回退规则回答
- 页面 response bank 缺 dossier 项：
  - 仍保持旧 chat 行为

## 验收口径

- chat 输入层支持 dossier
- chat 能识别 dossier 新问题类型
- CLI 能回答 dossier 问题
- 页面 response bank 包含 dossier-aware 项
- 页面快捷问题中出现 dossier 导向问题
- 全量测试通过
