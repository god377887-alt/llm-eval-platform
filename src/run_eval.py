"""V2 评测入口：显式 Provider、双 Prompt、规则检查与多格式持久化。"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from analyze_results import generate_artifacts
from config import (
    API_BASE_URL,
    API_KEY,
    DATABASE_PATH,
    DATA_FILE,
    DEFAULT_PROVIDER,
    MAX_RETRIES,
    MOCK_MODEL_NAME,
    MOCK_RESULTS_DIR,
    MODEL_NAME,
    PROMPT_FILES,
    REAL_RESULTS_DIR,
    REQUEST_TIMEOUT_SECONDS,
    load_prompt,
)
from database import finish_run, save_results, start_run
from export_results import export_csv, export_jsonl
from providers import (
    ConfigurationError,
    ProviderRequestError,
    ProviderResponse,
    create_provider,
    load_test_cases,
)
from rule_evaluator import evaluate_output


def utc_now() -> str:
    """返回统一的 UTC ISO 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def run_evaluation(
    provider_name: str,
    prompt_choice: str,
    limit: Optional[int] = None,
    output_dir: Optional[Path] = None,
    database_path: Optional[Path] = None,
    generate_analysis: bool = True,
) -> Tuple[List[Dict[str, Any]], Path, List[str]]:
    """运行测试并同时写入 JSONL、CSV 与 SQLite。"""
    if limit is not None and limit <= 0:
        raise ValueError("--limit 必须是大于 0 的整数。")

    provider = create_provider(
        requested_provider=provider_name,
        data_file=DATA_FILE,
        mock_model_name=MOCK_MODEL_NAME,
        api_key=API_KEY,
        base_url=API_BASE_URL,
        api_model=MODEL_NAME,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    )
    test_cases = (
        provider.load_test_cases()
        if getattr(provider, "is_mock", False)
        else load_test_cases(DATA_FILE)
    )
    if limit is not None:
        test_cases = test_cases[:limit]

    prompt_versions = list(PROMPT_FILES) if prompt_choice == "all" else [prompt_choice]
    target_dir = output_dir or (MOCK_RESULTS_DIR if provider.is_mock else REAL_RESULTS_DIR)
    target_database = database_path or DATABASE_PATH
    results: List[Dict[str, Any]] = []
    run_ids: List[str] = []

    for prompt_version in prompt_versions:
        run_id = str(uuid4())
        run_ids.append(run_id)
        started_at = utc_now()
        start_run(target_database, {
            "run_id": run_id,
            "started_at": started_at,
            "provider": provider.provider_type,
            "model_name": provider.model_name,
            "prompt_version": prompt_version,
            "is_mock": provider.is_mock,
        })
        prompt_text = load_prompt(prompt_version)
        prompt_results: List[Dict[str, Any]] = []

        for test_case in test_cases:
            timer = perf_counter()
            response = ProviderResponse(output="")
            status = "success"
            error_message = ""
            try:
                response = provider.generate(test_case, prompt_text, prompt_version)
            except Exception as exc:  # 单条失败需记录，不能中断整个批次。
                status = "error"
                error_message = str(exc)
                response.attempts = getattr(exc, "attempts", 1)

            latency_ms = round((perf_counter() - timer) * 1000, 3)
            rule_result = evaluate_output(test_case, response.output)
            result = {
                "run_id": run_id,
                "case_id": test_case["case_id"],
                "category": test_case["category"],
                "title": test_case["title"],
                "model_name": provider.model_name,
                "provider_type": provider.provider_type,
                "is_mock": provider.is_mock,
                "prompt_version": prompt_version,
                "input": test_case["input"],
                "output": response.output,
                "latency_ms": latency_ms,
                "status": status,
                "error_message": error_message,
                "created_at": utc_now(),
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "total_tokens": response.total_tokens,
                "estimated_cost": response.estimated_cost,
                "api_attempts": response.attempts,
                "risk_level": test_case["risk_level"],
                "expected_format": test_case["expected_format"],
                **rule_result,
            }
            prompt_results.append(result)
            results.append(result)

        save_results(target_database, prompt_results)
        run_status = "completed" if all(
            item["status"] == "success" for item in prompt_results
        ) else "completed_with_errors"
        finish_run(target_database, run_id, utc_now(), len(prompt_results), run_status)

    export_jsonl(results, target_dir / "raw_results.jsonl")
    export_csv(results, target_dir / "results.csv")
    if generate_analysis:
        generate_artifacts(results, "mock" if provider.is_mock else "real")
    return results, target_dir, run_ids


def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器；默认 Provider 固定为 mock。"""
    parser = argparse.ArgumentParser(description="多模型中文复杂任务评测平台 V2")
    parser.add_argument(
        "--provider",
        choices=["mock", "api"],
        default=DEFAULT_PROVIDER,
        help="默认 mock；只有显式 api 才可能发起真实请求。",
    )
    parser.add_argument(
        "--prompt-version",
        choices=["all", "baseline", "optimized"],
        default="all",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="只运行前 N 条测试题；在双 Prompt 模式下每个 Prompt 各运行 N 条。",
    )
    return parser


def main() -> int:
    """运行 CLI，并把配置错误转成清晰的非零退出信息。"""
    arguments = build_parser().parse_args()
    try:
        evaluation_results, result_dir, run_ids = run_evaluation(
            arguments.provider, arguments.prompt_version, arguments.limit
        )
    except (ConfigurationError, ValueError) as exc:
        print(f"配置错误：{exc}")
        return 2

    success_count = sum(item["status"] == "success" for item in evaluation_results)
    mock_label = "是" if evaluation_results and evaluation_results[0]["is_mock"] else "否"
    print(f"评测完成：共 {len(evaluation_results)} 条，执行成功 {success_count} 条。")
    print(f"Mock 结果：{mock_label}")
    print(f"运行批次：{', '.join(run_ids)}")
    print(f"结果目录：{result_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
