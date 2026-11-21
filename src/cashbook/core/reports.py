"""月度报表:收支汇总、分类占比、ASCII 条形图、预算预警。"""

from __future__ import annotations

from decimal import Decimal

from cashbook.core.util import fmt_money, pad, plain_money

BAR_WIDTH = 32


def summarize(records) -> dict:
    """汇总一组记录:总收入、总支出、结余。"""
    income = Decimal("0")
    expense = Decimal("0")
    for record in records:
        if record.direction == "in":
            income += record.amount
        else:
            expense += record.amount
    return {"income": income, "expense": expense, "net": income - expense}


def by_category(records) -> dict:
    """支出按分类汇总,从高到低排序。"""
    totals: dict = {}
    for record in records:
        if record.direction != "out":
            continue
        totals[record.category] = totals.get(record.category, Decimal("0")) + record.amount
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def bar_chart(totals: dict, bar_width: int = BAR_WIDTH) -> list:
    """生成 ASCII 条形图行:「分类 ████ 金额 (占比%)」。"""
    if not totals:
        return []
    largest = max(totals.values())
    total = sum(totals.values())
    lines = []
    for category, amount in totals.items():
        blocks = max(1, round(float(amount / largest) * bar_width)) if largest else 0
        percent = float(amount / total * 100) if total else 0.0
        lines.append(
            f"  {pad(category, 8)} {'█' * blocks} {fmt_money(amount)} ({percent:.1f}%)"
        )
    return lines


def budget_lines(records, budgets: dict) -> list:
    """生成预算状态行:未超支 [OK],超支 [!]。"""
    spent = by_category(records)
    lines = []
    for category, limit in sorted(budgets.items()):
        used = spent.get(category, Decimal("0"))
        ratio = float(used / limit) if limit else 0.0
        mark = "[!]" if used > limit else "[OK]"
        lines.append(
            f"  {mark} {pad(category, 8)} 已用 {fmt_money(used)} / 预算 {fmt_money(limit)}"
            f"({ratio:.0%})"
        )
    return lines


def month_report(ledger, month: str) -> dict:
    """整月报表:汇总 + 分类图表 + 预算状态,各字段均可直接 JSON 化。"""
    records = ledger.records(month=month)
    summary = summarize(records)
    totals = by_category(records)
    return {
        "month": month,
        "record_count": len(records),
        "income": plain_money(summary["income"]),
        "expense": plain_money(summary["expense"]),
        "net": plain_money(summary["net"]),
        "by_category": {cat: plain_money(amount) for cat, amount in totals.items()},
        "chart": bar_chart(totals),
        "budget": budget_lines(records, ledger.budgets()),
    }
