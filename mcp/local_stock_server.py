"""Local Stock Research MCP Server.

A local-first stdio MCP server backed by DuckDB curated tables.
No remote endpoints, no token relay, no public server assumptions.

Tools:
1. search_security
2. get_market_history
3. get_latest_quote
4. get_financial_statements
5. get_financial_metrics
6. get_announcements
7. search_announcements
8. compare_sources
9. get_data_freshness
10. run_data_quality_check
11. export_dataset
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lake.silver import SilverLayer
from models.schema import TABLE_DEFINITIONS
from models.dq_rules import default_registry, CheckSuite


# Initialize silver layer
silver = SilverLayer(
    curated_dir=os.getenv("DATA_DIR", "data/curated"),
    duckdb_path=os.getenv("DUCKDB_PATH", "db/market.duckdb"),
)


def _format_error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _paginate(df, page: int = 1, page_size: int = 50) -> dict:
    """Paginate a DataFrame and return metadata + rows."""
    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]
    return {
        "items": page_df.to_dict("records"),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


# --- Tool implementations ---

def search_security(
    query: str,
    exchange: Optional[list[str]] = None,
    asset_type: Optional[list[str]] = None,
    status: Optional[str] = None,
    limit: int = 20,
    page: int = 1,
) -> dict:
    """Search securities by name or symbol."""
    sql = "SELECT symbol, name, exchange, asset_type, status, list_date FROM security_master WHERE 1=1"
    params = []

    if query:
        sql += " AND (symbol LIKE ? OR name LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if exchange:
        placeholders = ", ".join(["?" for _ in exchange])
        sql += f" AND exchange IN ({placeholders})"
        params.extend(exchange)
    if asset_type:
        placeholders = ", ".join(["?" for _ in asset_type])
        sql += f" AND asset_type IN ({placeholders})"
        params.extend(asset_type)
    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY symbol"
    try:
        df = silver.conn.execute(sql, params).df()
        return _paginate(df, page, limit)
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def get_market_history(
    symbols: list[str],
    start_date: str,
    end_date: str,
    adjustment: str = "raw",
    fields: Optional[list[str]] = None,
    limit: int = 500,
    page_token: Optional[str] = None,
) -> dict:
    """Get market history for symbols."""
    placeholders = ", ".join(["?" for _ in symbols])
    field_list = ", ".join(fields) if fields else "symbol, trade_date, open, high, low, close, volume, amount, adjustment, source"

    sql = f"""
        SELECT {field_list}
        FROM market_daily
        WHERE symbol IN ({placeholders})
        AND trade_date BETWEEN ? AND ?
        AND adjustment = ?
        ORDER BY symbol, trade_date
        LIMIT ?
    """
    params = symbols + [start_date, end_date, adjustment, limit]

    try:
        df = silver.conn.execute(sql, params).df()
        result = {
            "items": df.to_dict("records"),
            "source_coverage": [{"symbol": s, "adjustment": adjustment} for s in symbols],
        }
        if len(df) >= limit:
            result["next_page_token"] = f"offset_{limit}"
        return result
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def get_latest_quote(
    symbols: list[str],
    allow_upstream: bool = False,
) -> dict:
    """Get latest available quote for symbols."""
    if len(symbols) > 50:
        return _format_error("TOO_MANY_SYMBOLS", "Max 50 symbols per request")

    placeholders = ", ".join(["?" for _ in symbols])
    sql = f"""
        SELECT DISTINCT ON (symbol)
            symbol, trade_date, close, volume, amount, adjustment, source, fetched_at
        FROM market_daily
        WHERE symbol IN ({placeholders})
        ORDER BY symbol, trade_date DESC
    """
    try:
        df = silver.conn.execute(sql, symbols).df()
        if df.empty:
            return _format_error("QUOTE_UNAVAILABLE", "No data found for given symbols")
        return {
            "items": df.to_dict("records"),
            "as_of": str(df["trade_date"].max()) if not df.empty else None,
        }
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def get_financial_statements(
    symbol: str,
    statement_types: list[str],
    report_period_start: Optional[str] = None,
    report_period_end: Optional[str] = None,
    mode: str = "cumulative",
    items: Optional[list[str]] = None,
    limit: int = 1000,
) -> dict:
    """Get financial statements for a symbol."""
    placeholders = ", ".join(["?" for _ in statement_types])
    sql = f"""
        SELECT symbol, report_period, statement_type, item_code, item_name,
               value, currency, cumulative_or_single_quarter, source, fetched_at
        FROM financial_statement
        WHERE symbol = ?
        AND statement_type IN ({placeholders})
        AND cumulative_or_single_quarter = ?
    """
    params = [symbol] + statement_types + [mode]

    if report_period_start:
        sql += " AND report_period >= ?"
        params.append(report_period_start)
    if report_period_end:
        sql += " AND report_period <= ?"
        params.append(report_period_end)
    if items:
        item_placeholders = ", ".join(["?" for _ in items])
        sql += f" AND item_code IN ({item_placeholders})"
        params.extend(items)

    sql += " ORDER BY report_period DESC, item_code LIMIT ?"
    params.append(limit)

    try:
        df = silver.conn.execute(sql, params).df()
        if df.empty:
            return _format_error("NO_STATEMENT", "No financial statements found")
        return _paginate(df, 1, limit)
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def get_financial_metrics(
    symbol: str,
    periods: int = 10,
    metrics: Optional[list[str]] = None,
) -> dict:
    """Get compact financial metrics panel."""
    sql = """
        SELECT report_period, statement_type, item_code, item_name,
               value, cumulative_or_single_quarter
        FROM financial_statement
        WHERE symbol = ?
        ORDER BY report_period DESC
        LIMIT ?
    """
    try:
        df = silver.conn.execute(sql, [symbol, periods * 50]).df()
        if df.empty:
            return _format_error("NO_METRIC_DATA", "No financial metrics found")

        # Pivot to compact format
        if metrics:
            df = df[df["item_code"].isin(metrics)]

        return {
            "symbol": symbol,
            "periods": df["report_period"].unique().tolist(),
            "metrics": df.to_dict("records"),
        }
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def get_announcements(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    categories: Optional[list[str]] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Get announcements for a symbol."""
    sql = """
        SELECT symbol, announcement_id, title, announcement_date, category,
               source_url, local_path, download_status, source
        FROM announcement
        WHERE symbol = ?
    """
    params = [symbol]

    if start_date:
        sql += " AND announcement_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND announcement_date <= ?"
        params.append(end_date)
    if categories:
        placeholders = ", ".join(["?" for _ in categories])
        sql += f" AND category IN ({placeholders})"
        params.extend(categories)

    sql += " ORDER BY announcement_date DESC"
    try:
        df = silver.conn.execute(sql, params).df()
        if df.empty:
            return _format_error("NO_ANNOUNCEMENTS", "No announcements found")
        return _paginate(df, page, page_size)
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def search_announcements(
    query: str,
    symbols: Optional[list[str]] = None,
    date_range: Optional[dict] = None,
    categories: Optional[list[str]] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Search announcements by text query."""
    sql = """
        SELECT symbol, announcement_id, title, announcement_date, category, source
        FROM announcement
        WHERE title LIKE ?
    """
    params = [f"%{query}%"]

    if symbols:
        placeholders = ", ".join(["?" for _ in symbols])
        sql += f" AND symbol IN ({placeholders})"
        params.extend(symbols)
    if date_range and date_range.get("start"):
        sql += " AND announcement_date >= ?"
        params.append(date_range["start"])
    if date_range and date_range.get("end"):
        sql += " AND announcement_date <= ?"
        params.append(date_range["end"])
    if categories:
        placeholders = ", ".join(["?" for _ in categories])
        sql += f" AND category IN ({placeholders})"
        params.extend(categories)

    sql += " ORDER BY announcement_date DESC"
    try:
        df = silver.conn.execute(sql, params).df()
        if df.empty:
            return _format_error("INDEX_NOT_READY", "No matching announcements found")
        return _paginate(df, page, page_size)
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


def compare_sources(
    dataset: str,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fields: Optional[list[str]] = None,
    sources: Optional[list[str]] = None,
) -> dict:
    """Compare data across sources for consistency."""
    if dataset == "market_daily":
        sql = """
            SELECT symbol, trade_date, source, close, volume, amount, adjustment
            FROM market_daily
            WHERE symbol = ?
        """
        params = [symbol]
        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)
        if sources:
            placeholders = ", ".join(["?" for _ in sources])
            sql += f" AND source IN ({placeholders})"
            params.extend(sources)
        sql += " ORDER BY trade_date, source"

        try:
            df = silver.conn.execute(sql, params).df()
            if df.empty:
                return _format_error("SOURCE_UNAVAILABLE", "No data from any source")

            # Group by trade_date and compare
            comparison = []
            for date, group in df.groupby("trade_date"):
                row = {"trade_date": str(date)}
                for _, r in group.iterrows():
                    src = r["source"]
                    row[f"{src}_close"] = r["close"]
                    row[f"{src}_volume"] = r["volume"]
                if len(group) > 1:
                    closes = group["close"].dropna().tolist()
                    if len(closes) > 1:
                        row["max_diff"] = max(closes) - min(closes)
                comparison.append(row)

            return {"comparison": comparison[:200]}
        except Exception as e:
            return _format_error("QUERY_FAILED", str(e))
    else:
        return _format_error("DATASET_UNSUPPORTED", f"Comparison for {dataset} not implemented")


def get_data_freshness(
    table_name: str,
    symbol: Optional[str] = None,
) -> dict:
    """Get data freshness information for a table."""
    try:
        df = silver.get_freshness(table_name)
        if df.empty:
            return _format_error("TABLE_UNKNOWN", f"No freshness data for {table_name}")
        return {"items": df.to_dict("records")}
    except Exception as e:
        return _format_error("TABLE_UNKNOWN", str(e))


def run_data_quality_check(
    table_name: str,
    check_suite: str = "core",
    date_range: Optional[dict] = None,
    symbol: Optional[str] = None,
) -> dict:
    """Run data quality checks on a table."""
    try:
        suite = CheckSuite(check_suite)
    except ValueError:
        return _format_error("CHECK_SUITE_UNKNOWN", f"Unknown suite: {check_suite}")

    results = default_registry.run_suite(suite=suite, table=table_name)
    return {
        "table": table_name,
        "suite": check_suite,
        "checks": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["result"] == "pass"),
            "failed": sum(1 for r in results if r["result"] == "fail"),
            "warnings": sum(1 for r in results if r["result"] == "warning"),
        },
    }


def export_dataset(
    dataset: str,
    format: str = "parquet",
    row_limit: int = 100000,
    columns: Optional[list[str]] = None,
) -> dict:
    """Export a dataset to a file."""
    if row_limit > 100000:
        return _format_error("EXPORT_TOO_LARGE", "Max 100000 rows per export")
    if format not in ("parquet", "csv"):
        return _format_error("FORMAT_UNSUPPORTED", f"Format {format} not supported")

    col_list = ", ".join(columns) if columns else "*"
    sql = f"SELECT {col_list} FROM {dataset} LIMIT ?"

    try:
        df = silver.conn.execute(sql, [row_limit]).df()
        export_dir = Path("data/extracts")
        export_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = export_dir / f"{dataset}_{ts}.{format}"

        if format == "parquet":
            df.to_parquet(filepath, index=False)
        else:
            df.to_csv(filepath, index=False)

        import hashlib
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)

        return {
            "artifact_path": str(filepath),
            "row_count": len(df),
            "checksum": h.hexdigest(),
        }
    except Exception as e:
        return _format_error("QUERY_FAILED", str(e))


# --- MCP Server (stdio transport) ---

TOOL_REGISTRY = {
    "search_security": search_security,
    "get_market_history": get_market_history,
    "get_latest_quote": get_latest_quote,
    "get_financial_statements": get_financial_statements,
    "get_financial_metrics": get_financial_metrics,
    "get_announcements": get_announcements,
    "search_announcements": search_announcements,
    "compare_sources": compare_sources,
    "get_data_freshness": get_data_freshness,
    "run_data_quality_check": run_data_quality_check,
    "export_dataset": export_dataset,
}


def handle_request(request: dict) -> dict:
    """Handle a single MCP request."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "local-stock-mcp",
                    "version": "0.1.0",
                },
            },
        }

    if method == "tools/list":
        tools = []
        for name, fn in TOOL_REGISTRY.items():
            tools.append({
                "name": name,
                "description": fn.__doc__ or "",
                "inputSchema": {"type": "object", "properties": {}},
            })
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in TOOL_REGISTRY:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }

        try:
            result = TOOL_REGISTRY[tool_name](**arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, default=str, ensure_ascii=False)}]
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    """Run the MCP server in stdio mode."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()
