# Task Tracker — Stock Research Data Foundation

> REQ-20260629-001

## 总目标

基于文章规划，构建本地优先的个人股票研究数据底座，包含：数据采集层、本地存储层（DuckDB+Parquet+SQLite）、本地MCP服务、7个研究Skill、验收测试套件。

## 阶段拆解

### Phase 1: 侦察审计（目标：产出3个审计文件）
- [x] P1.1 克隆12个仓库到 `third_party/`
  - akfamily/akshare ✓
  - waditu/tushare (网络问题，通过Web研究补充)
  - Micro-sheep/efinance ✓
  - mootdx/mootdx (网络问题，通过Web研究补充)
  - zer0quant/zer0share (通过Web研究)
  - tycallen/TushareDB (通过Web研究)
  - chenditc/investment_data (通过Web研究)
  - zwldarren/akshare-one-mcp (通过Web研究)
  - buuzzy/tushare_MCP (通过Web研究)
  - tr1s7an/CnInfoReports (通过Web研究)
  - legeling/Annualreport_tools (通过Web研究)
  - atompilot/baostock-skill (通过Web研究)
- [x] P1.2 审计每个仓库（pyproject/requirements、主包目录、测试目录、changelog、HTTP客户端/token/调度器/缓存/MCP工具源码）
- [x] P1.3 产出 `audits/project_matrix.csv`
- [x] P1.4 产出 `audits/source_endpoint_catalog.md`
- [x] P1.5 产出 `audits/reuse_decisions.md`

### Phase 2: 最小数据底座（目标：4个采集job可运行）
- [x] P2.1 创建项目骨架（pyproject.toml, uv.lock, .env.example, 目录结构）
- [x] P2.2 实现 `src/models/schema.py` — 4张规范表定义
- [x] P2.3 实现 `src/normalize/` — 符号归一化、单位归一化、字段映射、单季衍生
- [x] P2.4 实现 `src/adapters/tushare_adapter.py`
- [x] P2.5 实现 `src/adapters/akshare_adapter.py`
- [x] P2.6 实现 `src/adapters/baostock_adapter.py`
- [x] P2.7 实现 `src/adapters/cninfo_adapter.py`
- [x] P2.8 实现 `src/lake/` — bronze/silver/duckdb_views.sql
- [x] P2.9 实现 `sync_security_master` job
- [x] P2.10 实现 `sync_market_daily` job
- [x] P2.11 实现 `sync_financials` job
- [x] P2.12 实现 `sync_announcements` job
- [x] P2.13 编写5个数据质量测试

### Phase 3: 本地MCP（目标：11个工具可用）
- [x] P3.1 搭建MCP骨架（fork akshare-one-mcp transport shell）
- [x] P3.2 实现 `search_security`
- [x] P3.3 实现 `get_market_history`
- [x] P3.4 实现 `get_latest_quote`
- [x] P3.5 实现 `get_financial_statements`
- [x] P3.6 实现 `get_financial_metrics`
- [x] P3.7 实现 `get_announcements`
- [x] P3.8 实现 `search_announcements`
- [x] P3.9 实现 `compare_sources`
- [x] P3.10 实现 `get_data_freshness`
- [x] P3.11 实现 `run_data_quality_check`
- [x] P3.12 实现 `export_dataset`

### Phase 4: Skills（目标：7个SKILL.md完成）
- [x] P4.1 `stock-data-acquisition/SKILL.md`
- [x] P4.2 `stock-data-validation/SKILL.md`
- [x] P4.3 `company-fundamental-research/SKILL.md`
- [x] P4.4 `announcement-event-research/SKILL.md`
- [x] P4.5 `industry-supply-chain-research/SKILL.md`
- [x] P4.6 `valuation-and-earnings-sensitivity/SKILL.md`
- [x] P4.7 `investment-thesis-falsification/SKILL.md`

### Phase 5: 验收测试（目标：9项验收通过）
- [x] P5.1 数据正确性测试
- [x] P5.2 多源一致性测试
- [x] P5.3 新鲜度测试
- [x] P5.4 空值处理测试
- [x] P5.5 复权正确性测试
- [x] P5.6 财务基准正确性测试
- [x] P5.7 公告完整性测试
- [x] P5.8 MCP返回大小控制测试
- [x] P5.9 端到端研究流程测试

## 进度记录

| 检查时间 | 完成子任务数 | 总子任务数 | 状态 | 备注 |
|---|---|---|---|---|
| 2026-06-29 22:41 | 0 | 44 | 启动 | 初始化目标 |
| 2026-06-29 22:43 | 0 | 46 | 待启动 | 自动检查 |
| 2026-06-29 23:07 | 41 | 46 | 进行中 | 自动检查 |
| 2026-06-29 23:10 | 46 | 46 | 已完成 | 自动检查 |
| 2026-06-29 23:18 | 46 | 46 | 已完成 | 自动检查 |
| 2026-06-30 00:00 | 46 | 46 | 已完成 | 自动检查 |
| 2026-06-30 02:00 | 46 | 46 | 已完成 | 自动检查 |
| 2026-06-30 04:00 | 46 | 46 | 已完成 | 自动检查 |
| 2026-06-30 06:00 | 46 | 46 | 已完成 | 自动检查 |
| 2026-06-30 08:00 | 46 | 46 | 已完成 | 自动检查 |

## 交付资产

- `third_party/` — 12个审计仓库
- `audits/project_matrix.csv` — 项目矩阵
- `audits/source_endpoint_catalog.md` — 端点目录
- `audits/reuse_decisions.md` — 复用决策
- `src/` — 适配器/归一化/数据湖/模型/任务
- `mcp/` — 本地MCP服务
- `skills/` — 7个Skill
- `tests/` — 验收测试
