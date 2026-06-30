"""Sync job: market_daily.

Primary: Tushare daily + adj_factor
Secondary: AKShare stock_zh_a_hist
Verifier: BaoStock query_history_k_data_plus
Output: volume in shares, amount in CNY
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from ..adapters.tushare_adapter import TushareAdapter
from ..adapters.akshare_adapter import AKShareAdapter
from ..adapters.baostock_adapter import BaoStockAdapter
from ..lake.bronze import BronzeLayer
from ..lake.silver import SilverLayer


def run_sync_market_daily(
    trade_date: Optional[str] = None,
    symbols: Optional[list[str]] = None,
    tushare_token: str | None = None,
    verify_with_baostock: bool = False,
    verify_with_akshare: bool = False,
) -> dict:
    """Sync market_daily for a given trade date.

    trade_date: YYYYMMDD format. If None, uses today.
    symbols: list of canonical symbols. If None, syncs all from security_master.
    """
    run_id = str(uuid.uuid4())[:8]
    bronze = BronzeLayer()
    silver = SilverLayer()

    if trade_date is None:
        trade_date = datetime.now().strftime("%Y%m%d")

    result = {
        "run_id": run_id,
        "table": "market_daily",
        "trade_date": trade_date,
        "started_at": datetime.now().isoformat(),
        "tushare_rows": 0,
        "akshare_rows": 0,
        "baostock_rows": 0,
        "merged_rows": 0,
        "status": "running",
    }

    try:
        # --- Tushare (primary) ---
        ts = TushareAdapter(token=tushare_token)

        if symbols:
            all_dfs = []
            for sym in symbols:
                df = ts.get_daily(trade_date=trade_date, symbol=sym)
                all_dfs.append(df)
            df_ts_raw = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        else:
            df_ts_raw = ts.get_daily(trade_date=trade_date)

        if not df_ts_raw.empty:
            df_ts = ts.normalize_market_daily(df_ts_raw)
            bronze.write_dataframe("tushare", "market_daily", df_ts_raw, suffix=f"_{trade_date}")
            result["tushare_rows"] = len(df_ts)

            # Fetch adj_factor
            try:
                df_adj = ts.get_adj_factor(trade_date=trade_date)
                if not df_adj.empty:
                    adj_map = dict(zip(df_adj["ts_code"], df_adj["adj_factor"]))
                    df_ts["adj_factor"] = df_ts["symbol"].map(adj_map)
            except Exception:
                pass  # adj_factor is optional
        else:
            df_ts = pd.DataFrame()

        # --- AKShare (secondary, optional) ---
        df_ak = pd.DataFrame()
        if verify_with_akshare and symbols:
            ak = AKShareAdapter()
            ak_dfs = []
            for sym in symbols:
                try:
                    bare_code = sym.split(".")[0]
                    df_ak_raw = ak.get_daily_hist(
                        symbol=bare_code,
                        start_date=trade_date,
                        end_date=trade_date,
                        adjust="",
                    )
                    if not df_ak_raw.empty:
                        df_ak_norm = ak.normalize_market_daily(df_ak_raw, bare_code, adjust="raw")
                        ak_dfs.append(df_ak_norm)
                except Exception:
                    pass
            if ak_dfs:
                df_ak = pd.concat(ak_dfs, ignore_index=True)
                result["akshare_rows"] = len(df_ak)

        # --- BaoStock (verifier, optional) ---
        df_bs = pd.DataFrame()
        if verify_with_baostock and symbols:
            bs = BaoStockAdapter()
            bs_dfs = []
            date_iso = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
            for sym in symbols:
                try:
                    df_bs_raw = bs.get_history_k_data(
                        sym, start_date=date_iso, end_date=date_iso, adjust="1"
                    )
                    if not df_bs_raw.empty:
                        df_bs_norm = bs.normalize_market_daily(df_bs_raw, sym, adjust="1")
                        bs_dfs.append(df_bs_norm)
                except Exception:
                    pass
            if bs_dfs:
                df_bs = pd.concat(bs_dfs, ignore_index=True)
                result["baostock_rows"] = len(df_bs)

        # --- Merge: Tushare primary ---
        df_merged = df_ts if not df_ts.empty else pd.DataFrame()

        # Write to silver
        if not df_merged.empty:
            silver.write_parquet("market_daily", df_merged, partition_col="trade_date")
            silver.upsert_to_duckdb("market_daily", df_merged)
            silver.record_sync(
                "market_daily", "tushare",
                trade_date, len(df_merged), run_id
            )

        result["merged_rows"] = len(df_merged)
        result["status"] = "completed"

    except Exception as e:
        result["status"] = f"failed: {e}"

    result["finished_at"] = datetime.now().isoformat()
    return result
