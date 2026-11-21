"""CashBook 核心层单元测试(仅用标准库 unittest 运行)。"""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from cashbook.core.model import Record, parse_amount, parse_date, parse_month
from cashbook.core.reports import bar_chart, budget_lines, by_category, summarize
from cashbook.core.storage import Ledger


def rec(rid, date, direction, amount, category, note=""):
    return Record(id=rid, date=date, direction=direction, amount=Decimal(amount),
                  category=category, note=note)


class ParseTest(unittest.TestCase):
    def test_parse_amount(self):
        self.assertEqual(parse_amount("25.5"), Decimal("25.50"))
        self.assertEqual(parse_amount(3), Decimal("3.00"))
        with self.assertRaises(ValueError):
            parse_amount("abc")
        with self.assertRaises(ValueError):
            parse_amount("-5")

    def test_parse_date(self):
        self.assertRegex(parse_date("today"), r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(parse_date("2026-02-01"), "2026-02-01")
        self.assertEqual(parse_date("2026-2-1"), "2026-02-01")
        self.assertEqual(parse_date("2-1"), f"2026-02-01")  # 默认当年
        with self.assertRaises(ValueError):
            parse_date("2026-13-01")

    def test_parse_month(self):
        self.assertEqual(parse_month("2026-9"), "2026-09")
        self.assertEqual(parse_month("11"), "2026-11")
        self.assertEqual(parse_month("2026-11"), "2026-11")
        self.assertRegex(parse_month(None), r"^\d{4}-\d{2}$")
        with self.assertRaises(ValueError):
            parse_month("13")
        with self.assertRaises(ValueError):
            parse_month("abc")


class RecordTest(unittest.TestCase):
    def test_roundtrip(self):
        r = rec(1, "2026-11-21", "out", "25.5", "餐饮", "午饭")
        data = r.to_dict()
        again = Record.from_dict(data)
        self.assertEqual(again.amount, Decimal("25.50"))
        self.assertEqual(again.category, "餐饮")

    def test_validation(self):
        with self.assertRaises(ValueError):
            rec(0, "2026-11-21", "out", "1", "餐饮")          # id 非法
        with self.assertRaises(ValueError):
            rec(1, "2026-02-30", "out", "1", "餐饮")          # 日期不存在
        with self.assertRaises(ValueError):
            rec(1, "2026-11-21", "down", "1", "餐饮")         # 方向非法
        with self.assertRaises(ValueError):
            rec(1, "2026-11-21", "out", "1", "  ")            # 分类为空


class LedgerTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "ledger.json"
        self.ledger = Ledger(self.path)

    def test_add_and_persist(self):
        self.ledger.add("out", "25.50", "餐饮", "午饭")
        self.ledger.add("in", "3000", "工资", "月薪")
        # 重新加载同一文件,数据仍在
        again = Ledger(self.path)
        self.assertEqual(len(again.records()), 2)
        self.assertEqual(again.records()[0].amount, Decimal("25.50"))
        self.assertEqual(again.data["next_id"], 3)

    def test_filter_month_and_category(self):
        self.ledger.add("out", "10", "餐饮", date="2026-10-01")
        self.ledger.add("out", "20", "交通", date="2026-11-01")
        self.ledger.add("out", "30", "餐饮", date="2026-11-02")
        self.assertEqual(len(self.ledger.records(month="2026-11")), 2)
        self.assertEqual(len(self.ledger.records(month="2026-10")), 1)
        self.assertEqual(len(self.ledger.records(category="餐饮")), 2)
        self.assertEqual(len(self.ledger.records(month="2026-11", category="餐饮")), 1)

    def test_sorted_by_date_then_id(self):
        self.ledger.add("out", "10", "餐饮", date="2026-11-02")
        self.ledger.add("out", "20", "餐饮", date="2026-11-01")
        dates = [r.date for r in self.ledger.records()]
        self.assertEqual(dates, ["2026-11-01", "2026-11-02"])

    def test_remove(self):
        r = self.ledger.add("out", "10", "餐饮")
        self.assertTrue(self.ledger.remove(r.id))
        self.assertFalse(self.ledger.remove(r.id))
        self.assertEqual(self.ledger.records(), [])

    def test_budget(self):
        self.ledger.set_budget("餐饮", "800")
        self.ledger.set_budget("餐饮", "900")  # 覆盖
        self.assertEqual(self.ledger.budgets()["餐饮"], Decimal("900.00"))
        self.assertTrue(self.ledger.clear_budget("餐饮"))
        self.assertFalse(self.ledger.clear_budget("餐饮"))
        with self.assertRaises(ValueError):
            self.ledger.set_budget("餐饮", "0")


class ReportTest(unittest.TestCase):
    def test_summarize(self):
        records = [rec(1, "2026-11-01", "in", "3000", "工资"),
                   rec(2, "2026-11-02", "out", "25.5", "餐饮"),
                   rec(3, "2026-11-03", "out", "74.5", "购物")]
        s = summarize(records)
        self.assertEqual(s["income"], Decimal("3000.00"))
        self.assertEqual(s["expense"], Decimal("100.00"))
        self.assertEqual(s["net"], Decimal("2900.00"))

    def test_by_category_sorted(self):
        records = [rec(1, "2026-11-01", "out", "10", "交通"),
                   rec(2, "2026-11-02", "out", "100", "餐饮"),
                   rec(3, "2026-11-03", "out", "50", "餐饮"),
                   rec(4, "2026-11-04", "in", "999", "工资")]  # 收入不进分类
        totals = by_category(records)
        self.assertEqual(list(totals), ["餐饮", "交通"])
        self.assertEqual(totals["餐饮"], Decimal("150.00"))

    def test_bar_chart(self):
        lines = bar_chart({"餐饮": Decimal("100"), "交通": Decimal("50")})
        self.assertEqual(len(lines), 2)
        self.assertIn("餐饮", lines[0])
        self.assertGreater(lines[0].count("█"), lines[1].count("█"))
        self.assertEqual(bar_chart({}), [])

    def test_budget_lines_warns_on_overspend(self):
        records = [rec(1, "2026-11-01", "out", "600", "餐饮")]
        lines = budget_lines(records, {"餐饮": Decimal("500")})
        self.assertIn("[!]", lines[0])
        ok_lines = budget_lines(records, {"餐饮": Decimal("800")})
        self.assertIn("[OK]", ok_lines[0])


if __name__ == "__main__":
    unittest.main()
