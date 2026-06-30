"""BaoStock adapter — free secondary verifier.

Handles:
- query_all_stock: full stock list
- query_history_k_data_plus: historical daily K-line (volume already in shares)
- query_profit_data / query_growth_data: quarterly financial indicators

Important: BaoStock volume is in SHARES (not hands), unlike Tushare/AKShare.
"""

from datetime import datetime
from typing import Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ..normalize.symbols import normalize_symbol, denormalize_symbol, infer_board
from ..normalize.units import normalize_volume, normalize_amount


class BaoStockAdapter:
    """Adapter for BaoStock data service."""

    def __init__(self):
        self._logged_in = False

    def _login(self):
        if not self._logged_in:
            import baostock as bs
            bs.login()
            self._logged_in = True

    def _logout(self):
        if self._logged_in:
            import baostock as bs
            bs.logout()
            self._logged_in = False

    def __enter__(self):
        self._login()
        return self

    def __exit__(self, *args):
        self._logout()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_all_stock(self, date: str) -> pd.DataFrame:
        """Fetch all stock list for a given date.

        date: YYYY-MM-DD format
        """
        self._login()
        import baostock as bs
        rs = bs.query_all_stock(day=date)
        data = []
        while (rs.error_code == '0') and rs.next():
            data.append(rs.get_row_data)
        df = pd.DataFrame(data, columns=rs.fields)
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_history_k_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "2",  # 1=raw, 2=qfq(front), 3=hfq(back)
    ) -> pd.DataFrame:
        """Fetch historical daily K-line data.

        symbol: canonical e.g. 600519.SH (will be converted to sh.600519)
        start_date/end_date: YYYY-MM-DD
        adjust: '1' (raw), '2' (qfq), '3' (hfq)
        """
        self._login()
        import baostock as bs
        bs_code = denormalize_symbol(symbol, target="baostock")
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag=adjust,
        )
        data = []
        while (rs.error_code == '0') and rs.next():
            data.append(rs.get_row_data)
        df = pd.DataFrame(data, columns=rs.fields)
        return df

    def normalize_security_master(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize BaoStock all_stock to canonical security_master."""
        result = pd.DataFrame()
        # BaoStock code is like 'sh.600519'
        result["source_symbol"] = df["code"]
        result["symbol"] = df["code"].apply(lambda x: normalize_symbol(x, source="baostock"))
        result["exchange"] = result["symbol"].str.split(".").str[1]
        result["asset_type"] = "stock"
        result["name"] = df.get("code_name", "")
        result["status"] = "listed"
        result["source"] = "baostock"
        result["fetched_at"] = datetime.now().isoformat()
        bare_code = df["code"].str.split(".").str[1]
        result["board"] = bare_code.apply(lambda x: infer_board(x) or "unknown")
        return result

    def normalize_market_daily(
        self, df: pd.DataFrame, canonical_symbol: str, adjust: str = "raw"
    ) -> pd.DataFrame:
        """Normalize BaoStock K-line to canonical market_daily.

        BaoStock volume is already in shares — no conversion needed.
        """
        result = pd.DataFrame()
        result["symbol"] = canonical_symbol
        result["trade_date"] = pd.to_datetime(df["date"]).dt.date

        # BaoStock returns string values, convert to numeric
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                result[col] = pd.to_numeric(df[col], errors="coerce")

        # Volume: BaoStock is already in shares
        result["volume"] = pd.to_numeric(df.get("volume"), errors="coerce").astype("Int64")
        result["volume_unit"] = "shares"

        # Amount: BaoStock is in yuan
        result["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
        result["currency"] = "CNY"

        result["turnover_rate"] = pd.to_numeric(df.get("turn"), errors="coerce")
        result["pct_chg"] = pd.to_numeric(df.get("pctChg"), errors="coerce")

        adjust_map = {"1": "raw", "2": "qfq", "3": "hfq"}
        result["adjustment"] = adjust_map.get(adjust, "raw")
        result["source"] = "baostock"
        result["fetched_at"] = datetime.now().isoformat()
        return result
