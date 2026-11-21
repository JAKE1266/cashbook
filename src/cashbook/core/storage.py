"""JSON 账本存储:读写、增删查、预算管理。

数据文件结构::

    {
      "records": [ {"id": 1, "date": "2026-11-21", "direction": "out", ...}, ... ],
      "budgets": {"餐饮": "500.00"},
      "next_id": 2
    }

保存采用「写临时文件 + 原子替换」,即使中途断电也不会损坏账本。
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

from cashbook.core.model import Record, parse_amount, parse_date

DEFAULT_PATH = Path.home() / ".cashbook" / "data.json"


class Ledger:
    """一个 JSON 文件对应的账本。"""

    def __init__(self, path=None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.data = {"records": [], "budgets": {}, "next_id": 1}
        self._load()

    # ------------------------------------------------------------ 底层读写

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"账本文件损坏,不是合法 JSON:{self.path}({exc})") from exc
        records = [Record.from_dict(item) for item in raw.get("records", [])]
        self.data = {
            "records": records,
            "budgets": {str(k): str(v) for k, v in raw.get("budgets", {}).items()},
            "next_id": int(raw.get("next_id", 1)),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "records": [r.to_dict() for r in self.data["records"]],
            "budgets": dict(self.data["budgets"]),
            "next_id": self.data["next_id"],
        }
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)  # 原子替换

    # ------------------------------------------------------------ 账目增删查

    def add(self, direction: str, amount, category: str, note: str = "", date: str = "today") -> Record:
        record = Record(
            id=self.data["next_id"],
            date=parse_date(date),
            direction=direction,
            amount=parse_amount(amount),
            category=category,
            note=note,
        )
        self.data["records"].append(record)
        self.data["next_id"] = record.id + 1
        self.save()
        return record

    def remove(self, record_id: int) -> bool:
        before = len(self.data["records"])
        self.data["records"] = [r for r in self.data["records"] if r.id != int(record_id)]
        removed = len(self.data["records"]) < before
        if removed:
            self.save()
        return removed

    def records(self, month: str | None = None, category: str | None = None) -> list:
        """按月份/分类筛选,按日期与 ID 排序返回。``month`` 为 ``YYYY-MM``。"""
        if month is not None:
            if "-" not in month:
                raise ValueError(f"月份格式应为 YYYY-MM:{month}")
            year, mon = month.split("-")
            month = f"{int(year):04d}-{int(mon):02d}"
        result = []
        for record in self.data["records"]:
            if month is not None and record.month_key() != month:
                continue
            if category is not None and record.category != category:
                continue
            result.append(record)
        return sorted(result, key=lambda r: (r.date, r.id))

    # ------------------------------------------------------------ 预算

    def budgets(self) -> dict:
        return {cat: Decimal(limit) for cat, limit in self.data["budgets"].items()}

    def set_budget(self, category: str, limit) -> Decimal:
        limit = parse_amount(limit)
        if limit == 0:
            raise ValueError("预算金额应大于 0(清除预算请用 budget clear)")
        self.data["budgets"][category.strip()] = str(limit)
        self.save()
        return limit

    def clear_budget(self, category: str) -> bool:
        if category.strip() in self.data["budgets"]:
            del self.data["budgets"][category.strip()]
            self.save()
            return True
        return False
