"""Initialize DuckDB database with schema and views.

Run this once before first use:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lake.silver import SilverLayer
from config import config


def init_database():
    """Create DuckDB database with all tables and views."""
    print(f"Initializing DuckDB at: {config.duckdb_path}")

    silver = SilverLayer(
        curated_dir=str(config.curated_dir),
        duckdb_path=str(config.duckdb_path),
    )

    # Tables are auto-created in __init__
    # Now load views from SQL file
    views_sql_path = Path(__file__).parent.parent / "src" / "lake" / "duckdb_views.sql"
    if views_sql_path.exists():
        sql = views_sql_path.read_text(encoding="utf-8")
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            try:
                silver.conn.execute(stmt)
            except Exception as e:
                print(f"  Warning: {e}")

    # Verify tables
    tables = silver.conn.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name"
    ).fetchall()
    print(f"\nCreated tables: {[t[0] for t in tables]}")

    # Verify views
    views = silver.conn.execute(
        "SELECT table_name FROM information_schema.views ORDER BY table_name"
    ).fetchall()
    print(f"Created views: {[v[0] for v in views]}")

    silver.close()
    print(f"\n✅ Database initialized at {config.duckdb_path}")


if __name__ == "__main__":
    init_database()
