"""命令行入口测试:用临时账本文件端到端跑 main()。"""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from cashbook.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.file = str(Path(tmp.name) / "ledger.json")

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_full_workflow(self):
        # 记账 → 列表 → 报表 → 预算 → 导出 → 删除,端到端验证
        code, out, _ = self.run_cli("--file", self.file, "add", "25.5", "餐饮", "午饭")
        self.assertEqual(code, 0)
        self.assertIn("[id=1]", out)

        code, out, _ = self.run_cli("--file", self.file, "add", "3000", "工资", "--in")
        self.assertEqual(code, 0)

        code, out, _ = self.run_cli("--file", self.file, "list", "--json")
        data = json.loads(out)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["records"][0]["direction"], "out")

        code, out, _ = self.run_cli("--file", self.file, "summary", "--json")
        report = json.loads(out)
        self.assertEqual(report["income"], "3000.00")
        self.assertEqual(report["expense"], "25.50")
        self.assertEqual(report["net"], "2974.50")
        self.assertIn("餐饮", report["by_category"])

        code, out, _ = self.run_cli("--file", self.file, "budget", "set", "餐饮", "800")
        self.assertEqual(code, 0)
        code, out, _ = self.run_cli("--file", self.file, "summary")
        self.assertIn("[OK]", out)  # 未超支
        code, out, _ = self.run_cli("--file", self.file, "budget", "set", "餐饮", "20")
        code, out, _ = self.run_cli("--file", self.file, "summary")
        self.assertIn("[!]", out)  # 超支告警

        csv_path = str(Path(self.file).with_suffix(".csv"))
        code, out, _ = self.run_cli("--file", self.file, "export", csv_path)
        self.assertEqual(code, 0)
        with open(csv_path, encoding="utf-8-sig") as fp:
            rows = list(csv.reader(fp))
        self.assertEqual(rows[0], ["ID", "日期", "类型", "金额", "分类", "备注"])
        self.assertEqual(len(rows), 3)  # 表头 + 2 条

        code, out, _ = self.run_cli("--file", self.file, "rm", "1")
        self.assertEqual(code, 0)
        code, out, _ = self.run_cli("--file", self.file, "list", "--json")
        self.assertEqual(json.loads(out)["count"], 1)

    def test_human_table_alignment(self):
        self.run_cli("--file", self.file, "add", "12.3", "餐饮", "牛肉面")
        code, out, _ = self.run_cli("--file", self.file, "list")
        self.assertEqual(code, 0)
        self.assertIn("-12.30", out)
        self.assertIn("牛肉面", out)

    def test_empty_summary(self):
        code, out, _ = self.run_cli("--file", self.file, "summary")
        self.assertEqual(code, 0)
        self.assertIn("暂无记录", out)

    def test_rm_missing_returns_error(self):
        code, _, err = self.run_cli("--file", self.file, "rm", "99")
        self.assertEqual(code, 1)
        self.assertIn("未找到", err)

    def test_invalid_amount(self):
        code, _, err = self.run_cli("--file", self.file, "add", "abc", "餐饮")
        self.assertEqual(code, 1)
        self.assertIn("金额不合法", err)

    def test_no_args_shows_help(self):
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("usage", out.lower())


if __name__ == "__main__":
    unittest.main()
