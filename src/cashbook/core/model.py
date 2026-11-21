"""数据模型与输入解析。

金额一律使用 :class:`decimal.Decimal` 并保留两位小数,避免浮点误差;
日期为 ISO 格式 ``YYYY-MM-DD`` 字符串。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date as _date
from decimal import Decimal, InvalidOperation

TWO_PLACES = Decimal("0.01")
_DATE_RE = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$")
_MONTH_RE = re.compile(r"^\d{4}-\d{1,2}$")

DIRECTIONS = ("in", "out")
DIRECTION_LABELS = {"in": "收入", "out": "支出"}


def parse_amount(text) -> Decimal:
    """把任意输入解析为两位小数的金额(必须非负)。"""
    try:
        amount = Decimal(str(text).strip())
    except InvalidOperation as exc:
        raise ValueError(f"金额不合法:{text!r}") from exc
    if amount < 0:
        raise ValueError("金额不能为负(收入/支出用方向区分)")
    return amount.quantize(TWO_PLACES)


def parse_date(text: str = "today") -> str:
    """解析日期:支持 ``today`` / ``2026-11-21`` / ``11-21``(默认当年)。"""
    text = (text or "today").strip().lower()
    if text in ("", "today", "今天"):
        return _date.today().isoformat()
    candidate = text
    if re.match(r"^\d{1,2}-\d{1,2}$", text):  # MM-DD,默认当年
        candidate = f"{_date.today().year}-{text}"
    if not _DATE_RE.match(candidate):
        raise ValueError(f"日期格式应为 YYYY-MM-DD 或 MM-DD:{text}")
    year, mon, day = (int(part) for part in candidate.split("-"))
    try:
        return _date(year, mon, day).isoformat()
    except ValueError as exc:
        raise ValueError(f"日期不存在:{text}") from exc


def parse_month(text: str | None = None) -> str:
    """解析月份:支持 ``2026-11`` / ``11``(默认当年)/ 空(当月)。"""
    if text is None or str(text).strip() in ("", "this", "本月"):
        return _date.today().strftime("%Y-%m")
    text = str(text).strip()
    if _MONTH_RE.match(text):
        year, month = text.split("-")
        if not 1 <= int(month) <= 12:
            raise ValueError(f"月份不合法:{text}")
        return f"{int(year):04d}-{int(month):02d}"
    if re.match(r"^\d{1,2}$", text):
        month = int(text)
        if not 1 <= month <= 12:
            raise ValueError(f"月份不合法:{text}")
        return f"{_date.today().year:04d}-{month:02d}"
    raise ValueError(f"月份格式应为 YYYY-MM 或 MM:{text}")


@dataclass
class Record:
    """一条账目记录。

    ``direction``:``"in"`` 收入 / ``"out"`` 支出;``amount`` 恒为正数。
    """

    id: int
    date: str
    direction: str
    amount: Decimal
    category: str
    note: str = ""

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.id, int) or self.id < 1:
            raise ValueError(f"记录 ID 必须为正整数:{self.id!r}")
        try:
            _date.fromisoformat(self.date)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"日期不合法:{self.date!r}") from exc
        if self.direction not in DIRECTIONS:
            raise ValueError(f"方向只能是 in/out:{self.direction!r}")
        amount = Decimal(self.amount)
        if amount < 0:
            raise ValueError("金额不能为负")
        self.amount = amount.quantize(TWO_PLACES)
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("分类不能为空")
        self.category = self.category.strip()
        self.note = str(self.note or "").strip()

    @property
    def sign(self) -> str:
        return "+" if self.direction == "in" else "-"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "direction": self.direction,
            "amount": str(self.amount),
            "category": self.category,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Record":
        try:
            return cls(
                id=int(data["id"]),
                date=str(data["date"]),
                direction=str(data["direction"]),
                amount=Decimal(str(data["amount"])),
                category=str(data["category"]),
                note=str(data.get("note", "")),
            )
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise ValueError(f"记录数据损坏:{data!r}({exc})") from exc

    def month_key(self) -> str:
        return self.date[:7]
