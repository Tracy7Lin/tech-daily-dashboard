# 科技日报编辑质量增强实施计划

## 目标

通过新增 `editorial.py`，把首页与主题对比提升为更接近行业分析博客的写法，同时保持单条新闻仍然是高质量简报。

## 修改范围

- 新增：`src/tech_daily/editorial.py`
- 修改：`src/tech_daily/topics.py`
- 修改：`src/tech_daily/pipeline.py`
- 新增或修改测试：
  - `tests/test_editorial.py`
  - `tests/test_pipeline.py`
  - `tests/test_topics.py`

## 执行步骤

### 1. 先补失败测试

- headline 应体现“核心信号”而不是只报数字
- 主题簇 summary 应体现主题内的实际重心
- comparison 不应直接输出内部分类名
- trend 应体现行业方向，而不是模板句

### 2. 实现 `editorial.py`

- 公司切入点判定
- 主题 summary / comparison / trend 生成
- 日报 headline 生成

### 3. 接入原有流程

- `topics.py` 负责聚类，调用 editorial 产出表达
- `pipeline.py` 使用 editorial 生成日报 headline

### 4. 验证

- `python -m unittest discover -s tests -v`
- `python run_dashboard.py backfill --end-date 2026-05-11 --days 7 --output-dir build/site`
- 抽查首页与非空日报详情页

## 风险控制

- 不改变 `DailyReport` / `TopicCluster` 数据结构
- 不让 `editorial.py` 依赖渲染层
- 保持表达规则可测试、可维护、可替换
