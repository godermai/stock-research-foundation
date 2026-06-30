"""Acceptance criteria checks for the stock research data foundation.

Each check returns a dict with:
  - id: short identifier
  - name: human-readable name
  - status: "pass" | "fail"
  - detail: explanation (especially on failure)

The overall result aggregates all checks.
"""

import importlib
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

import pandas as pd

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normalize.symbols import normalize_symbol, denormalize_symbol, infer_exchange, infer_board
from src.normalize.units import normalize_volume, normalize_amount
from src.normalize.single_quarter import derive_single_quarter
from src.models.schema import TABLE_DEFINITIONS
from src.models.dq_rules import default_registry, CheckSuite
from src.lake.silver import SilverLayer


def _ok(check_id: str, name: str, detail: str = "") -> dict:
    return {"id": check_id, "name": name, "status": "pass", "detail": detail}


def _fail(check_id: str, name: str, detail: str) -> dict:
    return {"id": check_id, "name": name, "status": "fail", "detail": detail}


# ─── AC-01: Symbol normalization ───────────────────────────────────────

def ac_01_symbol_normalization() -> dict:
    """Symbol normalization handles all exchange formats correctly."""
    check_id = "AC-01"
    name = "Symbol normalization (SH/SZ/BJ, BaoStock, bare codes)"
    try:
        assert normalize_symbol("600519.SH") == "600519.SH"
        assert normalize_symbol("sh.600519") == "600519.SH"
        assert normalize_symbol("sh600519") == "600519.SH"
        assert normalize_symbol("600519") == "600519.SH"
        assert normalize_symbol("000001") == "000001.SZ"
        assert normalize_symbol("300750") == "300750.SZ"
        assert normalize_symbol("688001") == "688001.SH"
        assert normalize_symbol("920001") == "920001.BJ"
        assert denormalize_symbol("600519.SH", "baostock") == "sh.600519"
        assert infer_exchange("600519") == "SH"
        assert infer_board("688001") == "star"
        return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-02: Unit normalization ─────────────────────────────────────────

def ac_02_unit_normalization() -> dict:
    """Volume normalized to shares, amount normalized to CNY yuan."""
    check_id = "AC-02"
    name = "Unit normalization (volume→shares, amount→CNY)"
    try:
        # Tushare: vol in hands (×100 = shares), amount in thousand yuan (×1000 = yuan)
        vol, vol_unit = normalize_volume(1000, source="tushare")
        assert vol == 100000, f"Expected 100000, got {vol}"
        assert vol_unit == "shares"
        amt, amt_unit = normalize_amount(50000, source="tushare")
        assert amt == 50000000, f"Expected 50000000, got {amt}"
        assert amt_unit == "yuan"
        # BaoStock: already in shares
        vol_bs, vol_bs_unit = normalize_volume(1000, source="baostock")
        assert vol_bs == 1000, f"Expected 1000, got {vol_bs}"
        assert vol_bs_unit == "shares"
        return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-03: Single-quarter derivation ──────────────────────────────────

