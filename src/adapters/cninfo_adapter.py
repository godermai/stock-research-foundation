"""CNINFO adapter — official announcement source.

Handles:
- Announcement metadata query
- PDF download with content hashing
- Rate-limited requests

CNINFO is the truth source for announcements and filing PDFs.
"""

import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


CNINFO_ANNOUNCEMENT_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_PDF_BASE = "https://static.cninfo.com.cn/"


class CNINFOAdapter:
    """Adapter for CNINFO official announcement data."""

    def __init__(self, raw_dir: str = "data/raw/announcements"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=60))
    def query_announcements(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        page_num: int = 1,
        page_size: int = 30,
    ) -> dict:
        """Query announcement metadata.

        stock_code: bare code e.g. '600519'
        start_date/end_date: YYYY-MM-DD
        Returns raw JSON response.
        """
        data = {
            "stock": f"{stock_code},",
            "tabName": "fulltext",
            "pageSize": str(page_size),
            "pageNum": str(page_num),
            "column": "szse",  # will be overridden based on code
            "category": "",
            "plate": "",
            "seDate": f"{start_date}~{end_date}",
            "searchkey": "",
            "secid": "",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }

        # Determine column based on code prefix
        if stock_code.startswith("6"):
            data["column"] = "sse"
        elif stock_code.startswith(("0", "3")):
            data["column"] = "szse"
        elif stock_code.startswith(("8", "4")):
            data["column"] = "bse"

        resp = self._session.post(CNINFO_ANNOUNCEMENT_URL, data=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()

        # Rate limit: be polite
        time.sleep(1)

        return result

    def query_all_announcements(
        self, stock_code: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Fetch all announcements in date range, paginating automatically."""
        all_announcements = []
        page = 1

        while True:
            result = self.query_announcements(
                stock_code, start_date, end_date, page_num=page
            )
            announcements = result.get("announcements", [])
            if not announcements:
                break

            all_announcements.extend(announcements)

            total_pages = result.get("totalAnnouncementPage", 1)
            if page >= total_pages:
                break
            page += 1

        if not all_announcements:
            return pd.DataFrame()

        df = pd.DataFrame(all_announcements)
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=3, max=60))
    def download_pdf(
        self, announcement: dict, symbol: str
    ) -> dict:
        """Download a single announcement PDF and compute hash.

        Returns dict with local_path, content_hash, download_status.
        """
        adj_path = announcement.get("adjunctUrl", "")
        if not adj_path:
            return {
                "local_path": None,
                "content_hash": None,
                "download_status": "skipped",
                "pdf_sha256": None,
            }

        url = f"{CNINFO_PDF_BASE}{adj_path}"
        ann_date = announcement.get("announcementTime", "")
        ann_id = announcement.get("announcementId", adj_path.split("/")[-1])

        # Build local path: data/raw/announcements/SYMBOL/YYYYMMDD_ANNID.pdf
        date_str = datetime.fromtimestamp(
            ann_date / 1000 if isinstance(ann_date, (int, float)) else 0
        ).strftime("%Y%m%d") if ann_date else "unknown"

        safe_symbol = symbol.replace(".", "_")
        local_dir = self.raw_dir / safe_symbol
        local_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{date_str}_{ann_id}.pdf"
        local_path = local_dir / filename

        if local_path.exists():
            # Already downloaded, just compute hash
            sha256 = self._compute_sha256(local_path)
            return {
                "local_path": str(local_path),
                "content_hash": sha256,
                "download_status": "already_exists",
                "pdf_sha256": sha256,
            }

        try:
            resp = self._session.get(url, timeout=60)
            resp.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(resp.content)

            sha256 = self._compute_sha256(local_path)
            return {
                "local_path": str(local_path),
                "content_hash": sha256,
                "download_status": "downloaded",
                "pdf_sha256": sha256,
            }
        except Exception as e:
            return {
                "local_path": None,
                "content_hash": None,
                "download_status": f"failed: {e}",
                "pdf_sha256": None,
            }

    @staticmethod
    def _compute_sha256(filepath: Path) -> str:
        """Compute SHA256 hash of a file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def normalize_announcements(
        self, df: pd.DataFrame, symbol: str
    ) -> pd.DataFrame:
        """Normalize CNINFO announcement metadata to canonical schema."""
        if df.empty:
            return pd.DataFrame()

        n = len(df)
        result = pd.DataFrame(index=range(n))
        result["symbol"] = [symbol] * n
        result["announcement_id"] = df.get("announcementId", "").astype(str).values
        result["title"] = df.get("announcementTitle", "").values

        # announcementTime is in milliseconds
        ann_time = df.get("announcementTime")
        if ann_time is not None and len(ann_time) > 0:
            result["announcement_date"] = pd.to_datetime(
                ann_time / 1000, unit="s"
            ).dt.date
        else:
            result["announcement_date"] = None

        result["category"] = df.get("announcementTypeName", "")
        result["source_url"] = df.get("adjunctUrl", "").apply(
            lambda x: f"{CNINFO_PDF_BASE}{x}" if x else None
        )
        result["source"] = "cninfo"
        result["fetched_at"] = datetime.now().isoformat()
        result["exchange"] = df.get("secCode", "").apply(
            lambda x: "SSE" if str(x).startswith("6") else
                      ("SZSE" if str(x).startswith(("0", "3")) else
                       ("BSE" if str(x).startswith(("8", "4")) else None))
        )
        result["language"] = "zh"
        result["download_status"] = "pending"
        result["parse_status"] = "pending"
        result["is_amendment"] = df.get("announcementTitle", "").str.contains(
            "更正|补充|修订", na=False
        )

        return result
