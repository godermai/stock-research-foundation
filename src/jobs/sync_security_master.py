"""Sync job: security_master.

Primary: Tushare stock_basic + stock_company
Verify: BaoStock query_all_stock
"""

import uuid
from datetime import datetime

from ..adapters.tushare_adapter import TushareAdapter
from ..adapters.baostock_adapter import BaoStockAdapter
from ..lake.bronze import BronzeLayer
from ..lake.silver import SilverLayer


def run_sync_security_master(
    tushare_token: str | None = None,
    verify_with_baostock: bool = True,
) -> dict:
    """Sync security_master from Tushare (primary) + BaoStock (verify).

    Returns summary dict with counts and status.
    """
    run_id = str(uuid.uuid4())[:8]
    bronze = BronzeLayer()
    silver = SilverLayer()

    result = {
        "run_id": run_id,
        "table": "security_master",
        "started_at": datetime.now().isoformat(),
        "tushare_rows": 0,
        "baostock_rows": 0,
        "merged_rows": 0,
        "status": "running",
    }

    try:
        # --- Tushare (primary) ---
        ts = TushareAdapter(token=tushare_token)

        # Fetch listed stocks
        df_listed = ts.get_stock_basic(list_status="L")
        df_listed_norm = ts.normalize_security_master(df_listed)

        # Fetch delisted stocks
        df_delisted = ts.get_stock_basic(list_status="D")
        df_delisted_norm = ts.normalize_security_master(df_delisted)

        # Fetch paused stocks
        df_paused = ts.get_stock_basic(list_status="P")
        df_paused_norm = ts.normalize_security_master(df_paused)

        # Combine
        import pandas as pd
        df_tushare = pd.concat(
            [df_listed_norm, df_delisted_norm, df_paused_norm],
            ignore_index=True
        )

        # Save raw to bronze
        bronze.write_dataframe("tushare", "security_master", df_tushare)

        result["tushare_rows"] = len(df_tushare)

        # --- BaoStock (verify) ---
        df_baostock = None
        if verify_with_baostock:
            today = datetime.now().strftime("%Y-%m-%d")
            with BaoStockAdapter() as bs:
                df_bs_raw = bs.get_all_stock(date=today)
                df_baostock = bs.normalize_security_master(df_bs_raw)
                bronze.write_dataframe("baostock", "security_master", df_baostock)
                result["baostock_rows"] = len(df_baostock)

        # --- Merge: Tushare primary, BaoStock fills gaps ---
        df_merged = df_tushare.copy()
        if df_baostock is not None and not df_baostock.empty:
            # Find symbols in BaoStock not in Tushare
            ts_symbols = set(df_tushare["symbol"])
            bs_only = df_baostock[~df_baostock["symbol"].isin(ts_symbols)]
            if not bs_only.empty:
                df_merged = pd.concat([df_merged, bs_only], ignore_index=True)

        # --- Write to silver (Parquet + DuckDB) ---
        silver.write_parquet("security_master", df_merged)
        silver.upsert_to_duckdb("security_master", df_merged)
        silver.record_sync(
            "security_master", "tushare+baostock",
            None, len(df_merged), run_id
        )

        result["merged_rows"] = len(df_merged)
        result["status"] = "completed"

    except Exception as e:
        result["status"] = f"failed: {e}"

    result["finished_at"] = datetime.now().isoformat()
    return result
