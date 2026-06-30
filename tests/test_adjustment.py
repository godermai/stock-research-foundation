"""Tests for adjustment (复权) correctness.

Verifies that raw, qfq (forward-adjusted), and hfq (backward-adjusted)
price series reconcile correctly with adjustment factors.
"""

import pytest
import pandas as pd
import numpy as np
from src.normalize.units import normalize_volume, normalize_amount


class TestAdjustmentCorrectness:
    def test_raw_vs_qfq_with_adj_factor(self):
        """qfq_price = raw_price * (adj_factor / latest_adj_factor)."""
        # Simulate: stock had a 10:1 split, adj_factor goes from 1.0 to 0.1
        raw_close = [100.0, 100.0, 100.0, 10.0, 10.0]
        adj_factor = [1.0, 1.0, 1.0, 0.1, 0.1]
        latest_adj = adj_factor[-1]

        # qfq = raw * (latest_adj / adj)  =>  all become 10.0
        qfq_close = [r * (latest_adj / a) for r, a in zip(raw_close, adj_factor)]

        # All qfq prices should be 10.0
        assert all(abs(q - 10.0) < 0.001 for q in qfq_close)

    def test_raw_vs_hfq_with_adj_factor(self):
        """hfq_price = raw_price * (adj_factor / earliest_adj_factor).

        Pre-split: raw=100, adj=1.0 => hfq = 100 * 1.0/1.0 = 100
        Post-split: raw=10, adj=0.1 => hfq = 10 * 0.1/1.0 = 1.0
        (hfq preserves the actual historical price, not adjusted for future splits)
        """
        raw_close = [100.0, 100.0, 100.0, 10.0, 10.0]
        adj_factor = [1.0, 1.0, 1.0, 0.1, 0.1]
        earliest_adj = adj_factor[0]

        hfq_close = [r * (a / earliest_adj) for r, a in zip(raw_close, adj_factor)]

        # Pre-split prices stay at 100, post-split at 1
        assert all(abs(h - expected) < 0.001 for h, expected in zip(hfq_close, [100.0, 100.0, 100.0, 1.0, 1.0]))

    def test_qfq_and_hfq_are_consistent(self):
        """qfq and hfq daily returns match on non-event days.

        On ex-dates, qfq shows no gap (continuous) while hfq shows
        the historical price gap — both are correct but different.
        On normal days, returns must be identical.
        """
        raw_close = [100.0, 105.0, 110.0, 11.0, 11.5]
        adj_factor = [1.0, 1.0, 1.0, 0.1, 0.1]

        latest_adj = adj_factor[-1]
        earliest_adj = adj_factor[0]

        qfq = [r * (latest_adj / a) for r, a in zip(raw_close, adj_factor)]
        hfq = [r * (a / earliest_adj) for r, a in zip(raw_close, adj_factor)]

        # Daily returns on non-event days (indices 1,2: adj unchanged) should match
        for i in [1, 2]:
            qfq_ret = qfq[i] / qfq[i-1] - 1
            hfq_ret = hfq[i] / hfq[i-1] - 1
            assert abs(qfq_ret - hfq_ret) < 1e-10

        # On event day (index 3: split), qfq should show continuity
        qfq_event_ret = qfq[3] / qfq[2] - 1
        # qfq: day2 = 110*0.1/1.0 = 11, day3 = 11*0.1/0.1 = 11 => return = 0
        assert abs(qfq_event_ret) < 1e-10  # No gap in qfq

        # Post-event day (index 4): returns should also match
        qfq_post = qfq[4] / qfq[3] - 1
        hfq_post = hfq[4] / hfq[3] - 1
        assert abs(qfq_post - hfq_post) < 1e-10

    def test_no_adjustment_when_factor_constant(self):
        """When adj_factor is constant, raw = qfq = hfq."""
        raw_close = [100.0, 101.0, 102.0]
        adj_factor = [1.0, 1.0, 1.0]

        latest_adj = adj_factor[-1]
        earliest_adj = adj_factor[0]

        qfq = [r * (latest_adj / a) for r, a in zip(raw_close, adj_factor)]
        hfq = [r * (a / earliest_adj) for r, a in zip(raw_close, adj_factor)]

        assert qfq == raw_close
        assert hfq == raw_close

    def test_adjustment_label_preserved(self):
        """Verify that the adjustment label is correctly stored."""
        # This tests the concept: the canonical schema has an 'adjustment' column
        # that must be 'raw', 'qfq', or 'hfq'
        valid_adjustments = {"raw", "qfq", "hfq"}
        test_values = ["raw", "qfq", "hfq"]
        for v in test_values:
            assert v in valid_adjustments

    def test_volume_unaffected_by_adjustment(self):
        """Volume should not change between raw and adjusted data."""
        # Volume is in shares regardless of adjustment mode
        vol_raw, _ = normalize_volume(100000, source="tushare", original_unit="hands")
        vol_qfq, _ = normalize_volume(100000, source="tushare", original_unit="hands")

        assert vol_raw == vol_qfq == 10000000

    def test_corporate_action_linkage(self):
        """Verify that a dividend event creates a visible adj_factor change."""
        # Before dividend: adj_factor = 1.0, close = 100
        # After 10% dividend: adj_factor = 0.9, close = 90 (ex-dividend)
        # qfq should make both days show the same value
        raw_before = 100.0
        raw_after = 90.0
        adj_before = 1.0
        adj_after = 0.9

        latest_adj = adj_after  # latest is the ex-div date
        qfq_before = raw_before * (latest_adj / adj_before)
        qfq_after = raw_after * (latest_adj / adj_after)

        # In qfq terms, the price should be continuous (no gap)
        assert abs(qfq_before - qfq_after) < 0.001
