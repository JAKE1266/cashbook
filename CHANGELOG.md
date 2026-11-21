# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-11-21

### 变更
- 终端排版(CJK 对齐 / 截断)改用自研微库 [cjktable](https://github.com/JAKE1266/cjktable),删除内嵌实现

### 新增
- `add` 记账(收入/支出、日期可回填、备注)
- `list` 明细表(月份/分类筛选,中文表格对齐)
- `summary` 月度报表:收支汇总 + 分类 ASCII 条形图 + 预算预警
- `budget set/clear` 月度预算管理
- `rm` 按 ID 删除;`export` 导出 CSV(utf-8-sig,Excel 直接打开不乱码)
- `--json` 全命令支持,便于脚本化
- Decimal 精确金额;JSON 原子写入(写临时文件 + 原子替换)
- 20 个单元测试;GitHub Actions 三系统 × 三 Python 版本 CI
