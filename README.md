# 多模型中文复杂任务评测平台 V2

一个轻量、可追踪的中文 LLM 评测流水线。V2 保留 24 条测试题、双 Prompt、MockProvider、规则评测和图表报告，并新增显式真实 API 安全门槛、SQLite 运行存储与 SQL 统计报告。

> **仓库内 Mock 结果仅用于验证工程流程，不代表真实模型能力、真实成本或 Prompt 优化结论。**

## 核心能力

- 24 条中文复杂任务，覆盖 6 类场景，每类 4 条。
- `baseline` 与 `optimized` 双 Prompt，一次完整 Mock 运行生成 48 条结果。
- 默认 Provider 固定为 `mock`；即使本地存在 Key，也不会自动调用真实接口。
- 真实接口只能通过 `--provider api` 显式触发，支持超时、有限重试、错误与延迟记录。
- 解析接口明确返回的 token usage；接口未返回时留空。
- 成本字段已预留；没有明确价格配置时留空，不做估算。
- JSON、字段、长度、格式、不确定性与风险拒绝等基础规则检查。
- 同步导出 JSONL、CSV 和 SQLite，并通过真实 SQL 生成统计报告。

## 数据流

```text
test_cases.jsonl + Prompt
        ↓
MockProvider（默认）或 API Provider（显式）
        ↓
rule_evaluator
        ↓
JSONL / CSV + SQLite
        ↓
Mock 图表报告 + SQL 汇总报告
```

## 目录结构

```text
llm-eval-platform/
├─ data/test_cases.jsonl
├─ prompts/{baseline,optimized}.txt
├─ src/
│  ├─ config.py
│  ├─ providers.py
│  ├─ rule_evaluator.py
│  ├─ database.py
│  ├─ export_results.py
│  ├─ run_eval.py
│  ├─ analyze_results.py
│  └─ generate_sql_report.py
├─ tests/test_v2_pipeline.py
├─ results/
│  ├─ mock/{raw_results.jsonl,results.csv}
│  ├─ templates/
│  ├─ eval_runs.db
│  └─ sql_summary.csv
└─ reports/
   ├─ mock_summary.md
   ├─ mock_result_overview.png
   ├─ mock_badcase_distribution.png
   └─ sql_summary.md
```

## 测试集与评测维度

| 类别 | 数量 | 主要验证点 |
|---|---:|---|
| 复杂条件理解 | 4 | 多约束、组合、排序、预算 |
| 长文本总结 | 4 | 信息压缩、数字、长度与行数 |
| JSON 结构化输出 | 4 | JSON 有效性与字段完整性 |
| 事实不确定性 | 4 | 信息不足与来源核验 |
| 多轮对话约束 | 4 | 跨轮约束与最新指令 |
| 风险边界 | 4 | 安全拒绝与替代建议 |

每条结果记录运行批次、Provider、模型名、Prompt、输入输出、状态、错误、延迟、规则得分、规则明细、usage、成本占位和时间戳。基础规则只用于预筛，不能替代人工语义与事实评审。

## SQLite 表

- `runs`：每个 Prompt 版本的一次运行批次，记录 `run_id`、起止时间、Provider、模型、Prompt、Mock 标记、结果数和状态。
- `eval_results`：逐条结果、规则得分、失败规则 JSON、完整规则检查 JSON、延迟、错误、usage 与成本占位。

规则明细以 JSON 字段保存，可追溯某条结果为何通过或失败；常用维度已建立索引。

## 安全运行 Mock 模式

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe .\src\run_eval.py --provider mock --prompt-version all
.\.venv\Scripts\python.exe .\src\generate_sql_report.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`--limit N` 限制测试题数量；双 Prompt 时，每个 Prompt 各运行 N 条。

## 将来安全配置真实 API

1. 复制 `.env.example` 为 `.env`。
2. 仅在本机手动填写 `API_BASE_URL`、`API_KEY`、`MODEL_NAME`、`REQUEST_TIMEOUT_SECONDS`、`MAX_RETRIES`。
3. 确认 `.env` 未被 Git 跟踪。
4. 首次只运行少量题：

```powershell
.\.venv\Scripts\python.exe .\src\run_eval.py --provider api --prompt-version baseline --limit 2
```

缺少 `API_KEY` 时，API 模式会明确报错并停止，不会静默回退。真实输出进入已被 Git 忽略的 `results/real/`；数据库仍以 `is_mock=0` 与 Mock 数据分开统计。

## 输出文件

- `results/mock/raw_results.jsonl`：包含规则嵌套明细的 Mock 原始结果。
- `results/mock/results.csv`：可筛选的 Mock 平面结果。
- `results/eval_runs.db`：运行与逐条结果的 SQLite 数据库。
- `results/sql_summary.csv`：多组 SQL 查询的统一 CSV 输出。
- `reports/sql_summary.md`：数量、平均延迟、规则通过率、失败案例和最慢案例。
- `results/templates/`：人工评分与 Badcase 空白模板。
- `reports/mock_*.png`、`reports/mock_summary.md`：Mock 流程展示产物。

## Mock 与真实 API 的区别

| 项目 | MockProvider | API Provider |
|---|---|---|
| 是否联网 | 否 | 是，仅显式触发 |
| 是否需要 Key | 否 | 是 |
| 输出来源 | 本地固定模拟回答 | 配置的兼容接口 |
| usage / 成本 | 留空 | usage 按接口返回；成本无价格时留空 |
| 能否评价模型 | 不能 | 仍需真实运行与人工复核 |

## 当前局限

- 尚未运行真实模型，因此不得根据 Mock 结果评价模型或 Prompt。
- Mock 对两个 Prompt 返回同一组固定答案，不能证明 optimized 优于 baseline。
- 规则评测不能判断深层语义正确性、事实真实性或回答风格质量。
- 当前 API 实现面向 Chat Completions 兼容结构，未实现并发、限流或厂商特有字段。
- 成本只预留字段；在没有明确、可审计价格配置时不会估算。

## 后续计划

- 经人工确认后使用 `--limit` 做小规模真实 API 试跑。
- 增加可审计的模型价格配置与成本计算。
- 扩展人工评分流程、JSON Schema 和跨模型对比。
- 在不混淆 Mock/真实数据的前提下增加可视化仪表盘。
