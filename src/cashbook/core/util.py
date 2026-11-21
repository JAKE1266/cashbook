"""金额格式化 + 终端排版辅助。

排版原语(CJK 对齐/截断)自 v1.0 起统一来自自研微库 cjktable:
https://github.com/JAKE1266/cjktable —— 本模块只保留 CashBook 特有的金额格式化。
"""

from __future__ import annotations

from decimal import Decimal

# 终端排版原语统一来自 cjktable(签名与原内嵌实现完全兼容)
from cjktable import pad, truncate
from cjktable import width as display_width

__all__ = ["display_width", "fmt_money", "pad", "plain_money", "truncate"]


def fmt_money(amount) -> str:
    """人类可读金额(带千分位):1,253.50"""
    return f"{Decimal(amount).quantize(Decimal('0.01')):,.2f}"


def plain_money(amount) -> str:
    """数据用金额(无千分位,适合 JSON):1253.50"""
    return str(Decimal(amount).quantize(Decimal("0.01")))
