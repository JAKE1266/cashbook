# CashBook 轻记账

> 命令行里的记账本:记账、月度报表、分类图表、预算预警。
> 核心逻辑只用 Python 标准库;唯一依赖是自研微库 [cjktable](https://github.com/JAKE1266/cjktable)(终端中文对齐排版)。数据 100% 存在你自己的电脑上。

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-cjktable%20%28self--built%29-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ✨ 特性

- 💰 **精确金额**:全程 `Decimal`,没有 0.1 + 0.2 ≠ 0.3 的浮点烦恼
- 📊 **月度报表**:收支汇总 + 分类占比 **ASCII 条形图**,终端里一眼看穿钱花哪儿了
- 🎯 **预算预警**:给「餐饮」设个月度上限,超支自动 `[!]` 提醒
- 🖥 **中文友好**:表格按 CJK 双宽字符对齐(基于自研微库 [cjktable](https://github.com/JAKE1266/cjktable)),Windows / macOS / Linux 终端都不乱
- 📤 **一键导出**:CSV 采用 `utf-8-sig` 编码,Excel 双击打开不乱码
- 🔒 **数据自主**:就是一个 JSON 文件,备份 = 复制文件;保存采用「临时文件 + 原子替换」,不怕中途断电
- 🧪 **带测试**:20 个单元测试 + GitHub Actions 三系统 × 三版本 CI
- 🔌 **可脚本化**:每个命令都支持 `--json`

## 📦 安装

```bash
git clone https://github.com/JAKE1266/cashbook.git
cd cashbook
python -m cashbook --help          # 克隆即用

# 或安装为命令(获得 cashbook 命令)
pip install .
```

## 🚀 快速上手

```bash
cashbook add 25.5 餐饮 公司楼下午饭     # 记一笔支出(日期默认今天)
cashbook add 12 交通 地铁通勤 -d 11-19  # 日期可回填(MM-DD 默认当年)
cashbook add 8500 工资 --in            # 收入加 --in
cashbook budget set 餐饮 300           # 设月度预算
cashbook summary                       # 本月报表
cashbook list                          # 全部明细
cashbook export 2026账单.csv           # 导出 CSV
cashbook rm 3                          # 按 ID 删除
```

### 报表长这样

```
CashBook 月度报表:2026-11(共 5 条)
  总收入  +8,500.00
  总支出  -515.50
  结余    7,984.50

支出分类(从高到低):
  餐饮     ████████████████████████████████ 345.50 (67.0%)
  购物     ███████████████ 158.00 (30.6%)
  交通     █ 12.00 (2.3%)

本月预算:
  [!] 餐饮     已用 345.50 / 预算 300.00(115%)
```

## 🧰 命令一览

| 命令 | 作用 |
|------|------|
| `add AMOUNT CATEGORY [NOTE] [--in] [-d DATE]` | 记账(默认支出,`--in` 收入) |
| `list [-m 月份] [-c 分类]` | 明细表(中文列自动对齐) |
| `summary [-m 月份]` | 月度报表 + 分类图表 + 预算状态 |
| `budget [set 分类 金额 \| clear 分类]` | 查看 / 设置 / 清除月度预算 |
| `rm ID [ID...]` | 删除记录 |
| `export PATH [-m 月份] [-c 分类]` | 导出 CSV |
| 全局:`--file 路径` | 指定账本文件(默认 `~/.cashbook/data.json`) |
| 全局:`--json` | 所有命令输出 JSON |

## ❓ 常见问题

**Q: 数据存在哪?会不会上传?**
默认 `~/.cashbook/data.json`,纯本地文件,没有任何联网行为。换电脑 = 复制这个文件。

**Q: 想同时记两本账(比如公司报销)?**
用 `--file` 指向不同文件即可:`cashbook --file work.json add ...`。

**Q: 金额精度可靠吗?**
内部全程 `Decimal` 并强制两位小数,汇总求和与报表不会出现浮点尾差。

**Q: CSV 用 Excel 打开乱码?**
不会——导出用 `utf-8-sig`(带 BOM),Excel 可直接识别中文。

**Q: 想发布到 PyPI?**
`cashbook` 是占位名,发布前请在 `pyproject.toml` 换一个未被占用的名字。

## 📁 项目结构

```
cashbook/
├── .github/workflows/ci.yml   # CI:Ubuntu / Windows / macOS × Python 3.9-3.13
├── src/cashbook/
│   ├── core/
│   │   ├── model.py           # Record 数据模型 + 日期/金额解析
│   │   ├── storage.py         # JSON 账本(原子写入、增删查、预算)
│   │   ├── reports.py         # 月度报表、分类汇总、ASCII 条形图
│   │   └── util.py            # CJK 对齐、金额格式化
│   └── cli.py                 # 命令行入口
├── tests/                     # 20 个单元测试(unittest 免安装可跑)
└── pyproject.toml
```

## 🧪 开发与测试

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
# Windows(PowerShell):$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

## 🗺 路线图

- [ ] `stats` 年度趋势图(12 个月收支折线)
- [ ] 分类别名与默认分类配置
- [ ] Web 版仪表盘(与 PyToolBox 同款零依赖方案)

## 📄 许可证

[MIT](LICENSE) —— 可自由使用、修改与分发。

---

*同系列项目:[PyToolBox](https://github.com/JAKE1266/py-toolbox) 多功能工具箱 · [gitdash](https://github.com/JAKE1266/gitdash) Git 终端仪表盘 · [DevBox](https://github.com/JAKE1266/devbox) 前端开发工具箱 · [csvq](https://github.com/JAKE1266/csvq) SQL 查 CSV · [cjktable](https://github.com/JAKE1266/cjktable) CJK 排版微库 · [duviz](https://github.com/JAKE1266/duviz) 磁盘占用可视化 · [httpoke](https://github.com/JAKE1266/httpoke) HTTP 调试工具 · [mdown](https://github.com/JAKE1266/mdown) Markdown→HTML · [msite](https://github.com/JAKE1266/msite) 静态文档站 · [crony](https://github.com/JAKE1266/crony) cron 表达式解析 · [pomo](https://github.com/JAKE1266/pomo) 番茄钟 · [termplot](https://github.com/JAKE1266/termplot) 终端数据图表 · [filewatch](https://github.com/JAKE1266/filewatch) 目录变更监控 · [packpeek](https://github.com/JAKE1266/packpeek) 压缩包检查与安全解压*
