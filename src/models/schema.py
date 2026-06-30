"""Canonical schema definitions for the stock research data foundation.

Four canonical tables as specified in the architecture document:
- security_master
- market_daily
- financial_statement
- announcement
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    CONVERTIBLE_BOND = "convertible_bond"
    INDEX = "index"
    FUND = "fund"


class Adjustment(str, Enum):
    RAW = "raw"
    QFQ = "qfq"  # forward-adjusted
    HFQ = "hfq"  # backward-adjusted


class StatementType(str, Enum):
    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"


class CumulativeOrSingle(str, Enum):
    CUMULATIVE = "cumulative"
    SINGLE_QUARTER = "single_quarter"


class Source(str, Enum):
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    CNINFO = "cninfo"
    SSE = "sse"
    SZSE = "szse"
    BSE = "bse"
    HKEX = "hkex"


@dataclass
class ColumnDef:
    name: str
    dtype: str  # DuckDB type
    nullable: bool = True
    description: str = ""


@dataclass
class TableDef:
    name: str
    columns: list[ColumnDef]
    partition_by: list[str] = field(default_factory=list)
    description: str = ""


SECURITY_MASTER_COLUMNS = [
    ColumnDef("symbol", "VARCHAR", nullable=False, description="Canonical symbol e.g. 600519.SH"),
    ColumnDef("exchange", "VARCHAR", nullable=False, description="SSE/SZSE/BSE/HKEX"),
    ColumnDef("asset_type", "VARCHAR", nullable=False, description="stock/etf/bond/convertible_bond/index/fund"),
    ColumnDef("name", "VARCHAR", nullable=False, description="Security name in Chinese"),
    ColumnDef("list_date", "DATE", description="Listing date"),
    ColumnDef("delist_date", "DATE", description="Delisting date if applicable"),
    ColumnDef("status", "VARCHAR", nullable=False, description="listed/delisted/suspended/paused"),
    ColumnDef("source", "VARCHAR", nullable=False, description="Data source"),
    ColumnDef("fetched_at", "TIMESTAMP", nullable=False, description="Fetch timestamp"),
    # Recommended extras
    ColumnDef("source_symbol", "VARCHAR", description="Original symbol from source"),
    ColumnDef("name_en", "VARCHAR", description="English name if available"),
    ColumnDef("currency", "VARCHAR", description="CNY/HKD etc"),
    ColumnDef("is_st", "BOOLEAN", description="Is ST or *ST"),
    ColumnDef("board", "VARCHAR", description="main/star/chinext/bse"),
    ColumnDef("industry_code", "VARCHAR", description="Industry classification code"),
    ColumnDef("industry_name", "VARCHAR", description="Industry classification name"),
    ColumnDef("row_hash", "VARCHAR", description="Row content hash for dedup"),
    ColumnDef("valid_from", "TIMESTAMP", description="Row validity start"),
    ColumnDef("valid_to", "TIMESTAMP", description="Row validity end (NULL = current)"),
]

MARKET_DAILY_COLUMNS = [
    ColumnDef("symbol", "VARCHAR", nullable=False, description="Canonical symbol"),
    ColumnDef("trade_date", "DATE", nullable=False, description="Trading date"),
    ColumnDef("open", "DOUBLE", description="Open price"),
    ColumnDef("high", "DOUBLE", description="High price"),
    ColumnDef("low", "DOUBLE", description="Low price"),
    ColumnDef("close", "DOUBLE", description="Close price"),
    ColumnDef("volume", "BIGINT", description="Volume in SHARES (canonical)"),
    ColumnDef("amount", "DOUBLE", description="Amount in CNY (canonical)"),
    ColumnDef("adjustment", "VARCHAR", nullable=False, description="raw/qfq/hfq"),
    ColumnDef("source", "VARCHAR", nullable=False),
    ColumnDef("fetched_at", "TIMESTAMP", nullable=False),
    # Recommended extras
    ColumnDef("pre_close", "DOUBLE", description="Previous close"),
    ColumnDef("change", "DOUBLE", description="Price change"),
    ColumnDef("pct_chg", "DOUBLE", description="Percentage change"),
    ColumnDef("turnover_rate", "DOUBLE", description="Turnover rate"),
    ColumnDef("adj_factor", "DOUBLE", description="Adjustment factor"),
    ColumnDef("volume_unit", "VARCHAR", description="Original volume unit before normalization"),
    ColumnDef("currency", "VARCHAR", description="Currency code"),
    ColumnDef("is_suspended", "BOOLEAN", description="Was suspended on this date"),
    ColumnDef("row_hash", "VARCHAR", description="Row content hash"),
]

FINANCIAL_STATEMENT_COLUMNS = [
    ColumnDef("symbol", "VARCHAR", nullable=False),
    ColumnDef("report_period", "DATE", nullable=False, description="Report end date e.g. 2024-12-31"),
    ColumnDef("announcement_date", "DATE", description="Announcement date"),
    ColumnDef("statement_type", "VARCHAR", nullable=False, description="income/balance/cashflow"),
    ColumnDef("item_code", "VARCHAR", nullable=False, description="Financial item code"),
    ColumnDef("item_name", "VARCHAR", nullable=False, description="Financial item name"),
    ColumnDef("value", "DOUBLE", description="Financial value"),
    ColumnDef("currency", "VARCHAR", description="Currency"),
    ColumnDef("cumulative_or_single_quarter", "VARCHAR", nullable=False, description="cumulative/single_quarter"),
    ColumnDef("source", "VARCHAR", nullable=False),
    ColumnDef("fetched_at", "TIMESTAMP", nullable=False),
    # Recommended extras
    ColumnDef("statement_standard", "VARCHAR", description="Accounting standard"),
    ColumnDef("source_item_name", "VARCHAR", description="Original item name from source"),
    ColumnDef("unit", "VARCHAR", description="Original unit"),
    ColumnDef("f_ann_date", "DATE", description="Final announcement date"),
    ColumnDef("report_type", "VARCHAR", description="Report type classification"),
    ColumnDef("fs_version", "VARCHAR", description="Statement version"),
    ColumnDef("lineage_run_id", "VARCHAR", description="ETL run ID for lineage"),
    ColumnDef("row_hash", "VARCHAR", description="Row content hash"),
]

ANNOUNCEMENT_COLUMNS = [
    ColumnDef("symbol", "VARCHAR", nullable=False),
    ColumnDef("announcement_id", "VARCHAR", nullable=False, description="Unique announcement ID"),
    ColumnDef("title", "VARCHAR", nullable=False, description="Announcement title"),
    ColumnDef("announcement_date", "DATE", nullable=False, description="Announcement date"),
    ColumnDef("category", "VARCHAR", description="Category"),
    ColumnDef("source_url", "VARCHAR", description="Original URL"),
    ColumnDef("local_path", "VARCHAR", description="Local file path"),
    ColumnDef("content_hash", "VARCHAR", description="SHA256 of content"),
    ColumnDef("source", "VARCHAR", nullable=False),
    ColumnDef("fetched_at", "TIMESTAMP", nullable=False),
    # Recommended extras
    ColumnDef("exchange", "VARCHAR", description="Exchange"),
    ColumnDef("language", "VARCHAR", description="Language"),
    ColumnDef("pdf_sha256", "VARCHAR", description="PDF file SHA256"),
    ColumnDef("download_status", "VARCHAR", description="downloaded/failed/skipped"),
    ColumnDef("parse_status", "VARCHAR", description="parsed/failed/pending"),
    ColumnDef("text_path", "VARCHAR", description="Extracted text path"),
    ColumnDef("ocr_status", "VARCHAR", description="ocr_done/ocr_failed/not_needed"),
    ColumnDef("is_amendment", "BOOLEAN", description="Is amendment/correction"),
]


TABLE_DEFINITIONS = {
    "security_master": TableDef(
        name="security_master",
        columns=SECURITY_MASTER_COLUMNS,
        description="Canonical security master with listing status and classification",
    ),
    "market_daily": TableDef(
        name="market_daily",
        columns=MARKET_DAILY_COLUMNS,
        partition_by=["trade_date"],
        description="Daily market data with OHLCV in canonical units (shares, CNY)",
    ),
    "financial_statement": TableDef(
        name="financial_statement",
        columns=FINANCIAL_STATEMENT_COLUMNS,
        partition_by=["report_period"],
        description="Normalized long-form financial statements with lineage",
    ),
    "announcement": TableDef(
        name="announcement",
        columns=ANNOUNCEMENT_COLUMNS,
        partition_by=["announcement_date"],
        description="Announcement metadata with PDF download tracking",
    ),
}


# Pydantic-style models for validation (using dataclasses for simplicity)

@dataclass
class SecurityMaster:
    symbol: str
    exchange: str
    asset_type: str
    name: str
    status: str
    source: str
    fetched_at: str
    list_date: Optional[str] = None
    delist_date: Optional[str] = None
    source_symbol: Optional[str] = None
    name_en: Optional[str] = None
    currency: Optional[str] = None
    is_st: Optional[bool] = None
    board: Optional[str] = None
    industry_code: Optional[str] = None
    industry_name: Optional[str] = None
    row_hash: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


@dataclass
class MarketDaily:
    symbol: str
    trade_date: str
    adjustment: str
    source: str
    fetched_at: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    amount: Optional[float] = None
    pre_close: Optional[float] = None
    change: Optional[float] = None
    pct_chg: Optional[float] = None
    turnover_rate: Optional[float] = None
    adj_factor: Optional[float] = None
    volume_unit: Optional[str] = None
    currency: Optional[str] = None
    is_suspended: Optional[bool] = None
    row_hash: Optional[str] = None


@dataclass
class FinancialStatement:
    symbol: str
    report_period: str
    statement_type: str
    item_code: str
    item_name: str
    cumulative_or_single_quarter: str
    source: str
    fetched_at: str
    announcement_date: Optional[str] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    statement_standard: Optional[str] = None
    source_item_name: Optional[str] = None
    unit: Optional[str] = None
    f_ann_date: Optional[str] = None
    report_type: Optional[str] = None
    fs_version: Optional[str] = None
    lineage_run_id: Optional[str] = None
    row_hash: Optional[str] = None


@dataclass
class Announcement:
    symbol: str
    announcement_id: str
    title: str
    announcement_date: str
    source: str
    fetched_at: str
    category: Optional[str] = None
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    content_hash: Optional[str] = None
    exchange: Optional[str] = None
    language: Optional[str] = None
    pdf_sha256: Optional[str] = None
    download_status: Optional[str] = None
    parse_status: Optional[str] = None
    text_path: Optional[str] = None
    ocr_status: Optional[str] = None
    is_amendment: Optional[bool] = None
