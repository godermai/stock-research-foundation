"""Tests for announcement schema and hashing."""

import pytest
import hashlib
import tempfile
from pathlib import Path
from src.adapters.cninfo_adapter import CNINFOAdapter


class TestCNINFOHashing:
    def test_sha256_computation(self):
        """Verify SHA256 is computed correctly for downloaded files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = CNINFOAdapter(raw_dir=tmpdir)
            test_file = Path(tmpdir) / "test.txt"
            test_content = b"test content for hashing"
            test_file.write_bytes(test_content)

            expected = hashlib.sha256(test_content).hexdigest()
            actual = adapter._compute_sha256(test_file)
            assert actual == expected

    def test_normalize_announcements_empty(self):
        """Empty DataFrame should return empty."""
        adapter = CNINFOAdapter(raw_dir="/tmp/test_cninfo")
        result = adapter.normalize_announcements(
            __import__("pandas").DataFrame(), "600519.SH"
        )
        assert result.empty


class TestAnnouncementSchema:
    def test_announcement_has_required_fields(self):
        """Verify canonical announcement columns exist in schema."""
        from src.models.schema import ANNOUNCEMENT_COLUMNS
        col_names = [c.name for c in ANNOUNCEMENT_COLUMNS]
        required = [
            "symbol", "announcement_id", "title", "announcement_date",
            "category", "source_url", "local_path", "content_hash",
            "source", "fetched_at",
        ]
        for r in required:
            assert r in col_names, f"Missing required column: {r}"
