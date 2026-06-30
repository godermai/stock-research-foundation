"""Tests for symbol normalization."""

import pytest
from src.normalize.symbols import (
    normalize_symbol,
    denormalize_symbol,
    infer_exchange,
    infer_board,
)


class TestNormalizeSymbol:
    def test_already_canonical(self):
        assert normalize_symbol("600519.SH") == "600519.SH"
        assert normalize_symbol("000001.SZ") == "000001.SZ"

    def test_baostock_format(self):
        assert normalize_symbol("sh.600519") == "600519.SH"
        assert normalize_symbol("sz.000001") == "000001.SZ"

    def test_prefixed_no_dot(self):
        assert normalize_symbol("sh600519") == "600519.SH"
        assert normalize_symbol("SZ000001") == "000001.SZ"

    def test_bare_code_sh(self):
        assert normalize_symbol("600519") == "600519.SH"
        assert normalize_symbol("688001") == "688001.SH"

    def test_bare_code_sz(self):
        assert normalize_symbol("000001") == "000001.SZ"
        assert normalize_symbol("300750") == "300750.SZ"

    def test_bare_code_bj(self):
        assert normalize_symbol("920001") == "920001.BJ"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            normalize_symbol("")

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_symbol("invalid")


class TestDenormalizeSymbol:
    def test_to_baostock(self):
        assert denormalize_symbol("600519.SH", "baostock") == "sh.600519"

    def test_to_tushare(self):
        assert denormalize_symbol("600519.SH", "tushare") == "600519.SH"

    def test_to_bare(self):
        assert denormalize_symbol("600519.SH", "bare") == "600519"


class TestInferExchange:
    def test_sh_main(self):
        assert infer_exchange("600519") == "SH"

    def test_sh_star(self):
        assert infer_exchange("688001") == "SH"

    def test_sz_main(self):
        assert infer_exchange("000001") == "SZ"

    def test_sz_chinext(self):
        assert infer_exchange("300750") == "SZ"

    def test_bj(self):
        assert infer_exchange("920001") == "BJ"


class TestInferBoard:
    def test_main_sh(self):
        assert infer_board("600519") == "main"

    def test_star(self):
        assert infer_board("688001") == "star"

    def test_chinext(self):
        assert infer_board("300750") == "chinext"

    def test_bse(self):
        assert infer_board("920001") == "bse"
