"""生成 Mock 流程摘要、人工模板与展示图表。"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import REPORTS_DIR, TEMPLATES_DIR
from export_results import export_badcase_template, export_manual_scoring_template


MOCK_DISCLAIMER = "本报告基于 MockProvider 流程验证，不代表真实模型评测结论。"


def generate_artifacts(results: List[Dict[str, Any]], report_prefix: str) -> None:
    """根据结果生成模板、Markdown 摘要和两张 PNG 图。"""
    export_manual_scoring_template(
        results, TEMPLATES_DIR / "manual_scoring_template.csv"
    )
    export_badcase_template(results, TEMPLATES_DIR / "badcase_template.csv")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = REPORTS_DIR / f"{report_prefix}_summary.md"
    overview_path = REPORTS_DIR / f"{report_prefix}_result_overview.png"
    badcase_path = REPORTS_DIR / f"{report_prefix}_badcase_distribution.png"

    _write_summary(results, summary_path)
    _plot_overview(results, overview_path)
    _plot_badcases(results, badcase_path)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """从原始 JSONL 载入结果，供分析脚本独立运行。"""
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _write_summary(results: List[Dict[str, Any]], output_file: Path) -> None:
    """报告只描述流程覆盖与规则触发，不推断模型质量。"""
    by_category: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_category[result["category"]].append(result)

    status_success = sum(result["status"] == "success" for result in results)
    rule_flagged = sum(not result["rule_passed"] for result in results)
    prompt_versions = sorted({result["prompt_version"] for result in results})
    lines = [
        "# MockProvider 流程验证摘要",
        "",
        f"> **⚠️ {MOCK_DISCLAIMER}**",
        "",
        "## 运行概览",
        "",
        f"- 生成时间（UTC）：{datetime.now(timezone.utc).isoformat()}",
        f"- Provider：`mock`",
        f"- 记录数：{len(results)}",
        f"- 执行成功记录：{status_success}",
        f"- Prompt 版本：{', '.join(prompt_versions)}",
        f"- 基础规则标记待复核记录：{rule_flagged}",
        "",
        "以上数字仅验证批处理、记录、规则与导出流程是否工作，不是模型成功率或效果结论。",
        "",
        "## 分类覆盖",
        "",
        "| 测试类别 | 运行记录 | 执行成功 | 规则标记待复核 |",
        "|---|---:|---:|---:|",
    ]
    for category, items in by_category.items():
        lines.append(
            f"| {category} | {len(items)} | "
            f"{sum(item['status'] == 'success' for item in items)} | "
            f"{sum(not item['rule_passed'] for item in items)} |"
        )
    lines.extend(
        [
            "",
            "## 产物说明",
            "",
            "- `results/mock/raw_results.jsonl`：保留嵌套规则明细的 Mock 原始记录。",
            "- `results/mock/results.csv`：便于筛选的平面结果。",
            "- `results/templates/manual_scoring_template.csv`：人工评分空白模板。",
            "- `results/templates/badcase_template.csv`：Badcase 人工分类模板。",
            "",
            "## 结论边界",
            "",
            f"**{MOCK_DISCLAIMER}** 未配置真实 API 时，不比较模型能力，也不声称 Prompt 优化有效。",
        ]
    )
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _configure_plot_style() -> None:
    """优先使用 Windows 中文字体，并保持图表简洁。"""
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def _plot_overview(results: List[Dict[str, Any]], output_file: Path) -> None:
    """展示每个类别在两个 Prompt 版本下的流程运行覆盖数。"""
    _configure_plot_style()
    categories = list(dict.fromkeys(result["category"] for result in results))
    prompts = sorted({result["prompt_version"] for result in results})
    counts = Counter((result["category"], result["prompt_version"]) for result in results)

    x_values = list(range(len(categories)))
    width = 0.36
    fig, ax = plt.subplots(figsize=(12, 6.8))
    colors = ["#2563EB", "#0F766E"]
    for index, prompt in enumerate(prompts):
        offset = (index - (len(prompts) - 1) / 2) * width
        values = [counts[(category, prompt)] for category in categories]
        bars = ax.bar(
            [x + offset for x in x_values],
            values,
            width,
            label=prompt,
            color=colors[index % len(colors)],
        )
        ax.bar_label(bars, padding=3, fontsize=9)

    ax.set_title("Mock 流程执行覆盖（非模型结论）", fontsize=15, pad=16)
    ax.set_ylabel("运行记录数")
    ax.set_xticks(x_values)
    ax.set_xticklabels(categories, rotation=18, ha="right")
    ax.legend(title="Prompt 版本")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    fig.text(0.5, 0.01, MOCK_DISCLAIMER, ha="center", fontsize=9, color="#B91C1C")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _plot_badcases(results: List[Dict[str, Any]], output_file: Path) -> None:
    """展示基础规则分类分布；none 表示规则未触发而非模型正确。"""
    _configure_plot_style()
    labels = [
        "规则未触发" if result["badcase_category"] == "none" else result["badcase_category"]
        for result in results
    ]
    counts = Counter(labels)
    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    names = [item[0] for item in ordered]
    values = [item[1] for item in ordered]

    fig, ax = plt.subplots(figsize=(10, 6.2))
    bars = ax.barh(names[::-1], values[::-1], color="#D97706")
    ax.bar_label(bars, padding=4, fontsize=9)
    ax.set_title("Mock 基础规则分类分布（需人工复核）", fontsize=15, pad=16)
    ax.set_xlabel("记录数")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.2)
    fig.text(0.5, 0.01, MOCK_DISCLAIMER, ha="center", fontsize=9, color="#B91C1C")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 JSONL 结果生成模板、摘要和图表。")
    parser.add_argument("result_file", type=Path)
    parser.add_argument("--prefix", default="mock")
    args = parser.parse_args()
    generate_artifacts(load_jsonl(args.result_file), args.prefix)
    print("分析产物已生成。")

