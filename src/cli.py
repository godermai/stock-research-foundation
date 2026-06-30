"""Command-line interface for the stock research data foundation.

Usage:
    stock-cli init
    stock-cli sync security-master [--no-verify]
    stock-cli sync market-daily [--symbol SYMBOL] [--date YYYYMMDD] [--verify-baostock] [--verify-akshare]
    stock-cli sync financials --symbol SYMBOL --start YYYYMMDD --end YYYYMMDD
    stock-cli sync announcements --symbol SYMBOL [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--no-pdf]
    stock-cli mcp
    stock-cli query --sql "SELECT ..."
    stock-cli status [--table TABLE]
    stock-cli test [--verbose]
    stock-cli accept [--json]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.logging_config import setup_logging

logger = setup_logging("cli")


# ─── init ──────────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> int:
    """Initialize DuckDB database with schema and views."""
    from src.lake.silver import SilverLayer

    duckdb_path = os.getenv("DUCKDB_PATH", "db/market.duckdb")
    curated_dir = os.getenv("DATA_DIR", "data") + "/curated"

    print(f"Initializing DuckDB at: {duckdb_path}")
    silver = SilverLayer(
        curated_dir=curated_dir,
        duckdb_path=duckdb_path,
    )

    views_sql_path = Path(__file__).parent / "lake" / "duckdb_views.sql"
    if views_sql_path.exists():
        sql = views_sql_path.read_text(encoding="utf-8")
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            try:
                silver.conn.execute(stmt)
            except Exception as e:
                print(f"  Warning: {e}")

    tables = silver.conn.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name"
    ).fetchall()
    print(f"\nCreated tables: {[t[0] for t in tables]}")

    views = silver.conn.execute(
        "SELECT table_name FROM information_schema.views ORDER BY table_name"
    ).fetchall()
    if views:
        print(f"Created views: {[v[0] for v in views]}")

    silver.close()
    print(f"\nDatabase initialized at {duckdb_path}")
    return 0


# ─── sync ──────────────────────────────────────────────────────────────

def cmd_sync(args: argparse.Namespace) -> int:
    """Run a data sync job."""
    table = args.table
    token = config.tushare_token

    if table == "security-master":
        from src.jobs.sync_security_master import run_sync_security_master
        result = run_sync_security_master(
            tushare_token=token,
            verify_with_baostock=not args.no_verify,
        )
    elif table == "market-daily":
        from src.jobs.sync_market_daily import run_sync_market_daily
        result = run_sync_market_daily(
            trade_date=args.date,
            symbols=[args.symbol] if args.symbol else None,
            tushare_token=token,
            verify_with_baostock=args.verify_baostock,
            verify_with_akshare=args.verify_akshare,
        )
    elif table == "financials":
        from src.jobs.sync_financials import run_sync_financials
        result = run_sync_financials(
            symbol=args.symbol,
            start_period=args.start,
            end_period=args.end,
            tushare_token=token,
        )
    elif table == "announcements":
        from src.jobs.sync_announcements import run_sync_announcements
        result = run_sync_announcements(
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            download_pdfs=not args.no_pdf,
        )
    else:
        print(f"Unknown sync table: {table}")
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    status = result.get("status", "unknown")
    if status == "completed":
        return 0
    else:
        print(f"\nSync status: {status}")
        return 1


# ─── mcp ───────────────────────────────────────────────────────────────

def cmd_mcp(args: argparse.Namespace) -> int:
    """Start the MCP server in stdio mode."""
    from mcp.local_stock_server import main as mcp_main
    print("Starting MCP server (stdio mode)...", file=sys.stderr)
    mcp_main()
    return 0


# ─── query ─────────────────────────────────────────────────────────────

def cmd_query(args: argparse.Namespace) -> int:
    """Execute a SQL query against DuckDB."""
    from src.lake.silver import SilverLayer

    duckdb_path = os.getenv("DUCKDB_PATH", "db/market.duckdb")
    curated_dir = os.getenv("DATA_DIR", "data") + "/curated"
    silver = SilverLayer(
        curated_dir=curated_dir,
        duckdb_path=duckdb_path,
    )
    try:
        df = silver.query(args.sql)
        if df.empty:
            print("(no rows)")
        else:
            print(df.to_string(index=False))
    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
        return 1
    finally:
        silver.close()
    return 0


# ─── status ────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> int:
    """Show data freshness and sync status."""
    from src.lake.silver import SilverLayer

    duckdb_path = os.getenv("DUCKDB_PATH", "db/market.duckdb")
    curated_dir = os.getenv("DATA_DIR", "data") + "/curated"
    silver = SilverLayer(
        curated_dir=curated_dir,
        duckdb_path=duckdb_path,
    )
    try:
        tables = ["security_master", "market_daily", "financial_statement", "announcement"]
        if args.table:
            tables = [args.table]

        for table in tables:
            print(f"\n{'='*60}")
            print(f"  {table}")
            print(f"{'='*60}")

            # Row count
            try:
                count = silver.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                print(f"  Rows: {count[0]}")
            except Exception:
                print(f"  Rows: (table not found)")

            # Freshness
            try:
                df = silver.get_freshness(table)
                if not df.empty:
                    latest = df.iloc[0]
                    print(f"  Last sync: {latest['latest_fetched_at']}")
                    print(f"  Source: {latest['source']}")
                    print(f"  Rows synced: {latest['row_count']}")
                    if latest['latest_trade_date']:
                        print(f"  Latest data date: {latest['latest_trade_date']}")
                else:
                    print(f"  Last sync: (never)")
            except Exception:
                print(f"  Last sync: (never)")
    finally:
        silver.close()
    return 0


# ─── test ──────────────────────────────────────────────────────────────

def cmd_test(args: argparse.Namespace) -> int:
    """Run the pytest test suite."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    if args.verbose:
        cmd.append("-v")
    result = subprocess.run(cmd, cwd=str(config.project_root))
    return result.returncode


