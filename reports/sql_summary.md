# SQLite / SQL 评测统计报告

> **重要边界：Mock 数据只用于流程验证，不代表真实模型能力、真实成本或 Prompt 优化结论。**

本报告由 `results/eval_runs.db` 中的实际记录通过 SQL 查询生成，Mock 与真实 API 结果始终分组展示。

## 数据总览

| result_source | result_count | run_count | success_count | rule_pass_count |
|---|---|---|---|---|
| mock | 48 | 2 | 48 | 48 |

## 各 Prompt / 类别 / 状态数量

| result_source | provider_type | prompt_version | category | status | result_count |
|---|---|---|---|---|---|
| mock | mock | baseline | JSON 结构化输出 | success | 4 |
| mock | mock | baseline | 事实不确定性 | success | 4 |
| mock | mock | baseline | 复杂条件理解 | success | 4 |
| mock | mock | baseline | 多轮对话约束 | success | 4 |
| mock | mock | baseline | 长文本总结 | success | 4 |
| mock | mock | baseline | 风险边界 | success | 4 |
| mock | mock | optimized | JSON 结构化输出 | success | 4 |
| mock | mock | optimized | 事实不确定性 | success | 4 |
| mock | mock | optimized | 复杂条件理解 | success | 4 |
| mock | mock | optimized | 多轮对话约束 | success | 4 |
| mock | mock | optimized | 长文本总结 | success | 4 |
| mock | mock | optimized | 风险边界 | success | 4 |

## 平均延迟、规则得分与通过率

| result_source | provider_type | prompt_version | category | avg_latency_ms | avg_rule_score | rule_pass_rate_pct | result_count |
|---|---|---|---|---|---|---|---|
| mock | mock | baseline | JSON 结构化输出 | 0.014 | 1.0 | 100.0 | 4 |
| mock | mock | baseline | 事实不确定性 | 0.014 | 1.0 | 100.0 | 4 |
| mock | mock | baseline | 复杂条件理解 | 0.029 | 1.0 | 100.0 | 4 |
| mock | mock | baseline | 多轮对话约束 | 0.015 | 1.0 | 100.0 | 4 |
| mock | mock | baseline | 长文本总结 | 0.015 | 1.0 | 100.0 | 4 |
| mock | mock | baseline | 风险边界 | 0.014 | 1.0 | 100.0 | 4 |
| mock | mock | optimized | JSON 结构化输出 | 0.015 | 1.0 | 100.0 | 4 |
| mock | mock | optimized | 事实不确定性 | 0.015 | 1.0 | 100.0 | 4 |
| mock | mock | optimized | 复杂条件理解 | 0.025 | 1.0 | 100.0 | 4 |
| mock | mock | optimized | 多轮对话约束 | 0.014 | 1.0 | 100.0 | 4 |
| mock | mock | optimized | 长文本总结 | 0.015 | 1.0 | 100.0 | 4 |
| mock | mock | optimized | 风险边界 | 0.015 | 1.0 | 100.0 | 4 |

规则通过率仅表示基础格式与约束规则是否触发，不能替代人工质量判断。

## 失败或规则未通过案例

没有查询到失败或规则未通过案例。

## 最慢的 10 条结果

| result_source | run_id | case_id | category | prompt_version | model_name | latency_ms | status |
|---|---|---|---|---|---|---|---|
| mock | 8dedf49e-c2ac-4080-b5c3-bd1ce5b83300 | complex_001 | 复杂条件理解 | baseline | mock/mock-model-v2 | 0.062 | success |
| mock | a0c64d08-eefe-4a79-b695-f6d0b4f7fe77 | complex_001 | 复杂条件理解 | optimized | mock/mock-model-v2 | 0.05 | success |
| mock | 8dedf49e-c2ac-4080-b5c3-bd1ce5b83300 | complex_002 | 复杂条件理解 | baseline | mock/mock-model-v2 | 0.022 | success |
| mock | a0c64d08-eefe-4a79-b695-f6d0b4f7fe77 | complex_002 | 复杂条件理解 | optimized | mock/mock-model-v2 | 0.019 | success |
| mock | a0c64d08-eefe-4a79-b695-f6d0b4f7fe77 | summary_001 | 长文本总结 | optimized | mock/mock-model-v2 | 0.018 | success |
| mock | a0c64d08-eefe-4a79-b695-f6d0b4f7fe77 | complex_003 | 复杂条件理解 | optimized | mock/mock-model-v2 | 0.017 | success |
| mock | 8dedf49e-c2ac-4080-b5c3-bd1ce5b83300 | complex_003 | 复杂条件理解 | baseline | mock/mock-model-v2 | 0.016 | success |
| mock | 8dedf49e-c2ac-4080-b5c3-bd1ce5b83300 | multiturn_004 | 多轮对话约束 | baseline | mock/mock-model-v2 | 0.016 | success |
| mock | a0c64d08-eefe-4a79-b695-f6d0b4f7fe77 | json_002 | JSON 结构化输出 | optimized | mock/mock-model-v2 | 0.016 | success |
| mock | a0c64d08-eefe-4a79-b695-f6d0b4f7fe77 | uncertain_002 | 事实不确定性 | optimized | mock/mock-model-v2 | 0.016 | success |

**Mock 数据只用于流程验证，不代表真实模型能力、真实成本或 Prompt 优化结论。**
