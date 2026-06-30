# Stock Research Data Foundation

> 本地优先的个人股票研究数据底座，基于 DuckDB + Parquet + SQLite + MCP

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd /path/to/get-stock-data

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -e ".[dev]"
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的 Tushare Pro token
# 获取地址: https://tushare.pro/register
echo 'TUSHARE_TOKEN=your_token_here' >> .env
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 运行测试

```bash
python -m pytest tests/ -v
```

### 5. 启动数据同步

```python
from src.jobs import run_sync_security_master, run_sync_market_daily

# 同步证券主数据
result = run_sync_security_master(tushare_token="your_token")
print(result)

# 同步某日行情
result = run_sync_market_daily(trade_date="20240628")
print(result)
```

### 6. 启动 MCP 服务

```bash
python -m mcp.local_stock_server
```

## 架构概览

```
┌─────────────────────────────────────────────────┐
│              Skills (7个研究Skill)                │
├─────────────────────────────────────────────────┤
│           MCP Server (11个工具, stdio)            │
├─────────────────────────────────────────────────┤
│        Silver Layer (DuckDB + Parquet)           │
├─────────────────────────────────────────────────┤
│        Bronze Layer (原始数据落地)                 │
├─────────────────────────────────────────────────┤
│     Adapters (Tushare/AKShare/BaoStock/CNINFO)  │
└─────────────────────────────────────────────────┘
```

## 数据源

| 数据源 | 角色 | 需要 Token | 说明 |
|---|---|---|---|
| Tushare Pro | 主数据源 | 是 | 结构化API，字段文档齐全 |
| AKShare | 广度采集 | 否 | 多源公开数据，易变化 |
| BaoStock | 验证源 | 否 | 免费，volume单位为股 |
| CNINFO | 公告权威源 | 否 | 官方公告+PDF下载 |

## 规范化规则

- **符号格式**: `600519.SH` / `000001.SZ` / `920001.BJ` / `00700.HK`
- **成交量单位**: 股 (Tushare/AKShare的手×100，BaoStock已是股)
- **成交额单位**: 元 (Tushare的千元×1000)
- **财务数据**: 保留累计值和单季衍生值，标注来源

## 目录结构

```
get-stock-data/
├── src/
│   ├── adapters/          # 4个数据源适配器
│   ├── normalize/         # 符号/单位/字段/单季 归一化
│   ├── lake/              # Bronze/Silver/DuckDB视图
│   ├── models/            # Schema定义 + DQ规则
│   ├── jobs/              # 4个同步任务
│   ├── config.py          # 统一配置
│   ├── exceptions.py      # 自定义异常
│   └── logging_config.py  # 日志配置
├── mcp/                   # 本地MCP服务 (11个工具)
├── skills/                # 7个研究Skill
├── tests/                 # 62+ 测试
├── audits/                # Phase 1审计文件
├── scripts/init_db.py     # 数据库初始化
├── check_progress.py      # 进度检查 (crontab每2小时)
└── agents/                # 多智能体治理文件
```

## MCP 工具列表

| 工具 | 功能 | 最大返回行数 |
|---|---|---|
| `search_security` | 搜索证券 | 20 (可分页) |
| `get_market_history` | 获取行情历史 | 500/symbol |
| `get_latest_quote` | 获取最新报价 | 50 symbols |
| `get_financial_statements` | 获取财务报表 | 1000 |
| `get_financial_metrics` | 获取财务指标 | 50 |
| `get_announcements` | 获取公告 | 50 (可分页) |
| `search_announcements` | 搜索公告 | 20 (可分页) |
| `compare_sources` | 多源对比 | 200 |
| `get_data_freshness` | 数据新鲜度 | 20 |
| `run_data_quality_check` | 运行DQ检查 | N/A |
| `export_dataset` | 导出数据集 | 100000 |

## 多智能体治理

| 角色 | 执行者 | 职责 |
|---|---|---|
| 项目经理 | Claude Code | 进度监控/风险/验收 |
| 需求管理专家 | Claude Code | 需求矩阵/覆盖度/缺口 |
| 实施工程师 | Cascade | 编码/修复/测试 |

## License

MIT