# ─── accept ────────────────────────────────────────────────────────────

def cmd_accept(args: argparse.Namespace) -> int:
    """Run acceptance criteria checks."""
    from src.acceptance import run_acceptance

    results = run_acceptance()
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    else:
        passed = 0
        failed = 0
        for r in results["checks"]:
            status_icon = "PASS" if r["status"] == "pass" else "FAIL"
            print(f"  [{status_icon}] {r['id']}: {r['name']}")
            if r["status"] == "fail":
                print(f"         -> {r.get('detail', '')}")
                failed += 1
            else:
                passed += 1

        print(f"\n{'='*60}")
        print(f"  Acceptance: {passed} passed, {failed} failed, {len(results['checks'])} total")
        print(f"  Overall: {'PASS' if results['overall'] else 'FAIL'}")
        print(f"{'='*60}")

    return 0 if results["overall"] else 1


# ─── parser ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-cli",
        description="Stock research data foundation CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    subparsers.add_parser("init", help="Initialize DuckDB database")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Run a data sync job")
    sync_parser.add_argument("table", choices=["security-master", "market-daily", "financials", "announcements"])
    sync_parser.add_argument("--symbol", help="Canonical symbol (e.g. 600519.SH)")
    sync_parser.add_argument("--date", help="Trade date YYYYMMDD")
    sync_parser.add_argument("--start", help="Start date")
    sync_parser.add_argument("--end", help="End date")
    sync_parser.add_argument("--no-verify", action="store_true", help="Skip BaoStock verification (security-master)")
    sync_parser.add_argument("--verify-baostock", action="store_true", help="Verify with BaoStock (market-daily)")
    sync_parser.add_argument("--verify-akshare", action="store_true", help="Verify with AKShare (market-daily)")
    sync_parser.add_argument("--no-pdf", action="store_true", help="Skip PDF download (announcements)")

    # mcp
    subparsers.add_parser("mcp", help="Start MCP server (stdio)")

    # query
    query_parser = subparsers.add_parser("query", help="Run SQL query against DuckDB")
    query_parser.add_argument("--sql", required=True, help="SQL query string")

    # status
    status_parser = subparsers.add_parser("status", help="Show data freshness and sync status")
    status_parser.add_argument("--table", help="Specific table to check")

    # test
    test_parser = subparsers.add_parser("test", help="Run pytest test suite")
    test_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # accept
    accept_parser = subparsers.add_parser("accept", help="Run acceptance criteria checks")
    accept_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "init": cmd_init,
        "sync": cmd_sync,
        "mcp": cmd_mcp,
        "query": cmd_query,
        "status": cmd_status,
        "test": cmd_test,
        "accept": cmd_accept,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
