"""Tests for market daily normalization (unit conversion)."""

import pytest
from src.normalize.units import normalize_volume, normalize_amount


class TestNormalizeVolume:
    def test_tushare_hands_to_shares(self):
        vol, unit = normalize_volume(100, source="tushare", original_unit="hands")
        assert vol == 10000
        assert unit == "shares"

    def test_akshare_hands_to_shares(self):
        vol, unit = normalize_volume(500, source="akshare", original_unit="hands")
        assert vol == 50000
        assert unit == "shares"

    def test_baostock_already_shares(self):
        vol, unit = normalize_volume(10000, source="baostock")
        assert vol == 10000
        assert unit == "shares"

    def test_none_volume(self):
        vol, unit = normalize_volume(None, source="tushare")
        assert vol is None
        assert unit == "shares"


class TestNormalizeAmount:
    def test_tushare_thousand_yuan_to_yuan(self):
        amt, unit = normalize_amount(50000, source="tushare", original_unit="thousand_yuan")
        assert amt == 50000000
        assert unit == "yuan"

    def test_akshare_yuan(self):
        amt, unit = normalize_amount(1000000, source="akshare", original_unit="yuan")
        assert amt == 1000000
        assert unit == "yuan"

    def test_baostock_yuan(self):
        amt, unit = normalize_amount(1000000, source="baostock")
        assert amt == 1000000
        assert unit == "yuan"

    def test_none_amount(self):
        amt, unit = normalize_amount(None, source="tushare")
        assert amt is None
        assert unit == "yuan"
