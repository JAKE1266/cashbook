"""CashBook 轻记账 —— 零依赖的命令行个人记账工具。

JSON 存储、Decimal 精确金额、月度报表与预算预警,数据完全保存在本地::

    from cashbook import Ledger

    ledger = Ledger("data.json")
    ledger.add("out", "25.50", "餐饮", "公司楼下午饭")
"""

from cashbook.core.model import Record, parse_date, parse_month
from cashbook.core.reports import month_report, summarize
from cashbook.core.storage import Ledger

__version__ = "1.0.0"

__all__ = ["Ledger", "Record", "month_report", "parse_date", "parse_month", "summarize", "__version__"]
