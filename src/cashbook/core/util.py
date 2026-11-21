"""终端排版辅助:CJK 双宽字符对齐、金额格式化。"""

from __future__ import annotations

import unicodedata
from decimal import Decimal

Ellipsis = "…"


def display_width(text: str) -> int:
    """按终端显示宽度计算(全角/宽字符占 2 列)。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text: str, width: int, align: str = "left") -> str:
    """按显示宽度补空格,使含中文的列也能对齐。"""
    gap = max(0, width - display_width(text))
    return text + " " * gap if align == "left" else " " * gap + text


def truncate(text: str, width: int) -> str:
    """按显示宽度截断,超出部分以「…」结尾。"""
    if display_width(text) <= width:
        return text
    out, used = [], 0
    for ch in text:
        ch_width = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if used + ch_width > width - 1:
            break
        out.append(ch)
        used += ch_width
    return "".join(out) + Ellipsis


def fmt_money(amount: Decimal) -> str:
    """人类可读金额(带千分位):1,253.50"""
    return f"{Decimal(amount).quantize(Decimal('0.01')):,.2f}"


def plain_money(amount: Decimal) -> str:
    """数据用金额(无千分位,适合 JSON):1253.50"""
    return str(Decimal(amount).quantize(Decimal("0.01")))
