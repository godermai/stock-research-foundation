"""Tests for cross-source consistency.

These tests verify that volume and amount units are correctly normalized
across Tushare, AKShare, and BaoStock.
"""

import pytest
import pandas as pd
from src.normalize.units import normalize_volume, normalize_amount


class TestCrossSourceVolume:
    """Verify that the same trade, when fetched from different sources,
    produces the same canonical volume (in shares)."""

    def test_same_trade_volume_matches(self):
        """A trade with volume=1000 hands should be 100000 shares from all sources."""
        # Tushare: 1000 hands -> 100000 shares
        ts_vol, _ = normalize_volume(1000, source="tushare", original_unit="hands")
        # AKShare: 1000 hands -> 100000 shares
        ak_vol, _ = normalize_volume(1000, source="akshare", original_unit="hands")
        # BaoStock: 100000 shares (already)
        bs_vol, _ = normalize_volume(100000, source="baostock")

        assert ts_vol == ak_vol == bs_vol == 100000

    def test_amount_normalization_consistency(self):
        """Same trade amount should normalize to same CNY value."""
        # Tushare: 50000 thousand yuan -> 50000000 yuan
        ts_amt, _ = normalize_amount(50000, source="tushare", original_unit="thousand_yuan")
        # AKShare: 50000000 yuan
        ak_amt, _ = normalize_amount(50000000, source="akshare", original_unit="yuan")
        # BaoStock: 50000000 yuan
        bs_amt, _ = normalize_amount(50000000, source="baostock")

        assert ts_amt == ak_amt == bs_amt == 50000000


class TestSourceComparison:
    """Test the compare_sources concept."""

    def test_tolerance_breach_detection(self):
        """Verify that a tolerance breach can be detected."""
        ts_close = 100.0
        bs_close = 100.05
        tolerance = 0.01  # 0.01 yuan

        diff = abs(ts_close - bs_close)
        breach = diff > tolerance

        assert diff == pytest.approx(0.05, abs=0.001)
        assert breach is True

    def test_within_tolerance(self):
        """Verify that values within tolerance pass."""
        ts_close = 100.00
        bs_close = 100.005
        tolerance = 0.01

        diff = abs(ts_close - bs_close)
        breach = diff > tolerance

        assert breach is False
