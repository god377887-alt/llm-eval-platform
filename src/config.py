"""V1 项目的集中配置与路径定义。"""

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
REPORTS_DIR = ROOT_DIR / "reports"

# 仅从项目根目录读取本地 .env；.env 不应提交到 Git。
load_dotenv(ROOT_DIR / ".env")

PROVIDER_MODE = os.getenv("PROVIDER", "auto").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

MOCK_MODEL_NAME = "mock/mock-model-v1"


def load_prompt(prompt_version: str) -> str:
    """读取指定版本 Prompt，并在版本无效时给出明确错误。"""
    if prompt_version not in PROMPT_FILES:
        raise ValueError(f"未知 Prompt 版本：{prompt_version}")
    return PROMPT_FILES[prompt_version].read_text(encoding="utf-8").strip()

