"""Tests for announcement completeness and PDF retention."""

import pytest
import tempfile
import os
from pathlib import Path
from src.adapters.cninfo_adapter import CNINFOAdapter


class TestAnnouncementCompleteness:
    def test_pdf_hash_computation(self):
        """Verify PDF SHA256 is computed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = CNINFOAdapter(raw_dir=tmpdir)
            test_file = Path(tmpdir) / "test.pdf"
            test_content = b"%PDF-1.4 test content"
            test_file.write_bytes(test_content)

            import hashlib
            expected = hashlib.sha256(test_content).hexdigest()
            actual = adapter._compute_sha256(test_file)
            assert actual == expected
            assert len(actual) == 64  # SHA256 hex length

    def test_download_already_exists(self):
        """If PDF already exists, should return already_exists status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = CNINFOAdapter(raw_dir=tmpdir)

            # Create a pre-existing file
            symbol = "600519.SH"
            safe_symbol = symbol.replace(".", "_")
            ann_dir = Path(tmpdir) / safe_symbol
            ann_dir.mkdir(parents=True, exist_ok=True)
            existing_file = ann_dir / "20240115_test123.pdf"
            existing_file.write_bytes(b"existing content")

            # Try to download the same announcement
            announcement = {
                "adjunctUrl": "test/path.pdf",
                "announcementId": "test123",
                "announcementTime": 1705276800000,  # 2024-01-15
            }
            result = adapter.download_pdf(announcement, symbol)
            assert result["download_status"] == "already_exists"
            assert result["pdf_sha256"] is not None

    def test_announcement_metadata_retained_on_download_failure(self):
        """Even if PDF download fails, metadata should be retained."""
        import pandas as pd
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = CNINFOAdapter(raw_dir=tmpdir)

            # Create fake announcement data
            df = pd.DataFrame({
                "announcementId": ["ann001"],
                "announcementTitle": ["Test Announcement"],
                "announcementTime": [1705276800000],
                "announcementTypeName": ["定期报告"],
                "adjunctUrl": [""],  # No URL -> will be skipped
                "secCode": ["600519"],
            })

            normalized = adapter.normalize_announcements(df, "600519.SH")
            assert len(normalized) == 1
            assert normalized.iloc[0]["symbol"] == "600519.SH"
            assert normalized.iloc[0]["title"] == "Test Announcement"
            # Download status should be pending initially
            assert normalized.iloc[0]["download_status"] == "pending"

    def test_amendment_detection(self):
        """Announcements with 更正/补充/修订 should be flagged as amendments."""
        import pandas as pd
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = CNINFOAdapter(raw_dir=tmpdir)

            df = pd.DataFrame({
                "announcementId": ["ann001", "ann002", "ann003"],
                "announcementTitle": [
                    "2024年年度报告",
                    "2024年年度报告更正公告",
                    "关于补充披露的公告",
                ],
                "announcementTime": [1705276800000] * 3,
                "announcementTypeName": ["定期报告"] * 3,
                "adjunctUrl": [""] * 3,
                "secCode": ["600519"] * 3,
            })

            normalized = adapter.normalize_announcements(df, "600519.SH")
            assert normalized.iloc[0]["is_amendment"] == False  # Original
            assert normalized.iloc[1]["is_amendment"] == True   # 更正
            assert normalized.iloc[2]["is_amendment"] == True   # 补充
