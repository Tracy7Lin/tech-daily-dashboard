# 前端对话 Agent 实现计划

## 目标

实现一个页面内可用的前端对话 agent v1，满足：

- 页面右下角浮动入口
- 右侧抽屉式对话面板
- 基于本地产物回答问题
- 支持四类核心问题：
  - 今日总结
  - 公司追问
  - 主题追问
  - 运维状态
- 保持现有日报主链路稳定
- LLM 失败时可降级

## 实施原则

- 先补测试，再改实现
- 保持高内聚、低耦合
- 对话能力不反向污染抓取与日报生成
- 事实边界严格受现有产物限制
- 先实现最小可用链路，再做 UI 精修

## 模块拆分

### 1. 问答能力层

新增模块：

- `src/tech_daily/chat_agent_input.py`
- `src/tech_daily/chat_agent_analysis.py`
- `src/tech_daily/chat_agent_response.py`
- `src/tech_daily/chat_agent_pipeline.py`

职责：

- `chat_agent_input`
  - 读取当日日报、当日 agent brief、跨日 brief、专题 brief、health snapshot
- `chat_agent_analysis`
  - 问题归类
  - 提取相关上下文
- `chat_agent_response`
  - 规则 / LLM / hybrid 回答
- `chat_agent_pipeline`
  - 串联输入、分析、回答

### 2. CLI 接口

新增一个最小问答命令，例如：

```bash
python run_dashboard.py chat --date 2026-05-15 --question "今天最值得关注什么？"
```

职责：

- 便于本地验证问答链路
- 作为页面桥接前的稳定入口

### 3. 页面接入

修改：

- `src/tech_daily/render.py`
- `templates/index.html`
- `templates/daily.html`

目标：

- 增加右下角浮动入口
- 增加右侧抽屉式聊天面板
- 接入快捷问题 chips
- 保留科技感、简约、清晰层级

## 分阶段执行

### 阶段 A：问答能力层

任务：

- 增加结构化输入加载
- 实现 4 类问题分类
- 实现最小结构化回答对象
- 补单元测试

完成标准：

- 纯 Python 层可对指定问题返回结构化回答

### 阶段 B：CLI 问答入口

任务：

- 在 CLI 中新增 `chat` 子命令
- 打通最小端到端问答路径
- 补 CLI 测试

完成标准：

- 可以通过命令行直接问答并拿到结果

### 阶段 C：页面抽屉 UI

任务：

- 新增浮动按钮
- 新增抽屉式聊天面板
- 加入消息列表、输入框、发送按钮、快捷问题
- 补渲染测试

完成标准：

- 页面可以展示聊天 UI 壳层

### 阶段 D：页面问答联动

任务：

- 把页面问题与本地问答逻辑接通
- 支持快捷问题
- 支持加载中、失败、降级提示

完成标准：

- 页面内可完成最小问答闭环

### 阶段 E：体验收尾

任务：

- 优化视觉层次
- 优化空状态和错误状态
- 检查移动端表现
- 检查键盘关闭与焦点管理

完成标准：

- 风格与现有产品页面统一

## 问题分类策略

第一版问题分类建议：

- `daily_summary`
- `company_focus`
- `theme_focus`
- `ops_status`
- `out_of_scope`

实现方式：

- 先规则识别
- 必要时由 LLM 参与回答表达
- 不让 LLM 自主决定事实来源

## 输出对象

建议统一返回：

- `answer`
- `question_type`
- `sources_used`
- `follow_up_suggestions`
- `mode_used`

页面和 CLI 都从同一对象渲染。

## 降级策略

- LLM 不可用时，回退规则回答
- 页面问答失败时，不影响日报页面其余内容
- 问题超出当前能力边界时，给出可继续提问的方向

## 测试策略

至少补这些测试：

- 输入层读取本地产物
- 问题分类准确落到 4 类之一
- 回答对象结构稳定
- CLI `chat` 子命令可用
- 页面渲染出浮动入口与抽屉 UI
- 页面失败状态和降级状态可见

## 验证路径

完成实现后至少验证：

```bash
python -m unittest discover -s tests -v
python run_dashboard.py chat --date 2026-05-15 --question "今天最值得关注什么？"
python run_dashboard.py generate-today --output-dir build/site
```

并确认页面中出现：

- 浮动对话入口
- 右侧聊天抽屉
- 快捷问题
- 问答回答结果