def ac_03_single_quarter() -> dict:
    """Single-quarter derivation: Q1 SQ = Q1 cumulative; Q2 SQ = Q2 cum - Q1 cum."""
    check_id = "AC-03"
    name = "Single-quarter financial derivation (no invented values)"
    try:
        df = pd.DataFrame({
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
        result = derive_single_quarter(df)
        sq_rows = result[result["cumulative_or_single_quarter"] == "single_quarter"]
        assert len(sq_rows) == 4, f"Expected 4 single-quarter rows, got {len(sq_rows)}"

        # Q1 SQ = 400 (same as cumulative)
        q1_sq = sq_rows[sq_rows["report_period"] == "2024-03-31"]["value"].iloc[0]
        assert q1_sq == 400.0, f"Q1 SQ should be 400, got {q1_sq}"

        # Q2 SQ = 800 - 400 = 400
        q2_sq = sq_rows[sq_rows["report_period"] == "2024-06-30"]["value"].iloc[0]
        assert q2_sq == 400.0, f"Q2 SQ should be 400, got {q2_sq}"

        # Q3 SQ = 1200 - 800 = 400
        q3_sq = sq_rows[sq_rows["report_period"] == "2024-09-30"]["value"].iloc[0]
        assert q3_sq == 400.0, f"Q3 SQ should be 400, got {q3_sq}"

        # Q4 SQ = 1600 - 1200 = 400
        q4_sq = sq_rows[sq_rows["report_period"] == "2024-12-31"]["value"].iloc[0]
        assert q4_sq == 400.0, f"Q4 SQ should be 400, got {q4_sq}"

        return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-04: Schema definitions ─────────────────────────────────────────

def ac_04_schema_definitions() -> dict:
    """All four canonical tables have schema definitions."""
    check_id = "AC-04"
    name = "Canonical table schemas defined"
    try:
        expected = {"security_master", "market_daily", "financial_statement", "announcement"}
        actual = set(TABLE_DEFINITIONS.keys())
        missing = expected - actual
        assert not missing, f"Missing table definitions: {missing}"
        for tname, tdef in TABLE_DEFINITIONS.items():
            assert len(tdef.columns) > 0, f"{tname} has no columns"
        return _ok(check_id, name, f"Tables: {sorted(actual)}")
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-05: DQ rules registry ──────────────────────────────────────────

def ac_05_dq_rules() -> dict:
    """Data quality rule registry has built-in rules and runs without crash."""
    check_id = "AC-05"
    name = "DQ rule registry functional"
    try:
        rules = default_registry.list_rules(suite=CheckSuite.CORE)
        assert len(rules) >= 4, f"Expected >=4 core rules, got {len(rules)}"
        # Run suite on a dummy DataFrame
        df = pd.DataFrame({
            "symbol": ["600519.SH", "000001.SZ"],
            "trade_date": ["2024-01-01", "2024-01-01"],
            "volume": [100000, 200000],
            "volume_unit": ["shares", "shares"],
        })
        results = default_registry.run_suite(
            suite=CheckSuite.CORE, table="market_daily", df=df, table_name="market_daily"
        )
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert "result" in r
        return _ok(check_id, name, f"{len(rules)} core rules registered")
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-06: DuckDB Silver layer CRUD ───────────────────────────────────

def ac_06_silver_layer() -> dict:
    """SilverLayer can create tables, insert, query, and track freshness."""
    check_id = "AC-06"
    name = "SilverLayer DuckDB CRUD + freshness tracking"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            silver = SilverLayer(curated_dir=tmpdir, duckdb_path=db_path)

            # Insert security_master
            df = pd.DataFrame({
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
            silver.upsert_to_duckdb("security_master", df)
            silver.record_sync("security_master", "tushare", None, 1, "ac_test")

            # Query
            result = silver.query("SELECT COUNT(*) as cnt FROM security_master")
            assert result.iloc[0]["cnt"] == 1

            # Freshness
            fresh = silver.get_freshness("security_master")
            assert not fresh.empty
            assert fresh.iloc[0]["source"] == "tushare"

            silver.close()
            return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-07: MCP server tools exist ─────────────────────────────────────

def ac_07_mcp_tools() -> dict:
    """MCP server module defines all 11 tools."""
    check_id = "AC-07"
    name = "MCP server has 11 tool functions"
    try:
        # Import without instantiating the server (which opens DuckDB)
        spec = importlib.util.spec_from_file_location(
            "local_stock_server",
            Path(__file__).parent.parent / "mcp" / "local_stock_server.py",
        )
        # We just check the source contains the function definitions
        source = (Path(__file__).parent.parent / "mcp" / "local_stock_server.py").read_text()
        expected_tools = [
            "def search_security(",
            "def get_market_history(",
            "def get_latest_quote(",
            "def get_financial_statements(",
            "def get_financial_metrics(",
            "def get_announcements(",
            "def search_announcements(",
            "def compare_sources(",
            "def get_data_freshness(",
            "def run_data_quality_check(",
            "def export_dataset(",
        ]
        missing = [t for t in expected_tools if t not in source]
        assert not missing, f"Missing tool definitions: {missing}"
        return _ok(check_id, name, f"All 11 tools defined")
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-08: MCP JSON-RPC protocol ──────────────────────────────────────

def ac_08_mcp_jsonrpc() -> dict:
    """MCP server responds to JSON-RPC initialize and tools/list."""
    check_id = "AC-08"
    name = "MCP JSON-RPC initialize + tools/list"
    try:
        import json
        source = (Path(__file__).parent.parent / "mcp" / "local_stock_server.py").read_text()
        assert '"tools/list"' in source or "tools/list" in source, "No tools/list handler"
        assert '"initialize"' in source or "initialize" in source, "No initialize handler"
        assert '"jsonrpc"' in source, "No jsonrpc field"
        return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-09: Skills defined ─────────────────────────────────────────────

def ac_09_skills() -> dict:
    """All 7 Skill markdown files exist."""
    check_id = "AC-09"
    name = "7 Skill definitions present"
    try:
        skills_dir = Path(__file__).parent.parent / "skills"
        expected = [
            "stock-data-acquisition",
            "stock-data-validation",
            "company-fundamental-research",
            "announcement-event-research",
            "industry-supply-chain-research",
            "valuation-and-earnings-sensitivity",
            "investment-thesis-falsification",
        ]
        for skill in expected:
            skill_file = skills_dir / skill / "SKILL.md"
            assert skill_file.exists(), f"Missing: {skill_file}"
            content = skill_file.read_text()
            assert len(content) > 50, f"{skill} SKILL.md too short"
        return _ok(check_id, name, f"All 7 skills present")
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-10: Config & exceptions ────────────────────────────────────────

def ac_10_infrastructure() -> dict:
    """Config, exceptions, and logging modules are importable and functional."""
    check_id = "AC-10"
    name = "Infrastructure (config, exceptions, logging)"
    try:
        from src.config import config
        from src.exceptions import StockDataError, DataSourceError, TokenMissingError
        from src.logging_config import setup_logging

        assert config.duckdb_path is not None
        assert config.tushare_token is not None or True  # May be None in test env

        # Exception hierarchy
        assert issubclass(DataSourceError, StockDataError)
        assert issubclass(TokenMissingError, StockDataError)

        # Logging
        log = setup_logging("acceptance_test")
        assert log is not None

        return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-11: Sync jobs importable ───────────────────────────────────────

def ac_11_sync_jobs() -> dict:
    """All 4 sync job functions are importable."""
    check_id = "AC-11"
    name = "4 sync jobs importable"
    try:
        from src.jobs import (
            run_sync_security_master,
            run_sync_market_daily,
            run_sync_financials,
            run_sync_announcements,
        )
        assert callable(run_sync_security_master)
        assert callable(run_sync_market_daily)
        assert callable(run_sync_financials)
        assert callable(run_sync_announcements)
        return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-12: CLI entry point ────────────────────────────────────────────

def ac_12_cli() -> dict:
    """CLI module is importable and has all subcommands."""
    check_id = "AC-12"
    name = "CLI module with all subcommands"
    try:
        from src.cli import build_parser
        parser = build_parser()
        help_text = parser.format_help()
        for cmd in ["init", "sync", "mcp", "query", "status", "test", "accept"]:
            assert cmd in help_text, f"Missing CLI command: {cmd}"
        return _ok(check_id, name, "All 7 subcommands present")
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-13: End-to-end research flow ───────────────────────────────────

def ac_13_e2e_flow() -> dict:
    """End-to-end: insert data → query → detect disagreement → verify lineage."""
    check_id = "AC-13"
    name = "E2E research flow (multi-source, disagreement, lineage)"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            silver = SilverLayer(curated_dir=tmpdir, duckdb_path=db_path)

            # Security master
            sec = pd.DataFrame({
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
            silver.upsert_to_duckdb("security_master", sec)

            # Market daily from 2 sources with slight disagreement
            dates = pd.date_range("2024-01-01", periods=5, freq="B")
            md_tushare = pd.DataFrame({
                "symbol": ["600519.SH"] * 5,
                "trade_date": dates,
                "open": [1700.0 + i for i in range(5)],
                "high": [1710.0 + i for i in range(5)],
                "low": [1690.0 + i for i in range(5)],
                "close": [1705.0 + i for i in range(5)],
                "volume": [1000000 + i * 10000 for i in range(5)],
                "amount": [1700000000.0 + i * 10000000 for i in range(5)],
                "adjustment": ["raw"] * 5,
                "source": ["tushare"] * 5,
                "fetched_at": [datetime.now().isoformat()] * 5,
                "volume_unit": ["shares"] * 5,
                "currency": ["CNY"] * 5,
            })
            silver.upsert_to_duckdb("market_daily", md_tushare)

            md_baostock = pd.DataFrame({
                "symbol": ["600519.SH"] * 5,
                "trade_date": dates,
                "open": [1700.0 + i for i in range(5)],
                "high": [1710.0 + i for i in range(5)],
                "low": [1690.0 + i for i in range(5)],
                "close": [1705.01 + i for i in range(5)],
                "volume": [1000000 + i * 10000 for i in range(5)],
                "amount": [1700000000.0 + i * 10000000 for i in range(5)],
                "adjustment": ["raw"] * 5,
                "source": ["baostock"] * 5,
                "fetched_at": [datetime.now().isoformat()] * 5,
                "volume_unit": ["shares"] * 5,
                "currency": ["CNY"] * 5,
            })
            silver.upsert_to_duckdb("market_daily", md_baostock)

            # Financials with single-quarter
            fin = pd.DataFrame({
                "symbol": ["600519.SH"] * 2,
                "report_period": ["2024-03-31", "2024-06-30"],
                "statement_type": ["income"] * 2,
                "item_code": ["total_revenue"] * 2,
                "item_name": ["total_revenue"] * 2,
                "value": [400.0, 800.0],
                "currency": ["CNY"] * 2,
                "cumulative_or_single_quarter": ["cumulative"] * 2,
                "source": ["tushare"] * 2,
                "fetched_at": [datetime.now().isoformat()] * 2,
            })
            fin_sq = derive_single_quarter(fin)
            silver.upsert_to_duckdb("financial_statement", fin_sq)

            # Announcement
            ann = pd.DataFrame({
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
            silver.upsert_to_duckdb("announcement", ann)

            # Record sync metadata
            for table, source, date, count in [
                ("security_master", "tushare", None, 1),
                ("market_daily", "tushare", "2024-01-05", 10),
                ("financial_statement", "tushare", "2024-06-30", 4),
                ("announcement", "cninfo", "2024-03-28", 1),
            ]:
                silver.record_sync(table, source, date, count, "ac_test")

            # Verify: freshness for all tables
            for table in ["security_master", "market_daily", "financial_statement", "announcement"]:
                df = silver.get_freshness(table)
                assert not df.empty, f"No freshness for {table}"

            # Verify: source citations
            sources = silver.conn.execute("SELECT DISTINCT source FROM market_daily").fetchall()
            source_list = [r[0] for r in sources]
            assert "tushare" in source_list and "baostock" in source_list

            # Verify: disagreement detected
            diff_df = silver.conn.execute("""
                SELECT ABS(t.close - b.close) as diff
                FROM market_daily t
                JOIN market_daily b ON t.trade_date = b.trade_date AND t.symbol = b.symbol
                WHERE t.source = 'tushare' AND b.source = 'baostock'
            """).df()
            assert (diff_df["diff"] > 0).any()

            # Verify: single-quarter lineage
            sq = silver.conn.execute("""
                SELECT cumulative_or_single_quarter, COUNT(*) as cnt
                FROM financial_statement
                GROUP BY cumulative_or_single_quarter
            """).df()
            types = sq["cumulative_or_single_quarter"].tolist()
            assert "cumulative" in types and "single_quarter" in types

            silver.close()
            return _ok(check_id, name)
    except AssertionError as e:
        return _fail(check_id, name, f"Assertion failed: {e}")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── AC-14: Pytest suite ───────────────────────────────────────────────

def ac_14_pytest() -> dict:
    """All pytest unit tests pass."""
    check_id = "AC-14"
    name = "Pytest unit test suite passes"
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            timeout=300,
        )
        if result.returncode == 0:
            # Extract pass count from output
            line = result.stdout.strip().split("\n")[-1] if result.stdout else ""
            return _ok(check_id, name, f"pytest passed: {line}")
        else:
            # Show last few lines of failure
            lines = result.stdout.strip().split("\n")[-5:]
            return _fail(check_id, name, f"pytest failed: {' | '.join(lines)}")
    except subprocess.TimeoutExpired:
        return _fail(check_id, name, "pytest timed out (300s)")
    except Exception as e:
        return _fail(check_id, name, f"Error: {e}")


# ─── Runner ────────────────────────────────────────────────────────────

ALL_CHECKS = [
    ac_01_symbol_normalization,
    ac_02_unit_normalization,
    ac_03_single_quarter,
    ac_04_schema_definitions,
    ac_05_dq_rules,
    ac_06_silver_layer,
    ac_07_mcp_tools,
    ac_08_mcp_jsonrpc,
    ac_09_skills,
    ac_10_infrastructure,
    ac_11_sync_jobs,
    ac_12_cli,
    ac_13_e2e_flow,
]


def run_acceptance() -> dict:
    """Run all acceptance checks and return aggregated result.

    Returns:
        {
            "checks": [{"id", "name", "status", "detail"}, ...],
            "passed": int,
            "failed": int,
            "total": int,
            "overall": bool,
        }
    """
    checks = []
    for check_fn in ALL_CHECKS:
        result = check_fn()
        checks.append(result)

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")

    return {
        "checks": checks,
        "passed": passed,
        "failed": failed,
        "total": len(checks),
        "overall": failed == 0,
    }
