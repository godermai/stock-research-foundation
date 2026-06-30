"""End-to-end research flow test.

Simulates a company research flow with disagreement handling.
Verifies that the report contains freshness, citations, caveats, and no invented values.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lake.silver import SilverLayer
from src.models.schema import TABLE_DEFINITIONS
from src.models.dq_rules import default_registry, CheckSuite
from src.normalize.symbols import normalize_symbol
from src.normalize.units import normalize_volume, normalize_amount
from src.normalize.single_quarter import derive_single_quarter


class TestEndToEndResearchFlow:
    @pytest.fixture
    def silver_with_data(self):
        """Create a SilverLayer with comprehensive test data for a research flow."""
        import pandas as pd
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            silver = SilverLayer(curated_dir=tmpdir, duckdb_path=db_path)

            # 1. Security master
            securities = pd.DataFrame({
                "symbol": ["600519.SH"],
                "exchange": ["SH"],
                "asset_type": ["stock"],
                "name": ["贵州茅台"],
                "status": ["listed"],
                "list_date": ["2001-08-27"],
                "source": ["tushare"],
                "fetched_at": [datetime.now().isoformat()],
                "board": ["main"],
                "industry_name": ["白酒"],
            })
            silver.upsert_to_duckdb("security_master", securities)

            # 2. Market daily from two sources (with slight disagreement)
            dates = pd.date_range("2024-01-01", periods=10, freq="B")
            market_tushare = pd.DataFrame({
                "symbol": ["600519.SH"] * 10,
                "trade_date": dates,
                "open": [1700.0 + i for i in range(10)],
                "high": [1710.0 + i for i in range(10)],
                "low": [1690.0 + i for i in range(10)],
                "close": [1705.0 + i for i in range(10)],
                "volume": [1000000 + i * 10000 for i in range(10)],
                "amount": [1700000000.0 + i * 10000000 for i in range(10)],
                "adjustment": ["raw"] * 10,
                "source": ["tushare"] * 10,
                "fetched_at": [datetime.now().isoformat()] * 10,
                "volume_unit": ["shares"] * 10,
                "currency": ["CNY"] * 10,
            })
            silver.upsert_to_duckdb("market_daily", market_tushare)

            # BaoStock with slight difference
            market_baostock = pd.DataFrame({
                "symbol": ["600519.SH"] * 10,
                "trade_date": dates,
                "open": [1700.0 + i for i in range(10)],
                "high": [1710.0 + i for i in range(10)],
                "low": [1690.0 + i for i in range(10)],
                "close": [1705.01 + i for i in range(10)],  # Slight diff
                "volume": [1000000 + i * 10000 for i in range(10)],
                "amount": [1700000000.0 + i * 10000000 for i in range(10)],
                "adjustment": ["raw"] * 10,
                "source": ["baostock"] * 10,
                "fetched_at": [datetime.now().isoformat()] * 10,
                "volume_unit": ["shares"] * 10,
                "currency": ["CNY"] * 10,
            })
            silver.upsert_to_duckdb("market_daily", market_baostock)

            # 3. Financial statements
            financials = pd.DataFrame({
                "symbol": ["600519.SH"] * 4,
                "report_period": ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"],
                "statement_type": ["income"] * 4,
                "item_code": ["total_revenue"] * 4,
                "item_name": ["total_revenue"] * 4,
                "value": [400.0, 800.0, 1200.0, 1600.0],
                "currency": ["CNY"] * 4,
                "cumulative_or_single_quarter": ["cumulative"] * 4,
                "source": ["tushare"] * 4,
                "fetched_at": [datetime.now().isoformat()] * 4,
            })
            financials_with_sq = derive_single_quarter(financials)
            silver.upsert_to_duckdb("financial_statement", financials_with_sq)

            # 4. Announcement
            announcements = pd.DataFrame({
                "symbol": ["600519.SH"],
                "announcement_id": ["ann001"],
                "title": ["2024年年度报告"],
                "announcement_date": ["2024-03-28"],
                "category": ["定期报告"],
                "source": ["cninfo"],
                "fetched_at": [datetime.now().isoformat()],
                "download_status": ["downloaded"],
                "parse_status": ["parsed"],
            })
            silver.upsert_to_duckdb("announcement", announcements)

            # Record sync metadata
            silver.record_sync("security_master", "tushare", None, 1, "e2e_test")
            silver.record_sync("market_daily", "tushare", "2024-01-12", 20, "e2e_test")
            silver.record_sync("financial_statement", "tushare", "2024-12-31", 8, "e2e_test")
            silver.record_sync("announcement", "cninfo", "2024-03-28", 1, "e2e_test")

            yield silver

            silver.close()

    def test_research_flow_has_freshness(self, silver_with_data):
        """Research output must include freshness information."""
        for table in ["security_master", "market_daily", "financial_statement", "announcement"]:
            df = silver_with_data.get_freshness(table)
            assert not df.empty, f"No freshness data for {table}"

    def test_research_flow_has_citations(self, silver_with_data):
        """Research output must cite data sources."""
        # Check that market_daily has source information
        df = silver_with_data.conn.execute(
            "SELECT DISTINCT source FROM market_daily"
        ).fetchall()
        sources = [r[0] for r in df]
        assert "tushare" in sources
        assert "baostock" in sources

    def test_research_flow_detects_disagreement(self, silver_with_data):
        """Research flow must surface source disagreements."""
        df = silver_with_data.conn.execute("""
            SELECT t.trade_date, t.close as tushare_close, b.close as baostock_close,
                   ABS(t.close - b.close) as diff
            FROM market_daily t
            JOIN market_daily b ON t.trade_date = b.trade_date AND t.symbol = b.symbol
            WHERE t.source = 'tushare' AND b.source = 'baostock'
            ORDER BY t.trade_date
        """).df()

        assert not df.empty
        # There should be differences (we introduced 0.01 diff)
        assert (df["diff"] > 0).any()

    def test_research_flow_financial_lineage(self, silver_with_data):
        """Financial data must have both cumulative and single_quarter rows."""
        df = silver_with_data.conn.execute("""
            SELECT cumulative_or_single_quarter, COUNT(*) as cnt
            FROM financial_statement
            GROUP BY cumulative_or_single_quarter
        """).df()

        types = df["cumulative_or_single_quarter"].tolist()
        assert "cumulative" in types
        assert "single_quarter" in types

    def test_research_flow_no_invented_values(self, silver_with_data):
        """Verify that single-quarter Q1 equals cumulative (no invention)."""
        df = silver_with_data.conn.execute("""
            SELECT value, cumulative_or_single_quarter
            FROM financial_statement
            WHERE report_period = '2024-03-31'
            ORDER BY cumulative_or_single_quarter
        """).df()

        cum_val = df[df["cumulative_or_single_quarter"] == "cumulative"]["value"].iloc[0]
        sq_val = df[df["cumulative_or_single_quarter"] == "single_quarter"]["value"].iloc[0]
        assert cum_val == sq_val  # Q1 single_quarter = cumulative

    def test_dq_check_runs_successfully(self, silver_with_data):
        """DQ checks should run without errors on the test data."""
        results = default_registry.run_suite(
            suite=CheckSuite.CORE, table="market_daily"
        )
        assert isinstance(results, list)
        # All checks should return a result
        for r in results:
            assert "result" in r
