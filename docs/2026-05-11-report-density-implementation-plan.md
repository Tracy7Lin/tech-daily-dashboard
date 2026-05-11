# 科技日报信息密度增强实施计划

## 目标

在不调整核心数据流的前提下，通过渲染层增强同时完成：

- 首页可读性提升
- 日报详情页信息密度提升

## 范围

只修改以下文件：

- `src/tech_daily/render.py`
- `templates/index.html`
- `templates/daily.html`
- `tests/test_render.py`

必要时允许在 `render.py` 内新增小型辅助函数，但不扩散到分类、主题、流水线模块。

## 执行步骤

### 1. 为渲染增强补失败测试

- 首页应出现 `重点观察`
- 主题卡应显示公司数 / 条目数 / 代表事件摘要
- 公司卡应显示来源、发布时间、分类、对比角度与原始补充说明
- 详情页应渲染重点观察区块

### 2. 在 `render.py` 实现派生展示

- 增加全局重点观察选择逻辑
- 增加原始摘要 HTML 清洗和长度控制
- 增加时间与元信息格式化
- 扩展主题卡与公司卡的 HTML 生成

### 3. 更新模板

- 首页插入重点观察区块
- 详情页插入重点观察区块
- 为高信息密度布局增加必要样式

### 4. 验证

- `python -m unittest discover -s tests -v`
- `python run_dashboard.py backfill --end-date 2026-05-11 --days 7 --output-dir build/site`
- 抽查生成的 `build/site/index.html` 与单日日报页面

## 风险控制

- 避免在模板中嵌入复杂逻辑，复杂选择全部留在 `render.py`
- 不改变 `DailyReport` 模型，避免影响 JSON 兼容性
- 所有新增展示都允许在原始数据缺失时优雅降级
