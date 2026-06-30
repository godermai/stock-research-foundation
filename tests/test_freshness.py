"""Tests for data freshness tracking."""

import pytest
import tempfile
import os
from pathlib import Path
from src.lake.silver import SilverLayer


class TestFreshness:
    def test_freshness_table_creation(self):
        """Verify _sync_metadata table is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            silver = SilverLayer(curated_dir=tmpdir, duckdb_path=db_path)

            # Table should exist
            tables = silver.conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name = '_sync_metadata'"
            ).fetchall()
            assert len(tables) == 1

            silver.close()

    def test_record_and_query_freshness(self):
        """Verify sync metadata can be recorded and queried."""
        from datetime import datetime
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            silver = SilverLayer(curated_dir=tmpdir, duckdb_path=db_path)

            silver.record_sync(
                "market_daily", "tushare",
                "2024-01-15", 5000, "test_run_001"
            )

            df = silver.get_freshness("market_daily")
            assert len(df) == 1
            assert df.iloc[0]["table_name"] == "market_daily"
            assert df.iloc[0]["source"] == "tushare"
            assert df.iloc[0]["row_count"] == 5000

            silver.close()

    def test_freshness_empty_table(self):
        """Querying freshness for a table with no sync records should return empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            silver = SilverLayer(curated_dir=tmpdir, duckdb_path=db_path)

            df = silver.get_freshness("nonexistent_table")
            assert df.empty

            silver.close()
