# Research Assistant 侧栏化与共享策略收敛设计文档

日期：2026-05-18

## 1. 背景

当前 `runtime-first research assistant` 已经具备：

- 运行时读取日报 JSON 知识层
- dossier-aware 问答
- session memory
- 流式逐句输出
- 项目内 `research-agent-question-orchestration` skill

但还存在两个明显问题：

1. **Agent 的产品地位不够高**
   - 主要入口仍然是右下角浮动按钮
   - 更像页面内工具，而不是系统核心能力
   - 在桌面端阅读时，问答区与正文关系较弱

2. **回答组织策略仍然分散**
   - `chat_agent_response.py`
   - `research_agent_response.py`
   仍然各自保留一部分 answer synthesis / evidence / follow-up 逻辑
   - 这会让 CLI、网页侧栏、运行时研究助理继续像几条相近但不完全一致的回答链

这轮的目标不是新增更多 agent 层级，而是：

- 把 `Research Assistant` 正式提升为页面骨架的一部分
- 继续把研究助理的重复回答流程往共享策略层收

## 2. 目标

这轮实现以下两项目标：

### 2.1 页面骨架升级

桌面端页面改为：

- 左侧 1 份：导航/刊物入口
- 中间 3 份：正文内容
- 右侧 1 份：常驻 `Research Assistant`

移动端继续保留抽屉式问答，不强行塞入侧栏。

### 2.2 回答策略收敛

继续把以下内容从 responder 中收敛到共享策略层：

- answer synthesis
- evidence shape
- source label/reference policy
- follow-up suggestion policy

目标是让：

- CLI chat
- 页面常驻研究侧栏
- 运行时研究助理

更像同一个 agent 的不同入口。

## 3. 非目标

这轮不做：

- 长期记忆
- 向量检索 / RAG
- 外网搜索
- 多 agent orchestration
- 全站服务端渲染
- 移动端常驻侧栏
- 一次性把两个 responder 合并成一个大文件

## 4. 方案比较

### 方案 A：继续保留浮动按钮，只增强视觉存在感

优点：

- 改动小

缺点：

- 不能真正提升 agent 的产品地位
- 阅读和问答仍然是“正文之后再打开工具”

### 方案 B：桌面端常驻研究侧栏，移动端抽屉兜底

优点：

- 最符合当前科技情报杂志的阅读模型
- 能让研究助理成为页面骨架的一部分
- 不破坏移动端密度

缺点：

- 需要调整多个页面模板结构

### 方案 C：所有端都强制常驻侧栏

优点：

- 结构统一

缺点：

- 移动端体验明显变差
- 不适合当前页面信息密度

### 推荐

采用 **方案 B**。

## 5. 核心原则

### 5.1 Agent 是骨架，不是插件

在桌面端，`Research Assistant` 不应继续主要依赖浮动按钮暴露，而应成为：

- 当前主专题提示
- 快捷问题入口
- 运行时问答
- 证据来源
- 后续追问建议

的稳定边栏。

### 5.2 桌面/移动分层

- 桌面端：常驻右侧研究侧栏
- 移动端：抽屉式问答

不强行用一种布局覆盖所有端。

### 5.3 共享策略先于布局

这轮先继续收稳共享策略层，再让 UI 依赖它。避免把新的侧栏做出来之后，底层回答逻辑仍然分叉。

### 5.4 不过早做抽象框架

不引入新的复杂框架，只扩展：

- `research_assistant_policy.py`

作为 `question understanding` 之外的主要 agent 回答规范载体。

## 6. 页面结构设计

### 6.1 桌面端五栏布局

桌面端页面使用五栏心智模型：

- 左侧 1 栏：`magazine rail`
  - 主刊导航
  - 返回首页 / 日报 / 专题 / 档案
  - 当前期次/当前主题的小提示

- 中间 3 栏：`main editorial body`
  - 首页：封面与栏目
  - 日报页：当期正文
  - 专题页/档案页：深读内容

- 右侧 1 栏：`research assistant rail`
  - 当前主专题
  - 当前阶段
  - 快捷问题
  - 会话内容
  - 证据来源
  - follow-up suggestions

### 6.2 移动端

移动端不做常驻侧栏：

- 仍保留抽屉式聊天
- 主内容优先
- 研究助理通过明显按钮或粘性入口唤起

## 7. 侧栏组件分工

右侧研究侧栏拆成 4 个稳定组件：

### 7.1 assistant header

展示：

- `Research Assistant`
- 当前模式
- 当前主专题
- 当前阶段

### 7.2 assistant quick prompts

只保留 3-5 个高价值问题，例如：

- 这个主专题现在怎么理解？
- 为什么现在是 emerging？
- 最近几天关键时间线说明了什么？

### 7.3 assistant conversation

承载：

- 逐句流式输出
- 用户问题
- 运行状态
- 连续追问

### 7.4 assistant evidence rail

承载：

- 证据来源
- reference 标识
- follow-up suggestions

它应更像“研究工作台”，而不是普通聊天气泡堆叠。

## 8. 共享策略层收敛

### 8.1 当前状态

目前已经开始共享：

- evidence item
- follow-up suggestions
- payload finalization

但仍有一部分回答组织逻辑分散在：

- `chat_agent_response.py`
- `research_agent_response.py`

### 8.2 本轮收敛目标

继续扩展 `research_assistant_policy.py`，收敛：

- answer synthesis order
- dossier/company/timeline/ops 各类问题的回答组织方式
- evidence and follow-up generation policy

### 8.3 分层策略

#### question understanding

继续保留在现有结构中：

- `understand_chat_question(...)`
- `resolve_follow_up_route(...)`

本轮不大动这一层。

#### answer synthesis policy

统一规则：

- 先判断
- 再依据
- 再建议继续追问

并按问题类型组织：

- dossier summary
- theme state
- company position
- timeline focus
- ops status

#### evidence and follow-ups policy

统一：

- evidence shape
- source naming
- reference policy
- follow-up generation

## 9. 实现顺序

### 第一步：共享策略层

先扩展 `research_assistant_policy.py`，继续把 answer synthesis 往里收。

### 第二步：桌面端侧栏化

再把：

- 首页
- 日报页
- 专题页
- 档案页

改成桌面端带常驻 `Research Assistant` 侧栏的结构。

### 第三步：交互收尾

最后补：

- 侧栏与移动抽屉的切换
- 状态提示
- 快捷问题交互
- 证据 rail 展示

## 10. 风险控制

### 风险 1：页面布局回退

处理方式：

- 保持现有页面职责不变
- 只改变桌面端布局骨架

### 风险 2：移动端体验变差

处理方式：

- 移动端继续保留抽屉
- 不强推常驻侧栏

### 风险 3：回答逻辑漂移

处理方式：

- 不一次性合并 responder
- 先做 shared policy，再改 UI

## 11. 测试策略

至少覆盖：

- render tests
- `chat_agent_response` tests
- `research_agent_response` tests
- `generate-today` 真实构建验证

并重点验证：

- 桌面端存在常驻 agent 侧栏
- 移动端仍保留抽屉 fallback
- evidence / follow-ups 不回退
- 现有问题类型回答不漂移

## 12. 完成标准

满足以下条件时，这轮视为完成：

1. 桌面端形成 `左导航 / 中正文 / 右研究侧栏`
2. `Research Assistant` 不再主要靠底部 launcher 暴露
3. 移动端仍可用
4. `chat_agent_response.py` 与 `research_agent_response.py` 的 answer synthesis 进一步共享
5. 现有问答能力不回退
6. 全量测试通过
