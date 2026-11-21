"""CashBook 命令行入口。

::

    cashbook add 25.5 餐饮 公司楼下午饭      # 记一笔支出
    cashbook add 3000 工资 --in             # 记一笔收入
    cashbook summary                        # 本月报表
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

from . import __version__
from .core.model import DIRECTION_LABELS, parse_month
from .core.reports import month_report
from .core.storage import DEFAULT_PATH, Ledger
from .core.util import display_width, fmt_money, pad, truncate


def _table(headers: list, rows: list) -> str:
    """渲染对齐表格(自动适应中文双宽字符)。"""
    widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(str(cell)))
    lines = ["  ".join(pad(h, widths[i]) for i, h in enumerate(headers)),
             "  ".join("-" * widths[i] for i in range(len(headers)))]
    for row in rows:
        lines.append("  ".join(pad(str(cell), widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- 子命令

def cmd_add(args, ledger: Ledger) -> int:
    record = ledger.add(
        direction="in" if args.income else "out",
        amount=args.amount,
        category=args.category,
        note=" ".join(args.note),
        date=args.date,
    )
    if args.json:
        _print_json(record.to_dict())
        return 0
    label = DIRECTION_LABELS[record.direction]
    print(f"[OK] 已记录:{label} {fmt_money(record.amount)} | {record.category}"
          f" | {record.date}" + (f" | {record.note}" if record.note else "")
          + f" [id={record.id}]")
    return 0


def cmd_list(args, ledger: Ledger) -> int:
    month = parse_month(args.month) if args.month else None
    records = ledger.records(month=month, category=args.cat)
    if args.json:
        _print_json({"count": len(records), "records": [r.to_dict() for r in records]})
        return 0
    if not records:
        print("没有找到符合条件的记录。")
        return 0
    rows = [[r.id, r.date, DIRECTION_LABELS[r.direction],
             f"{r.sign}{fmt_money(r.amount)}", r.category,
             truncate(r.note, 16)] for r in records]
    print(_table(["ID", "日期", "类型", "金额", "分类", "备注"], rows))
    print(f"\n共 {len(records)} 条记录")
    return 0


def cmd_summary(args, ledger: Ledger) -> int:
    month = parse_month(args.month)
    report = month_report(ledger, month)
    if args.json:
        _print_json(report)
        return 0
    print(f"CashBook 月度报表:{report['month']}(共 {report['record_count']} 条)")
    if report["record_count"] == 0:
        print("该月暂无记录。")
        return 0
    income = Decimal(report["income"])
    expense = Decimal(report["expense"])
    print(f"  总收入  +{fmt_money(income)}")
    print(f"  总支出  -{fmt_money(expense)}" if expense else "  总支出  0.00")
    print(f"  结余    {fmt_money(Decimal(report['net']))}")
    print("\n支出分类(从高到低):")
    for line in report["chart"]:
        print(line)
    if report["budget"]:
        print("\n本月预算:")
        for line in report["budget"]:
            print(line)
    return 0


def cmd_budget(args, ledger: Ledger) -> int:
    if args.action == "set":
        limit = ledger.set_budget(args.category, args.limit)
        print(f"[OK] 已设置预算:{args.category} 每月 {fmt_money(limit)}")
        return 0
    if args.action == "clear":
        ok = ledger.clear_budget(args.category)
        print(f"[OK] 已清除 {args.category} 的预算" if ok else f"{args.category} 本来就没有预算")
        return 0
    budgets = ledger.budgets()
    if args.json:
        _print_json({cat: str(limit) for cat, limit in budgets.items()})
        return 0
    if not budgets:
        print("还没有设置预算。示例:cashbook budget set 餐饮 800")
        return 0
    print(_table(["分类", "每月预算"], [[cat, fmt_money(limit)] for cat, limit in budgets.items()]))
    return 0


def cmd_rm(args, ledger: Ledger) -> int:
    removed = [rid for rid in args.ids if ledger.remove(rid)]
    missing = [rid for rid in args.ids if rid not in removed]
    if args.json:
        _print_json({"removed": removed, "missing": missing})
        return 0
    if removed:
        print(f"[OK] 已删除 {len(removed)} 条记录:{', '.join(map(str, removed))}")
    if missing:
        print(f"[!] 未找到:{', '.join(map(str, missing))}", file=sys.stderr)
    return 1 if missing and not removed else 0


def cmd_export(args, ledger: Ledger) -> int:
    month = parse_month(args.month) if args.month else None
    records = ledger.records(month=month, category=args.cat)
    path = Path(args.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.writer(fp)
        writer.writerow(["ID", "日期", "类型", "金额", "分类", "备注"])
        for r in records:
            writer.writerow([r.id, r.date, DIRECTION_LABELS[r.direction],
                             str(r.amount), r.category, r.note])
    if args.json:
        _print_json({"path": str(path), "count": len(records)})
        return 0
    print(f"[OK] 已导出 {len(records)} 条记录到 {path}")
    print("    (utf-8-sig 编码,Excel 可直接打开且不乱码)")
    return 0


# ---------------------------------------------------------------- 参数解析

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cashbook",
        description="CashBook 轻记账 —— 零依赖的命令行记账本:记账 / 报表 / 预算 / 导出",
    )
    parser.add_argument("--version", action="version", version=f"cashbook {__version__}")
    parser.add_argument("--file", default=None, help=f"账本文件路径(默认 {DEFAULT_PATH})")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add", help="记一笔(默认支出,--in 为收入)")
    p.add_argument("amount", help="金额,如 25.5")
    p.add_argument("category", help="分类,如 餐饮 / 交通 / 工资")
    p.add_argument("note", nargs="*", help="备注(可省略)")
    p.add_argument("--in", dest="income", action="store_true", help="记为收入")
    p.add_argument("-d", "--date", default="today", help="日期(today / 2026-11-21 / 11-21)")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list", help="查看账目明细")
    p.add_argument("-m", "--month", default=None, help="限定月份(2026-11 或 11)")
    p.add_argument("-c", "--cat", default=None, help="限定分类")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("summary", help="月度报表:收支汇总 + 分类图表 + 预算")
    p.add_argument("-m", "--month", default=None, help="月份(默认本月)")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("budget", help="查看/设置/清除月度预算")
    p.add_argument("action", nargs="?", default="show", choices=("show", "set", "clear"))
    p.add_argument("category", nargs="?", default=None, help="分类名")
    p.add_argument("limit", nargs="?", default=None, help="每月预算金额")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=cmd_budget)

    p = sub.add_parser("rm", help="按 ID 删除记录")
    p.add_argument("ids", nargs="+", type=int, help="要删除的记录 ID")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=cmd_rm)

    p = sub.add_parser("export", help="导出 CSV(Excel 友好)")
    p.add_argument("path", help="输出文件路径,如 2026账单.csv")
    p.add_argument("-m", "--month", default=None, help="限定月份")
    p.add_argument("-c", "--cat", default=None, help="限定分类")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=cmd_export)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    ledger = Ledger(args.file)
    try:
        return args.func(args, ledger)
    except KeyboardInterrupt:
        print("\n已取消。")
        return 130
    except BrokenPipeError:
        return 0
    except (ValueError, TypeError, OSError) as exc:
        print(f"错误:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
