"""V2 项目的集中配置与路径定义。"""

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "data" / "test_cases.jsonl"
PROMPTS_DIR = ROOT_DIR / "prompts"
PROMPT_FILES = {
    "baseline": PROMPTS_DIR / "baseline.txt",
    "optimized": PROMPTS_DIR / "optimized.txt",
}

RESULTS_DIR = ROOT_DIR / "results"
MOCK_RESULTS_DIR = RESULTS_DIR / "mock"
REAL_RESULTS_DIR = RESULTS_DIR / "real"
TEMPLATES_DIR = RESULTS_DIR / "templates"
DATABASE_PATH = RESULTS_DIR / "eval_runs.db"
SQL_SUMMARY_CSV = RESULTS_DIR / "sql_summary.csv"
REPORTS_DIR = ROOT_DIR / "reports"
SQL_SUMMARY_MD = REPORTS_DIR / "sql_summary.md"

# 仅供程序运行时加载本地配置；任何日志都不得输出密钥内容。
load_dotenv(ROOT_DIR / ".env")

# 默认始终使用 Mock。即使本地存在 Key，也必须显式传入 --provider api 才会调用。
DEFAULT_PROVIDER = "mock"
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.getenv("API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini").strip()


def _read_positive_int(name: str, default: int, allow_zero: bool = False) -> int:
    """读取整数配置并尽早报告无效值，但绝不回显敏感配置。"""
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} 必须是整数。") from exc
    minimum = 0 if allow_zero else 1
    if value < minimum:
        raise ValueError(f"{name} 必须大于等于 {minimum}。")
    return value


REQUEST_TIMEOUT_SECONDS = _read_positive_int("REQUEST_TIMEOUT_SECONDS", 60)
MAX_RETRIES = _read_positive_int("MAX_RETRIES", 2, allow_zero=True)
MOCK_MODEL_NAME = "mock/mock-model-v2"


def load_prompt(prompt_version: str) -> str:
    """读取指定版本 Prompt，并在版本无效时给出明确错误。"""
    if prompt_version not in PROMPT_FILES:
        raise ValueError(f"未知 Prompt 版本：{prompt_version}")
    return PROMPT_FILES[prompt_version].read_text(encoding="utf-8").strip()
