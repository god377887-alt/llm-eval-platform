"""V1 评测入口：批量运行双 Prompt、规则检查并生成全部产物。"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

from analyze_results import generate_artifacts
from config import (
    DATA_FILE,
    MOCK_MODEL_NAME,
    MOCK_RESULTS_DIR,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    PROMPT_FILES,
    PROVIDER_MODE,
    REAL_RESULTS_DIR,
    REQUEST_TIMEOUT_SECONDS,
    load_prompt,
)
from export_results import export_csv, export_jsonl
from providers import create_provider, load_test_cases
from rule_evaluator import evaluate_output


def run_evaluation(provider_name: str, prompt_choice: str) -> tuple[List[Dict[str, Any]], Path]:
    """运行测试集并返回完整结果与实际输出目录。"""
    provider, fallback_reason = create_provider(
        requested_provider=provider_name,
        data_file=DATA_FILE,
        mock_model_name=MOCK_MODEL_NAME,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        openai_model=OPENAI_MODEL,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
    if fallback_reason:
        print(fallback_reason)

    test_cases = (
        provider.load_test_cases()
        if getattr(provider, "is_mock", False)
        else load_test_cases(DATA_FILE)
    )
    prompt_versions = (
        list(PROMPT_FILES.keys()) if prompt_choice == "all" else [prompt_choice]
    )
    results: List[Dict[str, Any]] = []

    for prompt_version in prompt_versions:
        prompt_text = load_prompt(prompt_version)
        for test_case in test_cases:
            started_at = perf_counter()
            output = ""
            status = "success"
            error_message = ""
            try:
                output = provider.generate(test_case, prompt_text, prompt_version)
            except Exception as exc:  # 保留错误记录，避免单条失败中断批次。
                status = "error"
                error_message = str(exc)

            latency_ms = round((perf_counter() - started_at) * 1000, 3)
            rule_result = evaluate_output(test_case, output)
            results.append(
                {
                    "case_id": test_case["case_id"],
                    "category": test_case["category"],
                    "title": test_case["title"],
                    "model_name": provider.model_name,
                    "provider_type": provider.provider_type,
                    "is_mock": provider.is_mock,
                    "prompt_version": prompt_version,
                    "input": test_case["input"],
                    "output": output,
                    "latency_ms": latency_ms,
                    "status": status,
                    "error_message": error_message,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "risk_level": test_case["risk_level"],
                    "expected_format": test_case["expected_format"],
                    **rule_result,
                }
            )

    output_dir = MOCK_RESULTS_DIR if provider.is_mock else REAL_RESULTS_DIR
    export_jsonl(results, output_dir / "raw_results.jsonl")
    export_csv(results, output_dir / "results.csv")
    report_prefix = "mock" if provider.is_mock else "real"
    generate_artifacts(results, report_prefix)
    return results, output_dir


def parse_args() -> argparse.Namespace:
    """解析命令行参数，默认自动选择 Provider 并运行双 Prompt。"""
    parser = argparse.ArgumentParser(description="多模型中文复杂任务评测平台 V1")
    parser.add_argument(
        "--provider",
        choices=["auto", "mock", "openai"],
        default=PROVIDER_MODE if PROVIDER_MODE in {"auto", "mock", "openai"} else "auto",
    )
    parser.add_argument(
        "--prompt-version",
        choices=["all", "baseline", "optimized"],
        default="all",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    evaluation_results, result_dir = run_evaluation(
        arguments.provider, arguments.prompt_version
    )
    success_count = sum(item["status"] == "success" for item in evaluation_results)
    mock_label = "是" if evaluation_results and evaluation_results[0]["is_mock"] else "否"
    print(f"评测完成：共 {len(evaluation_results)} 条，执行成功 {success_count} 条。")
    print(f"Mock 结果：{mock_label}")
    print(f"结果目录：{result_dir}")

