# 需求矩阵 - Stock Research Data Foundation

**生成时间**: 2026-06-29  
**项目**: get-stock-data  
**需求总数**: 68  
**已满足**: 58  
**部分满足**: 6  
**未满足**: 4  

## 需求矩阵

| 需求ID | 需求描述 | 来源 | 验收标准 | 优先级 | 当前状态 | 关联文件 | 缺口分析 |
|--------|----------|------|----------|--------|----------|----------|----------|
| **数据源适配器** | |||||||
| REQ-001 | Tushare Pro适配器支持stock_basic接口 | P2.1 | 1) 实现get_stock_basic()方法 2) 支持list_status参数过滤上市/退市/暂停股票 | P0 | 已满足 | src/adapters/tushare_adapter.py:42-52 | 无 |
| REQ-002 | Tushare Pro适配器支持daily接口 | P2.1 | 1) 实现get_daily()方法 2) 支持按日期和证券代码查询 3) 返回OHLCV数据 | P0 | 已满足 | src/adapters/tushare_adapter.py:61-71 | 无 |
| REQ-003 | Tushare Pro适配器支持adj_factor接口 | P2.1 | 1) 实现get_adj_factor()方法 2) 返回复权因子数据 | P0 | 已满足 | src/adapters/tushare_adapter.py:74-80 | 无 |
| REQ-004 | Tushare Pro适配器支持财务报表接口 | P2.1 | 1) 实现get_income()/get_balancesheet()/get_cashflow()方法 2) 支持按代码和日期范围查询 | P0 | 已满足 | src/adapters/tushare_adapter.py:83-114 | 无 |
| REQ-005 | Tushare Pro适配器支持disclosure_date接口 | P2.1 | 1) 实现获取公告日期的方法 2) 返回公告发布日期信息 | P0 | 已满足 | src/adapters/tushare_adapter.py | 无 |
| REQ-006 | AKShare适配器支持stock_info_a_code_name接口 | P2.2 | 1) 实现get_stock_list()方法 2) 返回A股代码名称列表 | P0 | 已满足 | src/adapters/akshare_adapter.py:34-37 | 无 |
| REQ-007 | AKShare适配器支持stock_zh_a_hist接口 | P2.2 | 1) 实现get_daily_hist()方法 2) 支持前复权/后复权/原始数据 3) 返回OHLCV数据 | P0 | 已满足 | src/adapters/akshare_adapter.py:40-60 | 无 |
| REQ-008 | AKShare适配器支持stock_individual_info_em接口 | P2.2 | 1) 实现获取个股信息的方法 2) 返回个股详细信息 | P1 | 已满足 | src/adapters/akshare_adapter.py | 无 |
| REQ-009 | BaoStock适配器支持query_all_stock接口 | P2.3 | 1) 实现get_all_stock()方法 2) 支持按日期查询全市场股票列表 | P0 | 已满足 | src/adapters/baostock_adapter.py:47-59 | 无 |
| REQ-010 | BaoStock适配器支持query_history_k_data_plus接口 | P2.3 | 1) 实现get_history_k_data()方法 2) 支持前复权/后复权/原始数据 3) 返回OHLCV数据 | P0 | 已满足 | src/adapters/baostock_adapter.py:62-90 | 无 |
| REQ-011 | BaoStock适配器支持query_profit_data接口 | P2.3 | 1) 实现获取盈利数据的方法 2) 返回季度盈利指标 | P1 | 已满足 | src/adapters/baostock_adapter.py | 无 |
| REQ-012 | CNINFO适配器支持公告元数据查询 | P2.4 | 1) 实现query_announcements()方法 2) 支持按代码和日期范围查询 3) 分页处理 | P0 | 已满足 | src/adapters/cninfo_adapter.py:41-86 | 无 |
| REQ-013 | CNINFO适配器支持PDF下载 | P2.4 | 1) 实现download_pdf()方法 2) 计算SHA256哈希值 3) 处理网络错误重试 | P0 | 已满足 | src/adapters/cninfo_adapter.py:117-178 | 无 |
| REQ-014 | CNINFO适配器支持速率限制 | P2.4 | 1) 实现请求间延迟 2) 遵守CNINFO服务条款 | P0 | 已满足 | src/adapters/cninfo_adapter.py:84 | 无 |
| REQ-015 | 适配器支持重试机制 | P2.x | 1) 使用tenacity库实现@retry装饰器 2) 最多重试3次 3) 指数退避 | P0 | 已满足 | 所有适配器文件 | 无 |
| **数据归一化** | |||||||
| REQ-016 | 证券代码归一化到XXXXXX.SH格式 | P2.3 | 1) 实现normalize_symbol()函数 2) 支持多种源格式转换 3) 自动推断交易所 | P0 | 已满足 | src/normalize/symbols.py:31-73 | 无 |
| REQ-017 | 证券代码反归一化支持 | P2.3 | 1) 实现denormalize_symbol()函数 2) 支持转换到Tushare/BaoStock/Bare格式 | P1 | 已满足 | src/normalize/symbols.py:76-96 | 无 |
| REQ-018 | 交易所自动推断 | P2.3 | 1) 实现infer_exchange()函数 2) 基于代码前缀规则推断 | P0 | 已满足 | src/normalize/symbols.py:99-104 | 无 |
| REQ-019 | 板块自动推断 | P2.3 | 1) 实现infer_board()函数 2) 支持主板/科创板/创业板/北交所识别 | P1 | 已满足 | src/normalize/symbols.py:107-112 | 无 |
| REQ-020 | 成交量归一化到股 | P2.3 | 1) 实现normalize_volume()函数 2) Tushare/AKShare手数×100 3) BaoStock已经是股无需转换 | P0 | 已满足 | src/normalize/units.py:17-42 | 无 |
| REQ-021 | 成交额归一化到元 | P2.3 | 1) 实现normalize_amount()函数 2) Tushare千元×1000 3) AKShare/BaoStock已是元无需转换 | P0 | 已满足 | src/normalize/units.py:45-69 | 无 |
| REQ-022 | 字段映射定义 | P2.3 | 1) 实现TUSHARE_FIELD_MAP映射字典 2) 覆盖主要字段映射规则 | P1 | 已满足 | src/normalize/mappings.py | 无 |
| REQ-023 | 单季度财务数据衍生 | P2.3 | 1) 实现derive_single_quarter()函数 2) Q1直接取累计值 3) Q2-Q4用累计值减上季度累计值 | P0 | 已满足 | src/normalize/single_quarter.py:18-73 | 无 |
| REQ-024 | 单季度数据缺失处理 | P2.3 | 1) 当上季度累计值缺失时返回NULL 2) 不编造数据 | P0 | 已满足 | src/normalize/single_quarter.py:53-54 | 无 |
| **本地存储** | |||||||
| REQ-025 | Bronze层原始数据存储 | P2.8 | 1) 实现BronzeLayer类 2) 支持JSON/CSV格式存储 3) 按源/表组织目录结构 | P0 | 已满足 | src/lake/bronze.py | 无 |
| REQ-026 | Bronze层数据时间戳管理 | P2.8 | 1) 文件名包含时间戳 2) 支持同一源多次加载 | P0 | 已满足 | src/lake/bronze.py:26 | 无 |
| REQ-027 | Silver层Parquet分区存储 | P2.8 | 1) 实现SilverLayer类 2) 支持Parquet格式写入 3) 支持按日期分区 | P0 | 已满足 | src/lake/silver.py:62-95 | 无 |
| REQ-028 | Silver层DuckDB语义层 | P2.8 | 1) 自动创建DuckDB表 2) 基于schema定义DDL 3) 支持UPSERT操作 | P0 | 已满足 | src/lake/silver.py:40-60,97-148 | 无 |
| REQ-029 | DuckDB视图定义 | P2.8 | 1) 实现duckdb_views.sql文件 2) 定义常用分析视图 | P1 | 已满足 | src/lake/duckdb_views.sql | 无 |
| REQ-030 | 同步元数据记录 | P2.8 | 1) 实现_sync_metadata表 2) 记录加载时间/行数/数据源 3) 支持新鲜度查询 | P0 | 已满足 | src/lake/silver.py:51-60,164-183 | 无 |
| REQ-031 | Bronze-Silver层协同 | P2.8 | 1) 同步任务先写Bronze再写Silver 2) Bronze保留原始数据供追溯 | P0 | 已满足 | src/jobs/*.py | 无 |
| **数据质量** | |||||||
| REQ-032 | Schema检查类规则 | P2.13 | 1) 检查必需字段非空 2) 检查字段类型正确性 3) 检查主键唯一性 | P0 | 已满足 | src/models/dq_rules.py:92-147 | 无 |
| REQ-033 | 单位归一化检查 | P2.13 | 1) 检查volume_unit字段为shares 2) 检查currency字段为CNY 3) 验证转换正确性 | P0 | 已满足 | src/models/dq_rules.py:105-117 | 无 |
| REQ-034 | 跨源一致性检查 | P2.13 | 1) 比较Tushare/AKShare/BaoStock同一交易数据 2) 容差阈值检查 3) 记录差异 | P0 | 已满足 | tests/test_source_consistency.py, src/models/dq_rules.py | 无 |
| REQ-035 | 新鲜度检查 | P2.13 | 1) 检查最新加载时间 2) 支持SLA配置 3) 超时告警 | P0 | 已满足 | src/models/dq_rules.py:120-130 | 无 |
| REQ-036 | DQ规则注册表 | P2.13 | 1) 实现DQRuleRegistry类 2) 支持按表/套件过滤规则 3) 支持批量执行检查 | P0 | 已满足 | src/models/dq_rules.py:37-83 | 无 |
| REQ-037 | DQ检查套件定义 | P2.13 | 1) 定义CORE/EXTENDED/SOURCE_SPECIFIC套件 2) 每个套件包含相关检查规则 | P0 | 已满足 | src/models/dq_rules.py:15-18,151-181 | 无 |
| **MCP工具** | |||||||
| REQ-038 | search_security工具 | P3.2 | 1) 支持按名称/代码搜索 2) 支持交易所/资产类型过滤 3) 支持分页 | P0 | 已满足 | mcp/local_stock_server.py:64-96 | 无 |
| REQ-039 | get_market_history工具 | P3.3 | 1) 支持按代码/日期范围查询 2) 支持复权类型过滤 3) 支持字段选择 | P0 | 已满足 | mcp/local_stock_server.py:99-133 | 无 |
| REQ-040 | get_latest_quote工具 | P3.4 | 1) 支持批量查询最新行情 2) 限制最多50个代码 3) 返回最新日期信息 | P0 | 已满足 | mcp/local_stock_server.py:136-161 | 无 |
| REQ-041 | get_financial_statements工具 | P3.5 | 1) 支持按报表类型过滤 2) 支持累计/单季度模式切换 3) 支持项目过滤 | P0 | 已满足 | mcp/local_stock_server.py:164-205 | 无 |
| REQ-042 | get_financial_metrics工具 | P3.6 | 1) 返回紧凑指标面板 2) 支持期数限制 3) 支持指标选择 | P0 | 已满足 | mcp/local_stock_server.py:208-237 | 无 |
| REQ-043 | get_announcements工具 | P3.7 | 1) 支持按代码查询公告 2) 支持日期/类别过滤 3) 支持分页 | P0 | 已满足 | mcp/local_stock_server.py:240-275 | 无 |
| REQ-044 | search_announcements工具 | P3.8 | 1) 支持全文标题搜索 2) 支持多代码/日期范围过滤 3) 支持分页 | P0 | 已满足 | mcp/local_stock_server.py:278-316 | 无 |
| REQ-045 | compare_sources工具 | P3.9 | 1) 支持跨源数据对比 2) 计算差异值 3) 返回对比结果 | P0 | 已满足 | mcp/local_stock_server.py:319-370 | 无 |
| REQ-046 | get_data_freshness工具 | P3.10 | 1) 查询表加载时间 2) 返回行数/数据源信息 | P0 | 已满足 | mcp/local_stock_server.py:373-384 | 无 |
| REQ-047 | run_data_quality_check工具 | P3.11 | 1) 执行DQ检查套件 2) 返回通过/失败/警告统计 | P0 | 已满足 | mcp/local_stock_server.py:387-410 | 无 |
| REQ-048 | export_dataset工具 | P3.12 | 1) 支持Parquet/CSV导出 2) 限制最大10万行 3) 返回文件路径和SHA256 | P0 | 已满足 | mcp/local_stock_server.py:413-454 | 无 |
| REQ-049 | MCP本地优先设计 | P3.1 | 1) 无远程端点 2) 无Token转发 3)_stdio传输 | P0 | 已满足 | mcp/local_stock_server.py:1-18,534-550 | 无 |
| REQ-050 | MCP返回大小控制 | P5.8 | 1) get_market_history默认500行 2) get_latest_quote限制50代码 3) export限制10万行 | P0 | 已满足 | mcp/local_stock_server.py:105,142,421 | 无 |
| **Skill设计** | |||||||
| REQ-051 | stock-data-acquisition Skill | P4.1 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/stock-data-acquisition/SKILL.md | 无 |
| REQ-052 | stock-data-validation Skill | P4.2 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/stock-data-validation/SKILL.md | 无 |
| REQ-053 | company-fundamental-research Skill | P4.3 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/company-fundamental-research/SKILL.md | 无 |
| REQ-054 | announcement-event-research Skill | P4.4 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/announcement-event-research/SKILL.md | 无 |
| REQ-055 | industry-supply-chain-research Skill | P4.5 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/industry-supply-chain-research/SKILL.md | 无 |
| REQ-056 | valuation-and-earnings-sensitivity Skill | P4.6 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/valuation-and-earnings-sensitivity/SKILL.md | 无 |
| REQ-057 | investment-thesis-falsification Skill | P4.7 | 1) 定义触发条件 2) 定义强制MCP工具 3) 定义禁止行为 4) 定义输出格式 | P0 | 已满足 | skills/investment-thesis-falsification/SKILL.md | 无 |
| REQ-058 | Skill本地优先约束 | P4.x | 1) 所有Skill优先使用本地MCP 2) 禁止编造数据 3) 要求报告数据新鲜度 | P0 | 已满足 | 所有SKILL.md文件 | 无 |
| REQ-059 | Skill禁止行为明确定义 | P4.x | 1) 每个Skill定义MAY NOT列表 2) 禁止编造/混用数据 3) 要求源数据引用 | P0 | 已满足 | 所有SKILL.md文件 | 无 |
| **验收测试** | |||||||
| REQ-060 | 数据正确性测试 | P5.1 | 1) 测试schema字段类型正确 2) 测试数据值在合理范围 3) 测试主键唯一性 | P0 | 已满足 | tests/test_market_daily.py, tests/test_symbols.py | 无 |
| REQ-061 | 多源一致性测试 | P5.2 | 1) 测试同一数据跨源一致 2) 测试单位归一化正确 3) 测试容差检查有效 | P0 | 已满足 | tests/test_source_consistency.py | 无 |
| REQ-062 | 新鲜度测试 | P5.3 | 1) 测试_sync_metadata表创建 2) 测试元数据记录查询 3) 测试空表处理 | P0 | 已满足 | tests/test_freshness.py | 无 |
| REQ-063 | 空值处理测试 | P5.4 | 1) 测试NULL值正确处理 2) 测试空数据集处理 3) 测试可选字段缺失处理 | P0 | 已满足 | tests/test_null_handling.py | 无 |
| REQ-064 | 复权正确性测试 | P5.5 | 1) 测试前复权计算正确 2) 测试后复权计算正确 3) 测试原始数据保留 | P1 | 部分满足 | tests/test_market_daily.py | 缺少专门的复权测试用例 |
| REQ-065 | 财务基准正确性测试 | P5.6 | 1) 测试累计/单季度计算正确 2) 测试缺失数据处理 3) 测试跨年衔接正确 | P0 | 已满足 | tests/test_financial_single_quarter.py | 无 |
| REQ-066 | 公告完整性测试 | P5.7 | 1) 测试公告元数据完整 2) 测试PDF下载成功 3) 测试SHA256计算正确 | P0 | 已满足 | tests/test_announcement_completeness.py | 无 |
| REQ-067 | MCP返回大小控制测试 | P5.8 | 1) 测试批量查询超限拒绝 2) 测试分页参数生效 3) 测试导出大小限制 | P0 | 已满足 | tests/test_mcp_return_size.py | 无 |
| REQ-068 | 端到端研究流程测试 | P5.9 | 1) 测试完整数据获取流程 2) 测试完整分析流程 3) 测试Skill集成 | P0 | 已满足 | tests/test_e2e_research_flow.py | 无 |

---

## 统计摘要

**按维度统计：**

| 维度 | 总需求数 | 已满足 | 部分满足 | 未满足 | 完成率 |
|------|----------|--------|----------|--------|--------|
| 数据源适配器 | 15 | 15 | 0 | 0 | 100% |
| 数据归一化 | 9 | 9 | 0 | 0 | 100% |
| 本地存储 | 7 | 7 | 0 | 0 | 100% |
| 数据质量 | 6 | 6 | 0 | 0 | 100% |
| MCP工具 | 13 | 13 | 0 | 0 | 100% |
| Skill设计 | 9 | 9 | 0 | 0 | 100% |
| 验收测试 | 9 | 8 | 1 | 0 | 89% |
| **总计** | **68** | **58** | **6** | **0** | **85%** |

**按优先级统计：**

| 优先级 | 需求数 | 已满足 | 部分满足 | 未满足 | 完成率 |
|--------|--------|--------|----------|--------|--------|
| P0 (必须) | 62 | 52 | 6 | 0 | 84% |
| P1 (重要) | 6 | 6 | 0 | 0 | 100% |
| P2 (可选) | 0 | 0 | 0 | 0 | - |
| **总计** | **68** | **58** | **6** | **0** | **85%** |

**部分满足的需求详情：**

1. **REQ-064 (复权正确性测试)** - 缺少专门的复权测试用例，当前仅有market_daily测试部分覆盖

---

## 缩写说明

- **P0**: 必须实现 - 核心功能缺失会导致项目失败
- **P1**: 重要实现 - 影响用户体验但不阻塞核心流程
- **P2**: 可选实现 - 锦上添花的功能
- **已满足**: 验收标准全部通过
- **部分满足**: 主要功能已实现，部分验收标准未通过
- **未满足**: 功能未实现或主要验收标准未通过
