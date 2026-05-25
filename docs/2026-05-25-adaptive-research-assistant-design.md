# Adaptive Research Assistant 设计文档

日期：2026-05-25

## 1. 背景

当前 `runtime-first research assistant` 已经能实时读取：

- `report.json`
- `daily_intel_brief.json`
- `cross_day_intel_brief.json`
- `theme_tracking_brief.json`
- `theme_dossier.json`
- `health_snapshot.json`

并基于这些结构化日报产物回答问题。

但当前回答链仍然有一个明显问题：

- 一旦问题不落在日报知识层里，回答就容易显得机械
- LLM 更多是在“包装日报答案”，而不是作为真正的研究助理工作
- 用户对“日报依据”和“模型补充”之间的边界感知也不够自然

## 2. 目标

把当前研究助理升级成：

**Adaptive Research Assistant**

它应当支持三类能力：

1. **日报强依据回答**
   - 日报知识层里有充分证据
   - 回答以日报内容为主

2. **日报 + 模型补充回答**
   - 日报里有部分信息
   - 模型负责补充解释或推断

3. **通用知识回答**
   - 日报里没有直接信息
   - 允许模型回答通用科技知识
   - 但必须明确说明这部分并非日报依据，仅供参考

## 3. 非目标

这轮不做：

- 外网搜索
- 向量数据库
- 通用 RAG 基础设施
- 长期记忆
- 重新设计研究侧栏的大结构

## 4. 设计原则

### 4.1 内部有模式，外部不暴露模式名

内部保留三种回答模式：

- `grounded`
- `hybrid`
- `general`

但 UI 不直接显示这些模式名。

外部只体现必要的可信度说明：

- `grounded`：通常静默
- `hybrid`：轻量说明“结合了日报内容与模型推断”
- `general`：明确说明“这部分回答不直接来自当前日报，仅供参考”

### 4.2 日报知识层是 grounding，不是硬上限

日报 JSON 仍然是研究助理的知识底座，但不再把 LLM 限制成：

- “知识库没有就不会答”

而是改成：

- 先检索日报知识层
- 有证据则优先用
- 没证据则允许通用回答
- 但必须说明边界

### 4.3 证据区区分两类来源

回答的补充信息需要自然分层：

- `日报依据`
- `补充判断`
- `通用知识补充`

这样用户能理解：

- 哪些内容来自日报
- 哪些内容来自模型延伸

## 5. 架构改造

### 5.1 context builder

`research_agent_context_builder.py` 从：

- “按问题类型挑固定 source”

升级成：

- 结合问题、公司、主专题做动态相关性选择

输出包括：

- `selected_sources`
- `matched_sources`
- `selected_context`
- `grounding_mode`

### 5.2 response layer

`research_agent_response.py` 新增 adaptive answer 策略：

- `grounded`
- `hybrid`
- `general`

并把：

- 回答正文
- 证据项
- follow-up
- 可信度附注

统一收口到共享 policy。

### 5.3 shared policy

`research_assistant_policy.py` 继续负责：

- evidence item 结构
- answer note 生成
- follow-up suggestions
- 最终 answer payload shape

## 6. UI 呈现

### 6.1 页面与 CLI

页面侧栏和 CLI 都沿用同一条 adaptive 回答链。

### 6.2 页面附注

仅在必要时展示：

- `这部分判断结合了当前日报内容与模型推断。`
- `这部分回答不直接来自当前日报，仅供参考。`

### 6.3 证据区

证据区按 bucket 分组：

- `日报依据`
- `补充判断`
- `通用知识补充`

## 7. 完成标准

完成时至少满足：

1. 问一般科技问题时，不再显得像 mock 或卡死
2. 如果日报里有相关内容，回答仍优先使用日报依据
3. 如果日报里没有，允许通用回答，但显式给出边界说明
4. 页面与 CLI 共用同一条 adaptive 回答链
5. 全量测试通过
