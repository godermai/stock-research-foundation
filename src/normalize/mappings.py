"""Source-to-schema field mappings.

Maps source-specific field names to canonical schema field names.
"""

# Tushare field -> canonical field
TUSHARE_FIELD_MAP = {
    # security_master
    "ts_code": "symbol",
    "name": "name",
    "list_date": "list_date",
    "delist_date": "delist_date",
    # market_daily
    "trade_date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "vol": "volume",        # in hands, needs *100
    "amount": "amount",     # in thousand yuan, needs *1000
    "pre_close": "pre_close",
    "change": "change",
    "pct_chg": "pct_chg",
    "turnover_rate": "turnover_rate",
    "adj_factor": "adj_factor",
    # financial_statement
    "end_date": "report_period",
    "ann_date": "announcement_date",
    "f_ann_date": "f_ann_date",
    "update_flag": "fs_version",
}

# AKShare field -> canonical field
AKSHARE_FIELD_MAP = {
    # market_daily (stock_zh_a_hist)
    "日期": "trade_date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",       # in hands, needs *100
    "成交额": "amount",        # in yuan
    "换手率": "turnover_rate",
    # security_master
    "代码": "source_symbol",
    "名称": "name",
}

# BaoStock field -> canonical field
BAOSTOCK_FIELD_MAP = {
    # market_daily
    "date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",       # already in shares
    "amount": "amount",       # in yuan
    # security_master
    "code": "source_symbol",  # sh.600519 format
    "code_name": "name",
    "ipoDate": "list_date",
    "outDate": "delist_date",
}


# Reverse maps for debugging
def reverse_map(m: dict) -> dict:
    return {v: k for k, v in m.items()}


TUSHARE_REVERSE_MAP = reverse_map(TUSHARE_FIELD_MAP)
AKSHARE_REVERSE_MAP = reverse_map(AKSHARE_FIELD_MAP)
BAOSTOCK_REVERSE_MAP = reverse_map(BAOSTOCK_FIELD_MAP)
