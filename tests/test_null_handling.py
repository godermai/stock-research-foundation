"""Tests for null and empty value handling."""

import pytest
import pandas as pd
from src.models.dq_rules import default_registry, CheckSuite


class TestNullHandling:
    def test_no_null_symbols_pass(self):
        """DataFrame with no null symbols should pass DQ check."""
        df = pd.DataFrame({
            "symbol": ["600519.SH", "000001.SZ"],
            "name": ["贵州茅台", "平安银行"],
        })
        rule = default_registry.get("schema_no_null_symbols")
        result = rule.check_fn(table_name="security_master", df=df)
        assert result["result"] == "pass"

    def test_null_symbols_fail(self):
        """DataFrame with null symbols should fail DQ check."""
        df = pd.DataFrame({
            "symbol": ["600519.SH", None],
            "name": ["贵州茅台", "Unknown"],
        })
        rule = default_registry.get("schema_no_null_symbols")
        result = rule.check_fn(table_name="security_master", df=df)
        assert result["result"] == "fail"

    def test_empty_string_not_treated_as_null(self):
        """Empty strings in symbol should not be treated as null by isna()."""
        df = pd.DataFrame({
            "symbol": ["600519.SH", ""],
            "name": ["贵州茅台", "Unknown"],
        })
        rule = default_registry.get("schema_no_null_symbols")
        result = rule.check_fn(table_name="security_master", df=df)
        # Empty string is not NaN, so this should pass
        assert result["result"] == "pass"

    def test_no_duplicates_pass(self):
        """DataFrame with no duplicate keys should pass."""
        df = pd.DataFrame({
            "symbol": ["600519.SH", "000001.SZ"],
            "trade_date": ["2024-01-15", "2024-01-15"],
        })
        rule = default_registry.get("schema_no_duplicates")
        result = rule.check_fn(table_name="market_daily", df=df)
        assert result["result"] == "pass"

    def test_duplicates_fail(self):
        """DataFrame with duplicate keys should fail."""
        df = pd.DataFrame({
            "symbol": ["600519.SH", "600519.SH"],
            "trade_date": ["2024-01-15", "2024-01-15"],
        })
        rule = default_registry.get("schema_no_duplicates")
        result = rule.check_fn(table_name="market_daily", df=df)
        assert result["result"] == "fail"
