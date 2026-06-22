"""从 SQLite 执行真实 SQL 聚合并生成 CSV 与 Markdown 报告。"""

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from config import DATABASE_PATH, SQL_SUMMARY_CSV, SQL_SUMMARY_MD


DISCLAIMER = (
    "Mock 数据只用于流程验证，不代表真实模型能力、真实成本或 Prompt 优化结论。"
)


def _fetch(connection: sqlite3.Connection, sql: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
    """执行只读 SQL 并返回字典列表。"""
    cursor = connection.execute(sql, parameters)
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def generate_sql_report(
    database_path: Path = DATABASE_PATH,
    csv_path: Path = SQL_SUMMARY_CSV,
    markdown_path: Path = SQL_SUMMARY_MD,
) -> Dict[str, List[Dict[str, Any]]]:
    """生成分组统计、未通过案例与最慢结果，并明确区分 Mock/API。"""
    if not database_path.exists():
        raise FileNotFoundError(f"SQLite 数据库不存在：{database_path}")
    with sqlite3.connect(database_path) as connection:
        datasets = {
            "counts": _fetch(connection, """
                SELECT CASE WHEN is_mock = 1 THEN 'mock' ELSE 'api' END AS result_source,
                       provider_type, prompt_version, category, status,
                       COUNT(*) AS result_count
                FROM eval_results
                GROUP BY is_mock, provider_type, prompt_version, category, status
                ORDER BY is_mock DESC, provider_type, prompt_version, category, status
            """),
            "performance": _fetch(connection, """
                SELECT CASE WHEN is_mock = 1 THEN 'mock' ELSE 'api' END AS result_source,
                       provider_type, prompt_version, category,
                       ROUND(AVG(latency_ms), 3) AS avg_latency_ms,
                       ROUND(AVG(rule_score), 4) AS avg_rule_score,
                       ROUND(100.0 * AVG(rule_passed), 2) AS rule_pass_rate_pct,
                       COUNT(*) AS result_count
                FROM eval_results
                GROUP BY is_mock, provider_type, prompt_version, category
                ORDER BY is_mock DESC, provider_type, prompt_version, category
            """),
            "failures": _fetch(connection, """
                SELECT CASE WHEN is_mock = 1 THEN 'mock' ELSE 'api' END AS result_source,
                       run_id, case_id, category, prompt_version, status,
                       rule_score, failed_rules_json, error_message
                FROM eval_results
                WHERE status <> 'success' OR rule_passed = 0
                ORDER BY is_mock DESC, prompt_version, category, case_id
            """),
            "slowest": _fetch(connection, """
                SELECT CASE WHEN is_mock = 1 THEN 'mock' ELSE 'api' END AS result_source,
                       run_id, case_id, category, prompt_version, model_name,
                       latency_ms, status
                FROM eval_results
                ORDER BY latency_ms DESC
                LIMIT 10
            """),
            "totals": _fetch(connection, """
                SELECT CASE WHEN is_mock = 1 THEN 'mock' ELSE 'api' END AS result_source,
                       COUNT(*) AS result_count,
                       COUNT(DISTINCT run_id) AS run_count,
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                       SUM(CASE WHEN rule_passed = 1 THEN 1 ELSE 0 END) AS rule_pass_count
                FROM eval_results
                GROUP BY is_mock
                ORDER BY is_mock DESC
            """),
        }

    _write_csv(datasets, csv_path)
    _write_markdown(datasets, markdown_path)
    return datasets


def _write_csv(datasets: Dict[str, List[Dict[str, Any]]], output_file: Path) -> None:
    """将多组 SQL 查询输出为具有统一列集合的 CSV。"""
    rows: List[Dict[str, Any]] = []
    fieldnames = ["section"]
    for section, items in datasets.items():
        for item in items:
            row = {"section": section, **item}
            rows.append(row)
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(datasets: Dict[str, List[Dict[str, Any]]], output_file: Path) -> None:
    """写入适合 GitHub 阅读的 SQL 统计报告。"""
    lines = [
        "# SQLite / SQL 评测统计报告", "",
        f"> **重要边界：{DISCLAIMER}**", "",
        "本报告由 `results/eval_runs.db` 中的实际记录通过 SQL 查询生成，Mock 与真实 API 结果始终分组展示。", "",
        "## 数据总览", "",
        _markdown_table(datasets["totals"]), "",
        "## 各 Prompt / 类别 / 状态数量", "",
        _markdown_table(datasets["counts"]), "",
        "## 平均延迟、规则得分与通过率", "",
        _markdown_table(datasets["performance"]), "",
        "规则通过率仅表示基础格式与约束规则是否触发，不能替代人工质量判断。", "",
        "## 失败或规则未通过案例", "",
        _markdown_table(datasets["failures"], empty_text="没有查询到失败或规则未通过案例。"), "",
        "## 最慢的 10 条结果", "",
        _markdown_table(datasets["slowest"]), "",
        f"**{DISCLAIMER}**", "",
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")


def _markdown_table(rows: List[Dict[str, Any]], empty_text: str = "暂无数据。") -> str:
    """把查询结果安全转换为 Markdown 表格。"""
    if not rows:
        return empty_text
    headers = list(rows[0])
    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        values = [str(row.get(header, "")).replace("|", "\\|").replace("\n", " ") for header in headers]
        output.append("| " + " | ".join(values) + " |")
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="从 SQLite 生成 SQL 统计报告。")
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--csv", type=Path, default=SQL_SUMMARY_CSV)
    parser.add_argument("--markdown", type=Path, default=SQL_SUMMARY_MD)
    args = parser.parse_args()
    datasets = generate_sql_report(args.database, args.csv, args.markdown)
    total = sum(item["result_count"] for item in datasets["totals"])
    print(f"SQL 报告已生成，数据库当前包含 {total} 条结果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
