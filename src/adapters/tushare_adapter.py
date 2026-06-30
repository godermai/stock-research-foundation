"""Tushare Pro adapter — primary structured upstream.

Handles:
- stock_basic: security master
- stock_company: company reference
- daily: daily market data (vol in hands, amount in thousand yuan)
- adj_factor: adjustment factors
- income/balancesheet/cashflow: financial statements
- disclosure_date: announcement dates
"""

import os
from datetime import datetime, date
from typing import Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ..normalize.symbols import normalize_symbol, infer_board
from ..normalize.units import normalize_volume, normalize_amount
from ..normalize.mappings import TUSHARE_FIELD_MAP


class TushareAdapter:
    """Adapter for Tushare Pro API."""

    def __init__(self, token: Optional[str] = None):
        self._token = token or os.getenv("TUSHARE_TOKEN")
        if not self._token:
            raise ValueError("TUSHARE_TOKEN not set. Get it from https://tushare.pro")
        self._api = None

    @property
    def api(self):
        if self._api is None:
            import tushare as ts
            ts.set_token(self._token)
            self._api = ts.pro_api()
        return self._api

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_stock_basic(self, list_status: str = "L") -> pd.DataFrame:
        """Fetch stock_basic for security_master.

        list_status: 'L' (listed), 'D' (delisted), 'P' (paused)
        """
        df = self.api.stock_basic(
            exchange="",
            list_status=list_status,
            fields="ts_code,symbol,name,area,industry,list_date,delist_date,list_status,exchange"
        )
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_stock_company(self) -> pd.DataFrame:
        """Fetch stock_company for company reference."""
        df = self.api.stock_company(fields="ts_code,exchange,chairman,manager,secretary,reg_capital,setup_date,province,city,introduction,website,email,office,employees,main_business,business_scope")
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_daily(self, trade_date: str, symbol: Optional[str] = None) -> pd.DataFrame:
        """Fetch daily market data.

        trade_date: YYYYMMDD format
        symbol: optional ts_code filter
        """
        kwargs = {"trade_date": trade_date}
        if symbol:
            kwargs["ts_code"] = symbol
        df = self.api.daily(**kwargs)
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_adj_factor(self, trade_date: str, symbol: Optional[str] = None) -> pd.DataFrame:
        """Fetch adjustment factors."""
        kwargs = {"trade_date": trade_date}
        if symbol:
            kwargs["ts_code"] = symbol
        df = self.api.adj_factor(**kwargs)
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_income(self, symbol: str, start_period: str, end_period: str) -> pd.DataFrame:
        """Fetch income statements.

        symbol: ts_code
        start_period/end_period: YYYYMMDD
        """
        df = self.api.income(
            ts_code=symbol,
            start_date=start_period,
            end_date=end_period,
        )
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_balancesheet(self, symbol: str, start_period: str, end_period: str) -> pd.DataFrame:
        """Fetch balance sheet statements."""
        df = self.api.balancesheet(
            ts_code=symbol,
            start_date=start_period,
            end_date=end_period,
        )
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def get_cashflow(self, symbol: str, start_period: str, end_period: str) -> pd.DataFrame:
        """Fetch cash flow statements."""
        df = self.api.cashflow(
            ts_code=symbol,
            start_date=start_period,
            end_date=end_period,
        )
        return df

    def normalize_security_master(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize stock_basic to canonical security_master schema."""
        result = pd.DataFrame()
        result["symbol"] = df["ts_code"]  # Already canonical format
        result["exchange"] = df.get("exchange", "")
        result["asset_type"] = "stock"
        result["name"] = df["name"]
        result["list_date"] = df.get("list_date")
        result["delist_date"] = df.get("delist_date")
        result["status"] = df["list_status"].map({
            "L": "listed",
            "D": "delisted",
            "P": "paused",
        }).fillna("unknown")
        result["source"] = "tushare"
        result["fetched_at"] = datetime.now().isoformat()
        result["source_symbol"] = df.get("ts_code")
        result["board"] = df["ts_code"].str[:2].apply(
            lambda x: infer_board(x) or "unknown"
        )
        result["industry_name"] = df.get("industry")
        return result

    def normalize_market_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize daily data to canonical market_daily schema."""
        result = pd.DataFrame()
        result["symbol"] = df["ts_code"]
        result["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d").dt.date
        result["open"] = df.get("open")
        result["high"] = df.get("high")
        result["low"] = df.get("low")
        result["close"] = df.get("close")
        result["pre_close"] = df.get("pre_close")
        result["change"] = df.get("change")
        result["pct_chg"] = df.get("pct_chg")
        result["turnover_rate"] = df.get("turnover_rate")

        # Volume: Tushare vol is in hands -> multiply by 100
        vol, vol_unit = normalize_volume(
            df.get("vol"), source="tushare", original_unit="hands"
        )
        result["volume"] = vol
        result["volume_unit"] = vol_unit

        # Amount: Tushare amount is in thousand yuan -> multiply by 1000
        amt, amt_unit = normalize_amount(
            df.get("amount"), source="tushare", original_unit="thousand_yuan"
        )
        result["amount"] = amt
        result["currency"] = "CNY"

        result["adjustment"] = "raw"
        result["source"] = "tushare"
        result["fetched_at"] = datetime.now().isoformat()
        return result
