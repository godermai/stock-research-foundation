"""AKShare adapter — breadth collector and secondary verifier.

Handles:
- stock_zh_a_hist: daily market data (volume in hands, amount in yuan)
- stock_info_a_code_name: security list
- stock_individual_info_em: individual stock info
"""

import os
from datetime import datetime
from typing import Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ..normalize.symbols import normalize_symbol, infer_exchange, infer_board
from ..normalize.units import normalize_volume, normalize_amount


class AKShareAdapter:
    """Adapter for AKShare public-web data collection."""

    def __init__(self):
        self._ak = None

    @property
    def ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_stock_list(self) -> pd.DataFrame:
        """Fetch A-share stock code/name list."""
        df = self.ak.stock_info_a_code_name()
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_daily_hist(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """Fetch daily market history.

        symbol: bare 6-digit code (e.g. '600519')
        start_date/end_date: YYYYMMDD
        adjust: '' (raw), 'qfq', 'hfq'
        """
        df = self.ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust if adjust else "",
        )
        return df

    def normalize_security_master(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize stock_info_a_code_name to canonical security_master."""
        result = pd.DataFrame()
        # AKShare returns 'code' and 'name' columns
        result["source_symbol"] = df["code"]
        result["symbol"] = df["code"].apply(lambda x: normalize_symbol(x, source="akshare"))
        result["exchange"] = result["symbol"].str.split(".").str[1]
        result["asset_type"] = "stock"
        result["name"] = df["name"]
        result["status"] = "listed"
        result["source"] = "akshare"
        result["fetched_at"] = datetime.now().isoformat()
        result["board"] = df["code"].apply(lambda x: infer_board(x) or "unknown")
        return result

    def normalize_market_daily(
        self, df: pd.DataFrame, symbol: str, adjust: str = "raw"
    ) -> pd.DataFrame:
        """Normalize stock_zh_a_hist output to canonical market_daily."""
        result = pd.DataFrame()
        result["symbol"] = normalize_symbol(symbol, source="akshare")
        result["trade_date"] = pd.to_datetime(df["日期"]).dt.date
        result["open"] = df.get("开盘")
        result["high"] = df.get("最高")
        result["low"] = df.get("最低")
        result["close"] = df.get("收盘")
        result["turnover_rate"] = df.get("换手率")

        # Volume: AKShare 成交量 is in hands -> multiply by 100
        vol, vol_unit = normalize_volume(
            df.get("成交量"), source="akshare", original_unit="hands"
        )
        result["volume"] = vol
        result["volume_unit"] = vol_unit

        # Amount: AKShare 成交额 is already in yuan
        amt, amt_unit = normalize_amount(
            df.get("成交额"), source="akshare", original_unit="yuan"
        )
        result["amount"] = amt
        result["currency"] = "CNY"

        result["adjustment"] = adjust if adjust else "raw"
        result["source"] = "akshare"
        result["fetched_at"] = datetime.now().isoformat()
        return result
