"""Silver layer — curated Parquet partitions + DuckDB semantic layer.

Stores normalized data as Parquet partitions, with DuckDB views for SQL access.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ..models.schema import TABLE_DEFINITIONS


class SilverLayer:
    """Curated analytical lake with Parquet + DuckDB."""

    def __init__(
        self,
        curated_dir: str = "data/curated",
        duckdb_path: str = "db/market.duckdb",
    ):
        self.curated_dir = Path(curated_dir)
        self.curated_dir.mkdir(parents=True, exist_ok=True)
        self.duckdb_path = Path(duckdb_path)
        self.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(str(self.duckdb_path))
            self._init_tables()
        return self._conn

    def _init_tables(self):
        """Create DuckDB tables from schema definitions."""
        for table_name, table_def in TABLE_DEFINITIONS.items():
            cols = []
            for col in table_def.columns:
                nullable = "" if col.nullable else " NOT NULL"
                cols.append(f'"{col.name}" {col.dtype}{nullable}')
            ddl = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(cols)})'
            self.conn.execute(ddl)

        # Metadata table for freshness tracking
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _sync_metadata (
                table_name VARCHAR NOT NULL,
                source VARCHAR NOT NULL,
                latest_trade_date DATE,
                latest_fetched_at TIMESTAMP NOT NULL,
                row_count BIGINT,
                run_id VARCHAR
            )
        """)

    def write_parquet(
        self, table_name: str, df: pd.DataFrame, partition_col: Optional[str] = None
    ) -> list[Path]:
        """Write DataFrame as Parquet partitions.

        Returns list of written Parquet file paths.
        """
        table_dir = self.curated_dir / table_name
        table_dir.mkdir(parents=True, exist_ok=True)

        if df.empty:
            return []

        written_files = []

        if partition_col and partition_col in df.columns:
            # Partition by the specified column
            for partition_value in df[partition_col].unique():
                partition_df = df[df[partition_col] == partition_value]
                safe_value = str(partition_value).replace("/", "_").replace(" ", "_")
                part_dir = table_dir / f"{partition_col}={safe_value}"
                part_dir.mkdir(parents=True, exist_ok=True)

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = part_dir / f"{ts}.parquet"
                partition_df.to_parquet(filepath, index=False, engine="pyarrow")
                written_files.append(filepath)
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = table_dir / f"{ts}.parquet"
            df.to_parquet(filepath, index=False, engine="pyarrow")
            written_files.append(filepath)

        return written_files

    def upsert_to_duckdb(self, table_name: str, df: pd.DataFrame) -> int:
        """Insert or replace data in DuckDB table.

        Returns number of rows inserted.
        """
        if df.empty:
            return 0

        # Use INSERT OR REPLACE for upsert semantics
        # First, register the DataFrame as a temporary view
        self.conn.register("_temp_upsert", df)

        # Get primary key columns (simplified: use all columns for comparison)
        # For proper upsert, we'd need explicit PK definitions
        # For now, delete existing rows with same key and insert new ones
        table_def = TABLE_DEFINITIONS.get(table_name)
        if table_def is None:
            raise ValueError(f"Unknown table: {table_name}")

        # Determine key columns based on table
        key_cols = {
            "security_master": ["symbol"],
            "market_daily": ["symbol", "trade_date", "adjustment", "source"],
            "financial_statement": [
                "symbol", "report_period", "statement_type",
                "item_code", "cumulative_or_single_quarter", "source"
            ],
            "announcement": ["announcement_id", "source"],
        }.get(table_name, ["symbol"])

        key_list = ", ".join(f'"{c}"' for c in key_cols if c in df.columns)

        if key_list:
            # Delete existing rows with matching keys
            where_clause = " AND ".join(
                f't."{c}" = _temp_upsert."{c}"'
                for c in key_cols if c in df.columns
            )
            self.conn.execute(
                f'DELETE FROM {table_name} t USING _temp_upsert WHERE {where_clause}'
            )

        # Insert new rows
        cols = ", ".join(f'"{c}"' for c in df.columns if c in [
            col.name for col in table_def.columns
        ])
        self.conn.execute(
            f'INSERT INTO {table_name} ({cols}) SELECT {cols} FROM _temp_upsert'
        )

        self.conn.unregister("_temp_upsert")
        return len(df)

    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query against DuckDB."""
        return self.conn.execute(sql).df()

    def get_latest_date(self, table_name: str, date_col: str = "trade_date") -> Optional[str]:
        """Get the latest date in a table."""
        try:
            result = self.conn.execute(
                f'SELECT MAX("{date_col}") FROM {table_name}'
            ).fetchone()
            return str(result[0]) if result and result[0] else None
        except Exception:
            return None

    def record_sync(
        self,
        table_name: str,
        source: str,
        latest_date: Optional[str],
        row_count: int,
        run_id: str,
    ):
        """Record sync metadata."""
        self.conn.execute(
            "INSERT INTO _sync_metadata VALUES (?, ?, ?, ?, ?, ?)",
            [table_name, source, latest_date, datetime.now(), row_count, run_id]
        )

    def get_freshness(self, table_name: str) -> pd.DataFrame:
        """Get freshness metadata for a table."""
        return self.conn.execute(
            "SELECT * FROM _sync_metadata WHERE table_name = ? ORDER BY latest_fetched_at DESC LIMIT 10",
            [table_name]
        ).df()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
