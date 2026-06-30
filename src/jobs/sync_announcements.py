"""Sync job: announcement.

Primary: CNINFO official notices and PDF downloads
Hash every downloaded file; keep metadata even if PDF text extraction fails.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from ..adapters.cninfo_adapter import CNINFOAdapter
from ..normalize.symbols import normalize_symbol
from ..lake.bronze import BronzeLayer
from ..lake.silver import SilverLayer


def run_sync_announcements(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    download_pdfs: bool = True,
    lookback_days: int = 30,
) -> dict:
    """Sync announcements for a symbol from CNINFO.

    symbol: canonical e.g. 600519.SH
    start_date/end_date: YYYY-MM-DD (if None, uses lookback_days)
    """
    run_id = str(uuid.uuid4())[:8]
    bronze = BronzeLayer()
    silver = SilverLayer()

    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    bare_code = symbol.split(".")[0]

    result = {
        "run_id": run_id,
        "table": "announcement",
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "started_at": datetime.now().isoformat(),
        "metadata_rows": 0,
        "pdfs_downloaded": 0,
        "pdfs_failed": 0,
        "pdfs_skipped": 0,
        "status": "running",
    }

    try:
        cninfo = CNINFOAdapter()

        # Fetch announcement metadata
        df_raw = cninfo.query_all_announcements(bare_code, start_date, end_date)

        if df_raw.empty:
            result["status"] = "completed"
            result["finished_at"] = datetime.now().isoformat()
            return result

        # Save raw to bronze
        bronze.write_dataframe("cninfo", "announcement", df_raw, suffix=f"_{bare_code}")

        # Normalize metadata
        df_norm = cninfo.normalize_announcements(df_raw, symbol)
        result["metadata_rows"] = len(df_norm)

        # Download PDFs
        if download_pdfs:
            for idx, row in df_raw.iterrows():
                download_result = cninfo.download_pdf(row.to_dict(), symbol)

                status = download_result["download_status"]
                if status == "downloaded":
                    result["pdfs_downloaded"] += 1
                elif status == "already_exists":
                    result["pdfs_skipped"] += 1
                elif status == "skipped":
                    result["pdfs_skipped"] += 1
                else:
                    result["pdfs_failed"] += 1

                # Update normalized DataFrame
                df_norm.loc[idx, "local_path"] = download_result["local_path"]
                df_norm.loc[idx, "content_hash"] = download_result["content_hash"]
                df_norm.loc[idx, "download_status"] = status
                df_norm.loc[idx, "pdf_sha256"] = download_result["pdf_sha256"]

        # Write to silver
        if not df_norm.empty:
            silver.write_parquet(
                "announcement", df_norm, partition_col="announcement_date"
            )
            silver.upsert_to_duckdb("announcement", df_norm)
            silver.record_sync(
                "announcement", "cninfo",
                end_date, len(df_norm), run_id
            )

        result["status"] = "completed"

    except Exception as e:
        result["status"] = f"failed: {e}"

    result["finished_at"] = datetime.now().isoformat()
    return result
