# Claude Code Task — Phase 1: 侦察审计

## 工作目录
`/Users/mai/CascadeProjects/get-stock-data`

## 你的任务范围
**只操作 `third_party/` 和 `audits/` 目录**，不要修改 `src/`、`mcp/`、`skills/`、`tests/`（另一个智能体在处理）。

## 任务清单

### Step 1: 克隆12个仓库到 `third_party/`
```bash
mkdir -p third_party
cd third_party
git clone --depth 1 https://github.com/akfamily/akshare.git
git clone --depth 1 https://github.com/waditu/tushare.git
git clone --depth 1 https://github.com/Micro-sheep/efinance.git
git clone --depth 1 https://github.com/mootdx/mootdx.git
git clone --depth 1 https://github.com/zer0quant/zer0share.git
git clone --depth 1 https://github.com/tycallen/TushareDB.git
git clone --depth 1 https://github.com/chenditc/investment_data.git
git clone --depth 1 https://github.com/zwldarren/akshare-one-mcp.git
git clone --depth 1 https://github.com/buuzzy/tushare_MCP.git
git clone --depth 1 https://github.com/tr1s7an/CnInfoReports.git
git clone --depth 1 https://github.com/legeling/Annualreport_tools.git
git clone --depth 1 https://github.com/atompilot/baostock-skill.git
```

### Step 2: 审计每个仓库
对每个仓库检查：
- `pyproject.toml` 或 `requirements.txt`（Python版本、依赖面）
- 主包目录结构
- 测试目录是否存在
- changelog/release metadata
- HTTP客户端、token、调度器、缓存、MCP工具相关源码

### Step 3: 产出3个审计文件

#### `audits/project_matrix.csv`
列：project, repo, stars, forks, last_release, license, python_version, has_tests, has_local_db, has_cache, has_scheduler, token_required, public_web_dependency, decision(Adopt/Fork/Borrow/Reject), notes

#### `audits/source_endpoint_catalog.md`
列出每个数据源项目的：
- 上游数据源（Tushare Pro / Eastmoney / CNINFO / BaoStock server 等）
- 主要接口/函数名
- 输出字段
- 是否需要token/cookie
- 已知稳定性问题

#### `audits/reuse_decisions.md`
对每个仓库给出：
- 决策类别（Adopt/Fork/Borrow/Reject）
- 决策理由（3-5句）
- 可复用的具体代码/模式
- 不可复用的部分
- 集成建议

## 完成后
更新 `task_tracker.md` 中 Phase 1 的 checkbox（将 `- [ ]` 改为 `- [x]`），仅改 P1.x 开头的行。
