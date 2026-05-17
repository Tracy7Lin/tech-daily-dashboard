# Session-Memory Chat 设计文档

## 1. 目标

让当前网页与 CLI 的 chat 从“单轮问答器”升级为“会话级研究助理”。

第一版只做当前会话内的上下文记忆，不做长期记忆或跨页面持久化。

## 2. 范围

支持这类连续追问：

- `这个主专题现在怎么理解？`
- `那 Google 呢？`
- `为什么不是 active？`
- `继续说时间线`
- `还有别的吗？`

要求：

- 页面 chat drawer 可连续追问
- CLI 可在单次运行中传入最近几轮消息
- 事实边界仍然只来自本地产物

## 3. 非目标

- 不做数据库存储
- 不做跨天长期记忆
- 不做用户画像
- 不做外部搜索或 RAG

## 4. 核心设计

### 4.1 会话窗口

每轮只保留最近 `3-6` 条消息的结构化摘要：

- `role`
- `question`
- `question_type`
- `resolved_theme`
- `resolved_company`
- `answer_summary`

### 4.2 追问补全

新增一层会话理解逻辑，用于识别：

- `那 X 呢`
- `为什么`
- `继续说`
- `还有别的吗`

并根据上一轮或最近几轮补全：

- 当前主题
- 当前公司
- 当前问题类型

### 4.3 接入方式

- 新增 `chat_agent_memory.py`
- `chat_agent_analysis.py` 支持 `follow_up`
- `chat_agent_pipeline.py` 支持 `history/messages`
- `web_chat_server.py` 接收 `messages`
- 前端 drawer 保留最近消息并发送给后端

## 5. 降级策略

如果补全失败：

- 回退到单轮问答
- 保持页面可用
- 必要时提示用户补充公司或主题名称

## 6. 验收标准

- 页面内连续追问可用
- `那 Google 呢` 能继承上一轮主专题
- `为什么不是 active` 能继承上一轮主题状态问题
- 单轮问答不受影响
- 全量测试通过
