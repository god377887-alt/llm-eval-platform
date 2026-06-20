# MockProvider 流程验证摘要

> **⚠️ 本报告基于 MockProvider 流程验证，不代表真实模型评测结论。**

## 运行概览

- 生成时间（UTC）：2026-06-20T12:46:35.753195+00:00
- Provider：`mock`
- 记录数：48
- 执行成功记录：48
- Prompt 版本：baseline, optimized
- 基础规则标记待复核记录：0

以上数字仅验证批处理、记录、规则与导出流程是否工作，不是模型成功率或效果结论。

## 分类覆盖

| 测试类别 | 运行记录 | 执行成功 | 规则标记待复核 |
|---|---:|---:|---:|
| 复杂条件理解 | 8 | 8 | 0 |
| 长文本总结 | 8 | 8 | 0 |
| JSON 结构化输出 | 8 | 8 | 0 |
| 事实不确定性 | 8 | 8 | 0 |
| 多轮对话约束 | 8 | 8 | 0 |
| 风险边界 | 8 | 8 | 0 |

## 产物说明

- `results/mock/raw_results.jsonl`：保留嵌套规则明细的 Mock 原始记录。
- `results/mock/results.csv`：便于筛选的平面结果。
- `results/templates/manual_scoring_template.csv`：人工评分空白模板。
- `results/templates/badcase_template.csv`：Badcase 人工分类模板。

## 结论边界

**本报告基于 MockProvider 流程验证，不代表真实模型评测结论。** 未配置真实 API 时，不比较模型能力，也不声称 Prompt 优化有效。
