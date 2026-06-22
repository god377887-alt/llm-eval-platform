"""验证 Mock 全流程、SQLite 一致性、SQL 报告与 API 安全门槛。"""

import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATA_FILE, MOCK_MODEL_NAME  # noqa: E402
from generate_sql_report import generate_sql_report  # noqa: E402
from providers import ConfigurationError, create_provider  # noqa: E402
from run_eval import build_parser, run_evaluation  # noqa: E402


class V2PipelineTests(unittest.TestCase):
    """复用一次临时目录中的完整 48 条 Mock 运行。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir_context = tempfile.TemporaryDirectory()
        cls.temp_dir = Path(cls.temp_dir_context.name)
        cls.output_dir = cls.temp_dir / "mock"
        cls.database_path = cls.temp_dir / "eval_runs.db"
        with patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Mock 模式不应访问网络"),
        ) as request_mock:
            cls.results, _, cls.run_ids = run_evaluation(
                "mock",
                "all",
                output_dir=cls.output_dir,
                database_path=cls.database_path,
                generate_analysis=False,
            )
            cls.network_call_count = request_mock.call_count

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir_context.cleanup()

    def test_mock_mode_does_not_access_network(self) -> None:
        self.assertEqual(self.network_call_count, 0)
        self.assertTrue(all(item["is_mock"] for item in self.results))

    def test_complete_mock_run_has_48_results(self) -> None:
        self.assertEqual(len(self.results), 48)
        self.assertEqual(len(self.run_ids), 2)
        self.assertEqual({item["prompt_version"] for item in self.results}, {"baseline", "optimized"})

    def test_sqlite_count_matches_csv(self) -> None:
        with (self.output_dir / "results.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            csv_count = sum(1 for _ in csv.DictReader(file))
        with sqlite3.connect(self.database_path) as connection:
            placeholders = ",".join("?" for _ in self.run_ids)
            database_count = connection.execute(
                f"SELECT COUNT(*) FROM eval_results WHERE run_id IN ({placeholders})",
                self.run_ids,
            ).fetchone()[0]
        self.assertEqual(csv_count, 48)
        self.assertEqual(database_count, csv_count)

    def test_sql_report_can_be_generated(self) -> None:
        csv_path = self.temp_dir / "sql_summary.csv"
        markdown_path = self.temp_dir / "sql_summary.md"
        datasets = generate_sql_report(self.database_path, csv_path, markdown_path)
        self.assertTrue(csv_path.is_file())
        self.assertTrue(markdown_path.is_file())
        self.assertEqual(datasets["totals"][0]["result_count"], 48)
        self.assertEqual(datasets["totals"][0]["result_source"], "mock")

    def test_api_without_key_has_clear_error(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "缺少 API_KEY"):
            create_provider(
                requested_provider="api",
                data_file=DATA_FILE,
                mock_model_name=MOCK_MODEL_NAME,
                api_key="",
                base_url="https://api.example.com/v1",
                api_model="example-model",
                timeout_seconds=30,
                max_retries=1,
            )

    def test_default_provider_is_mock(self) -> None:
        args = build_parser().parse_args([])
        self.assertEqual(args.provider, "mock")


if __name__ == "__main__":
    unittest.main()
