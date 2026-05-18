# Runtime-First Research Assistant 设计文档

日期：2026-05-18

## 1. 背景

当前网页 `情报问答` 虽然已经具备：

- 运行时 `/api/chat`
- dossier-aware 问答
- session memory
- 静态 `response_bank` 兜底

但实际体验仍然容易接近“mock”：

- 页面在很多情况下优先表现为预生成回答，而不是实时 agent
- 用户很难判断当前到底是静态预览、规则回退，还是实时 LLM 问答
- 回答自由度有限，容易表现成“围绕预设问题的问答器”，而不是研究助理

问题不在于缺少 LLM，而在于 **运行模式和系统边界不对**。当前 chat 的默认心智仍然是“页面内嵌问答壳层”，而不是“实时研究助理”。

## 2. 目标

把当前网页 chat 和 CLI chat 升级成：

**自由提问的研究助理**

同时保持一个明确的知识边界：

- 它的知识库只来自本项目生成的日报体系
- 不做开放互联网搜索
- 不从 HTML 页面抓内容
- 不依赖页面结构理解内容

它应该能自然回答：

- 今天最值得关注什么？
- 这个主专题现在怎么理解？
- 为什么现在是 emerging？
- Google 在这个专题里的位置是什么？
- 最近几天关键时间线说明了什么？
- 还有别的值得关注的主题吗？

## 3. 非目标

这轮不做：

- 外网搜索
- 向量数据库 / 检索基础设施
- 长期记忆
- 用户级个性化记忆
- 多 agent orchestration
- 把 chat 变成一个通用大模型聊天框

## 4. 核心原则

### 4.1 Runtime-First

页面和 CLI 的默认路径应当是：

`用户问题 -> runtime research agent -> 读取结构化知识 -> 动态构造上下文 -> 回答`

而不是：

`用户问题 -> 页面预生成 response_bank -> 固定答案`

### 4.2 JSON Knowledge Layer

agent 只读取结构化产物，不读 HTML。

输入知识层包括：

- `report.json`
- `daily_intel_brief.json`
- `cross_day_intel_brief.json`
- `theme_tracking_brief.json`
- `theme_dossier.json`
- `health_snapshot.json`

这保证：

- 前端可自由改版
- chat 不被模板结构绑死
- 问答逻辑稳定、可测试

### 4.3 Preview Fallback

静态 `response_bank` 仍然保留，但只作为：

- `file://` 打开的本地预览
- 本地服务未启动时的回退
- `/api/chat` 暂时失败时的安全降级

也就是说，`response_bank` 继续存在，但从主路径降级为备用路径。

## 5. 方案比较

### 方案 A：继续增强现有 response_bank

优点：

- 改动最小

缺点：

- 无法根治“像 mock”的问题
- 依然会优先表现为固定答案池

### 方案 B：Runtime-First Research Assistant

优点：

- 回答路径和系统边界清楚
- 页面与 CLI 使用同一条真实问答链
- 更符合“研究助理”的目标

缺点：

- 需要一次中等规模重构

### 方案 C：直接 RAG 化

优点：

- 自由问答上限更高

缺点：

- 当前过重
- 会引入新的检索基础设施，不适合现在这轮

### 推荐

采用 **方案 B**。

## 6. 架构设计

### 6.1 新的能力链

新增一条明确的运行时研究助理链：

- `research_agent_input`
- `research_agent_context_builder`
- `research_agent_response`
- `research_agent_pipeline`

### 6.2 责任划分

#### research_agent_input

职责：

- 按日期读取结构化日报产物
- 只处理文件定位和载入
- 不处理回答逻辑

输入：

- `site_dir`
- `data_dir`
- `report_date`

输出：

- `ResearchAgentInputs`

#### research_agent_context_builder

职责：

- 从多份 JSON 中筛选与问题相关的上下文
- 按问题类型组织证据
- 做轻量动态上下文裁剪

它不生成最终答案，只生成“适合回答这个问题的上下文”。

#### research_agent_response

职责：

- 结合上下文和问题生成最终回答
- 支持：
  - `rule`
  - `llm`
  - `hybrid`

原则：

- 事实只来自上下文
- LLM 只负责理解和表达增强
- 不发明上下文之外的新事实

#### research_agent_pipeline

职责：

- 统一编排整条运行时问答链
- 页面 `/api/chat` 和 CLI `chat` 都调用它

## 7. 与现有 chat 的关系

### 保留

- `chat drawer` UI
- `session memory`
- `/api/chat`
- `response_bank` 作为 fallback

### 调整

- 页面默认不再把 `response_bank` 当主回答源
- `/api/chat` 成为主路径
- `response_bank` 仅在无运行时服务或运行时失败时使用

### 替换

当前更偏“固定路由 + 预生成答案”的部分，应逐步让位给 `research_agent_pipeline`。

## 8. 页面行为

### HTTP 运行时

当页面运行在：

- `http://127.0.0.1:8080`
- 或其他本地服务地址

chat 默认：

- 先请求 `/api/health`
- 再走 `/api/chat`

页面会清楚显示三种状态：

- `静态预览模式`
- `本地问答服务已连接，但当前返回规则回答`
- `实时增强问答已连接`

### file 预览

当页面运行在 `file://` 下：

- 直接使用 `response_bank`
- 明确提示这是静态预览模式

## 9. CLI 行为

CLI 继续保留：

```bash
python run_dashboard.py chat --date YYYY-MM-DD --question "..."
```

但内部改成调用新的 `research_agent_pipeline`，保证和网页是同一条回答链。

## 10. 错误处理

### 缺少日报产物

- 返回清晰错误
- 不伪装成“无内容回答”

### 运行时服务不可用

- 页面回退到 `response_bank`
- 明确提示当前不是实时问答

### LLM 不可用

- 继续使用规则路径
- 仍然能回答，但明确状态为规则回答

## 11. 测试策略

至少覆盖：

- `research_agent_input` 正确读取多份 JSON
- `research_agent_context_builder` 能按问题类型选择上下文
- `research_agent_response` 在 `rule / llm / hybrid` 下行为正确
- `/api/health` 能返回运行时模式与 LLM 可用性
- `/api/chat` 页面与 CLI 共享同一条运行时问答链
- `response_bank` 仅作为 fallback，不再是主路径

## 12. 完成标准

满足以下条件时，这轮视为完成：

1. 页面 chat 默认走运行时 agent
2. CLI 和网页共用同一条问答主链
3. 页面可以明确分辨静态预览、规则回退、实时增强
4. 提问风格显著比当前更自由，不再像固定问答器
5. `response_bank` 只剩下兜底角色

