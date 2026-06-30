-- DuckDB semantic layer views
-- These views provide convenient analytical access over the canonical tables.

-- Latest security master (non-delisted)
CREATE OR REPLACE VIEW v_active_securities AS
SELECT *
FROM security_master
WHERE status = 'listed'
ORDER BY symbol;

-- Market daily with adjustment factor joined
CREATE OR REPLACE VIEW v_market_daily_with_adj AS
SELECT
    m.symbol,
    m.trade_date,
    m.open,
    m.high,
    m.low,
    m.close,
    m.volume,
    m.amount,
    m.adjustment,
    m.adj_factor,
    m.turnover_rate,
    m.pct_chg,
    m.source,
    s.name,
    s.board,
    s.industry_name
FROM market_daily m
LEFT JOIN security_master s ON m.symbol = s.symbol
WHERE m.adjustment = 'raw';

-- Latest trade date per symbol
CREATE OR REPLACE VIEW v_latest_trade_date AS
SELECT symbol, MAX(trade_date) AS latest_date
FROM market_daily
GROUP BY symbol;

-- Financial statements pivoted (income statement key items)
CREATE OR REPLACE VIEW v_income_summary AS
SELECT
    symbol,
    report_period,
    statement_type,
    cumulative_or_single_quarter,
    MAX(CASE WHEN item_code = 'total_revenue' THEN value END) AS total_revenue,
    MAX(CASE WHEN item_code = 'operating_profit' THEN value END) AS operating_profit,
    MAX(CASE WHEN item_code = 'net_profit' THEN value END) AS net_profit,
    MAX(CASE WHEN item_code = 'n_income_attr_p' THEN value END) AS net_profit_attr_parent,
    source
FROM financial_statement
WHERE statement_type = 'income'
GROUP BY symbol, report_period, statement_type, cumulative_or_single_quarter, source
ORDER BY symbol, report_period;

-- Announcement counts by symbol and date
CREATE OR REPLACE VIEW v_announcement_counts AS
SELECT
    symbol,
    announcement_date,
    COUNT(*) AS announcement_count,
    COUNT(CASE WHEN download_status = 'downloaded' THEN 1 END) AS downloaded_count,
    COUNT(CASE WHEN parse_status = 'parsed' THEN 1 END) AS parsed_count
FROM announcement
GROUP BY symbol, announcement_date
ORDER BY symbol, announcement_date DESC;

-- Data freshness summary
CREATE OR REPLACE VIEW v_freshness_summary AS
SELECT
    table_name,
    source,
    MAX(latest_fetched_at) AS last_sync,
    MAX(latest_trade_date) AS latest_data_date,
    SUM(row_count) AS total_rows_loaded
FROM _sync_metadata
GROUP BY table_name, source
ORDER BY table_name, source;
