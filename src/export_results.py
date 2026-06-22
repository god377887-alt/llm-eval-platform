"""导出评测结果与人工复核模板。"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


RESULT_FIELDS = [
    "run_id", "case_id", "category", "title", "model_name", "provider_type",
    "is_mock", "prompt_version", "input", "output", "latency_ms", "status",
    "error_message", "created_at", "input_tokens", "output_tokens", "total_tokens",
    "estimated_cost", "api_attempts", "risk_level", "expected_format", "rule_passed",
    "rule_score", "failed_rules", "badcase_category", "rule_checks",
]


def export_jsonl(results: Iterable[Dict[str, Any]], output_file: Path) -> None:
    """保存包含嵌套规则明细的原始 JSONL。"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")


def export_csv(results: Iterable[Dict[str, Any]], output_file: Path) -> None:
    """保存适合筛选的平面 CSV。"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(_flatten_for_csv(result))


def export_manual_scoring_template(results: List[Dict[str, Any]], output_file: Path) -> None:
    """输出人工评分空白模板，不预填任何虚构人工结论。"""
    fields = [
        "run_id", "case_id", "category", "title", "model_name", "provider_type",
        "is_mock", "prompt_version", "rule_passed", "accuracy_score_1_5",
        "constraint_score_1_5", "format_score_1_5", "safety_score_1_5",
        "overall_score_1_5", "review_status", "reviewer", "comments",
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "run_id": result["run_id"], "case_id": result["case_id"],
                "category": result["category"], "title": result["title"],
                "model_name": result["model_name"], "provider_type": result["provider_type"],
                "is_mock": result["is_mock"], "prompt_version": result["prompt_version"],
                "rule_passed": result["rule_passed"], "review_status": "pending",
            })


def export_badcase_template(results: List[Dict[str, Any]], output_file: Path) -> None:
    """输出 Badcase 分类模板，自动规则仅作为人工复核线索。"""
    fields = [
        "run_id", "case_id", "category", "title", "model_name", "provider_type",
        "is_mock", "prompt_version", "is_badcase_candidate", "auto_badcase_category",
        "auto_failed_rules", "human_badcase_category", "severity", "root_cause",
        "evidence", "recommended_action", "reviewer",
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "run_id": result["run_id"], "case_id": result["case_id"],
                "category": result["category"], "title": result["title"],
                "model_name": result["model_name"], "provider_type": result["provider_type"],
                "is_mock": result["is_mock"], "prompt_version": result["prompt_version"],
                "is_badcase_candidate": "yes" if not result["rule_passed"] else "no",
                "auto_badcase_category": result["badcase_category"],
                "auto_failed_rules": "|".join(result["failed_rules"]),
            })


def _flatten_for_csv(result: Dict[str, Any]) -> Dict[str, Any]:
    """将列表和字典编码为 JSON 字符串，并把未知值保留为空。"""
    flattened: Dict[str, Any] = {}
    for field in RESULT_FIELDS:
        value = result.get(field)
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        flattened[field] = "" if value is None else value
    return flattened
