"""Tests for single-quarter financial derivation."""

import pytest
import pandas as pd
from src.normalize.single_quarter import derive_single_quarter


class TestDeriveSingleQuarter:
    def test_q1_unchanged(self):
        """Q1 single_quarter should equal cumulative."""
        df = pd.DataFrame({
            "symbol": ["600519.SH"] * 1,
            "report_period": ["2024-03-31"],
            "statement_type": ["income"],
            "item_code": ["total_revenue"],
            "item_name": ["total_revenue"],
            "value": [100.0],
            "cumulative_or_single_quarter": ["cumulative"],
            "source": ["tushare"],
            "fetched_at": ["2024-04-01T10:00:00"],
        })
        result = derive_single_quarter(df)
        sq_rows = result[result["cumulative_or_single_quarter"] == "single_quarter"]
        assert len(sq_rows) == 1
        assert sq_rows.iloc[0]["value"] == 100.0

    def test_q2_subtracts_q1(self):
        """Q2 single_quarter = Q2_cumulative - Q1_cumulative."""
        df = pd.DataFrame({
            "symbol": ["600519.SH", "600519.SH"],
            "report_period": ["2024-03-31", "2024-06-30"],
            "statement_type": ["income", "income"],
            "item_code": ["total_revenue", "total_revenue"],
            "item_name": ["total_revenue", "total_revenue"],
            "value": [100.0, 250.0],
            "cumulative_or_single_quarter": ["cumulative", "cumulative"],
            "source": ["tushare", "tushare"],
            "fetched_at": ["2024-04-01T10:00:00", "2024-07-01T10:00:00"],
        })
        result = derive_single_quarter(df)
        sq_rows = result[
            (result["cumulative_or_single_quarter"] == "single_quarter") &
            (result["report_period"] == "2024-06-30")
        ]
        assert len(sq_rows) == 1
        assert sq_rows.iloc[0]["value"] == 150.0  # 250 - 100

    def test_q4_subtracts_q3(self):
        """Q4 single_quarter = Q4_cumulative - Q3_cumulative."""
        df = pd.DataFrame({
            "symbol": ["600519.SH"] * 4,
            "report_period": ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"],
            "statement_type": ["income"] * 4,
            "item_code": ["net_profit"] * 4,
            "item_name": ["net_profit"] * 4,
            "value": [50.0, 120.0, 200.0, 300.0],
            "cumulative_or_single_quarter": ["cumulative"] * 4,
            "source": ["tushare"] * 4,
            "fetched_at": ["2024-04-01T10:00:00"] * 4,
        })
        result = derive_single_quarter(df)
        sq_rows = result[
            (result["cumulative_or_single_quarter"] == "single_quarter") &
            (result["report_period"] == "2024-12-31")
        ]
        assert len(sq_rows) == 1
        assert sq_rows.iloc[0]["value"] == 100.0  # 300 - 200

    def test_missing_prev_q_is_null(self):
        """If previous cumulative is missing, single_quarter should be None."""
        df = pd.DataFrame({
            "symbol": ["600519.SH"],
            "report_period": ["2024-06-30"],
            "statement_type": ["income"],
            "item_code": ["total_revenue"],
            "item_name": ["total_revenue"],
            "value": [250.0],
            "cumulative_or_single_quarter": ["cumulative"],
            "source": ["tushare"],
            "fetched_at": ["2024-07-01T10:00:00"],
        })
        result = derive_single_quarter(df)
        sq_rows = result[
            (result["cumulative_or_single_quarter"] == "single_quarter") &
            (result["report_period"] == "2024-06-30")
        ]
        assert len(sq_rows) == 1
        assert pd.isna(sq_rows.iloc[0]["value"])

    def test_empty_dataframe(self):
        """Empty input should return empty output."""
        df = pd.DataFrame()
        result = derive_single_quarter(df)
        assert result.empty
