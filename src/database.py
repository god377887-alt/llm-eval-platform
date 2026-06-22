"""使用 Python 内置 sqlite3 持久化评测运行与逐条结果。"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    is_mock INTEGER NOT NULL CHECK (is_mock IN (0, 1)),
    result_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS eval_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    error_message TEXT NOT NULL,
    rule_passed INTEGER NOT NULL CHECK (rule_passed IN (0, 1)),
    rule_score REAL NOT NULL,
    failed_rules_json TEXT NOT NULL,
    rule_checks_json TEXT NOT NULL,
    badcase_category TEXT NOT NULL,
    created_at TEXT NOT NULL,
    model_name TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    is_mock INTEGER NOT NULL CHECK (is_mock IN (0, 1)),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost REAL,
    api_attempts INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_eval_results_run_id
    ON eval_results(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_dimensions
    ON eval_results(is_mock, prompt_version, category, status);
"""


def initialize_database(database_path: Path) -> None:
    """创建数据库目录、表与索引。"""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(SCHEMA_SQL)


def start_run(database_path: Path, run: Dict[str, Any]) -> None:
    """登记一个 Prompt 版本的运行批次。"""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO runs (
                run_id, started_at, provider, model_name, prompt_version, is_mock
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run["run_id"],
                run["started_at"],
                run["provider"],
                run["model_name"],
                run["prompt_version"],
                int(run["is_mock"]),
            ),
        )


def save_results(database_path: Path, results: Iterable[Dict[str, Any]]) -> int:
    """批量写入结果；规则明细以 JSON 保存以便逐条追溯。"""
    rows = list(results)
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO eval_results (
                run_id, case_id, category, title, prompt_version,
                input_text, output_text, status, latency_ms, error_message,
                rule_passed, rule_score, failed_rules_json, rule_checks_json,
                badcase_category, created_at, model_name, provider_type, is_mock,
                input_tokens, output_tokens, total_tokens, estimated_cost, api_attempts
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    item["run_id"], item["case_id"], item["category"], item["title"],
                    item["prompt_version"], item["input"], item["output"], item["status"],
                    item["latency_ms"], item["error_message"], int(item["rule_passed"]),
                    item["rule_score"], json.dumps(item["failed_rules"], ensure_ascii=False),
                    json.dumps(item["rule_checks"], ensure_ascii=False),
                    item["badcase_category"], item["created_at"], item["model_name"],
                    item["provider_type"], int(item["is_mock"]), item.get("input_tokens"),
                    item.get("output_tokens"), item.get("total_tokens"),
                    item.get("estimated_cost"), item.get("api_attempts", 1),
                )
                for item in rows
            ],
        )
    return len(rows)


def finish_run(
    database_path: Path,
    run_id: str,
    completed_at: str,
    result_count: int,
    status: str,
) -> None:
    """完成运行批次并记录结果数量与总体状态。"""
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE runs
            SET completed_at = ?, result_count = ?, status = ?
            WHERE run_id = ?
            """,
            (completed_at, result_count, status, run_id),
        )
