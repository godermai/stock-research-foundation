"""Sync job: financial_statement.

Primary: Tushare income/balancesheet/cashflow + disclosure dates
Verify: CNINFO announcement ledger
Derive: single-quarter rows locally
"""

import uuid
from datetime import datetime
from typing import Optional

import pandas as pd

from ..adapters.tushare_adapter import TushareAdapter
from ..normalize.single_quarter import derive_single_quarter
from ..lake.bronze import BronzeLayer
from ..lake.silver import SilverLayer


def run_sync_financials(
    symbol: str,
    start_period: str,
    end_period: str,
    tushare_token: str | None = None,
) -> dict:
    """Sync financial statements for a symbol.

    symbol: canonical e.g. 600519.SH
    start_period/end_period: YYYYMMDD
    """
    run_id = str(uuid.uuid4())[:8]
    bronze = BronzeLayer()
    silver = SilverLayer()

    result = {
        "run_id": run_id,
        "table": "financial_statement",
        "symbol": symbol,
        "started_at": datetime.now().isoformat(),
        "income_rows": 0,
        "balance_rows": 0,
        "cashflow_rows": 0,
        "single_quarter_rows": 0,
        "total_rows": 0,
        "status": "running",
    }

    try:
        ts = TushareAdapter(token=tushare_token)
        all_statements = []

        # Fetch income statements
        df_income = ts.get_income(symbol, start_period, end_period)
        if not df_income.empty:
            bronze.write_dataframe("tushare", "financial_income", df_income, suffix=f"_{symbol}")
            income_norm = _normalize_financial(df_income, symbol, "income")
            all_statements.append(income_norm)
            result["income_rows"] = len(income_norm)

        # Fetch balance sheet
        df_balance = ts.get_balancesheet(symbol, start_period, end_period)
        if not df_balance.empty:
            bronze.write_dataframe("tushare", "financial_balance", df_balance, suffix=f"_{symbol}")
            balance_norm = _normalize_financial(df_balance, symbol, "balance")
            all_statements.append(balance_norm)
            result["balance_rows"] = len(balance_norm)

        # Fetch cash flow
        df_cashflow = ts.get_cashflow(symbol, start_period, end_period)
        if not df_cashflow.empty:
            bronze.write_dataframe("tushare", "financial_cashflow", df_cashflow, suffix=f"_{symbol}")
            cashflow_norm = _normalize_financial(df_cashflow, symbol, "cashflow")
            all_statements.append(cashflow_norm)
            result["cashflow_rows"] = len(cashflow_norm)

        if not all_statements:
            result["status"] = "completed"
            result["total_rows"] = 0
            result["finished_at"] = datetime.now().isoformat()
            return result

        # Combine all statements
        df_all = pd.concat(all_statements, ignore_index=True)

        # Derive single-quarter values
        df_with_sq = derive_single_quarter(df_all)
        sq_count = len(df_with_sq[df_with_sq["cumulative_or_single_quarter"] == "single_quarter"])
        result["single_quarter_rows"] = sq_count

        # Write to silver
        silver.write_parquet("financial_statement", df_with_sq, partition_col="report_period")
        silver.upsert_to_duckdb("financial_statement", df_with_sq)
        silver.record_sync(
            "financial_statement", "tushare",
            end_period, len(df_with_sq), run_id
        )

        result["total_rows"] = len(df_with_sq)
        result["status"] = "completed"

    except Exception as e:
        result["status"] = f"failed: {e}"

    result["finished_at"] = datetime.now().isoformat()
    return result


def _normalize_financial(df: pd.DataFrame, symbol: str, statement_type: str) -> pd.DataFrame:
    """Normalize Tushare financial statement to canonical long-form.

    Tushare returns wide-format with each financial item as a column.
    We melt to long-form with item_code and item_name.
    """
    # Columns that are metadata, not financial items
    meta_cols = {
        "ts_code", "ann_date", "f_ann_date", "end_date", "update_flag",
        "report_type", "comp_type", "currency", "name",
    }

    # Identify financial item columns
    item_cols = [c for c in df.columns if c not in meta_cols]

    # Melt to long format
    df_long = df.melt(
        id_vars=[c for c in df.columns if c in meta_cols],
        value_vars=item_cols,
        var_name="item_code",
        value_name="value",
    )

    # Build canonical columns
    result = pd.DataFrame()
    result["symbol"] = symbol
    result["report_period"] = pd.to_datetime(
        df_long["end_date"], format="%Y%m%d"
    ).dt.date if "end_date" in df_long.columns else None
    result["announcement_date"] = pd.to_datetime(
        df_long.get("ann_date"), format="%Y%m%d", errors="coerce"
    ).dt.date if "ann_date" in df_long.columns else None
    result["statement_type"] = statement_type
    result["item_code"] = df_long["item_code"]
    result["item_name"] = df_long["item_code"]  # Use code as name; can map later
    result["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    result["currency"] = df_long.get("currency", "CNY")
    result["cumulative_or_single_quarter"] = "cumulative"
    result["source"] = "tushare"
    result["fetched_at"] = datetime.now().isoformat()
    result["f_ann_date"] = pd.to_datetime(
        df_long.get("f_ann_date"), format="%Y%m%d", errors="coerce"
    ).dt.date if "f_ann_date" in df_long.columns else None
    result["report_type"] = df_long.get("report_type")
    result["fs_version"] = df_long.get("update_flag")
    result["lineage_run_id"] = None
    result["source_item_name"] = df_long["item_code"]

    return result
