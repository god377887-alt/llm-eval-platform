# Learning Log

## V2：API 就绪、SQLite 与 SQL 报告

### 已完成

- 保留 24 条测试题、双 Prompt、MockProvider、规则评测与原有展示产物。
- 默认 Provider 固定为 Mock，真实 API 只能由 `--provider api` 显式触发。
- API Provider 支持超时、有限重试、错误、延迟、模型名及可选 token usage 记录。
- 未返回 usage 时留空；未配置明确价格时成本字段留空。
- 新增 `--limit N`，支持未来低风险小批量试跑。
- 使用 Python 内置 `sqlite3` 保存运行批次、逐条结果与可追溯规则明细。
- 使用真实 SQL 生成 CSV 与 Markdown 统计报告，并区分 Mock 与 API 数据。
- 增加 unittest，覆盖无网络 Mock、48 条完整运行、CSV/SQLite 一致性、SQL 报告和缺 Key 报错。

### 尚未完成

- 未调用任何真实模型 API，未产生真实模型结果或费用。
- 未进行人工评分，因此不能评价模型质量或 Prompt 优化效果。
- 未配置可审计的模型价格表，成本字段不做估算。
- 尚未实现并发、限流、语义评测器或跨模型统计显著性分析。

### 当前结论边界

仓库中的 Mock 数据仅证明评测、规则、导出、数据库与报告链路可以运行，不代表真实模型能力、真实成本或 Prompt 优化结论。
