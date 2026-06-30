"""Tests for the CLI interface and acceptance criteria."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import build_parser, main as cli_main
from src.acceptance import run_acceptance, ALL_CHECKS


class TestCLIParser:
    def test_parser_has_all_commands(self):
        parser = build_parser()
        help_text = parser.format_help()
        for cmd in ["init", "sync", "mcp", "query", "status", "test", "accept"]:
            assert cmd in help_text, f"Missing command: {cmd}"

    def test_parser_sync_choices(self):
        parser = build_parser()
        args = parser.parse_args(["sync", "security-master"])
        assert args.table == "security-master"

        args = parser.parse_args(["sync", "market-daily", "--symbol", "600519.SH"])
        assert args.table == "market-daily"
        assert args.symbol == "600519.SH"

    def test_parser_query_requires_sql(self):
        parser = build_parser()
        args = parser.parse_args(["query", "--sql", "SELECT 1"])
        assert args.sql == "SELECT 1"

    def test_parser_accept_json_flag(self):
        parser = build_parser()
        args = parser.parse_args(["accept", "--json"])
        assert args.json is True


class TestCLIInit:
    def test_init_creates_database(self, tmp_path):
        db_path = tmp_path / "test.duckdb"
        os.environ["DUCKDB_PATH"] = str(db_path)
        os.environ["DATA_DIR"] = str(tmp_path / "data")
        try:
            rc = cli_main(["init"])
            assert rc == 0
            assert db_path.exists()
        finally:
            os.environ.pop("DUCKDB_PATH", None)
            os.environ.pop("DATA_DIR", None)


class TestCLIQuery:
    def test_query_returns_rows(self, tmp_path):
        db_path = tmp_path / "test.duckdb"
        os.environ["DUCKDB_PATH"] = str(db_path)
        os.environ["DATA_DIR"] = str(tmp_path / "data")
        try:
            cli_main(["init"])
            rc = cli_main(["query", "--sql", "SELECT 42 as answer"])
            assert rc == 0
        finally:
            os.environ.pop("DUCKDB_PATH", None)
            os.environ.pop("DATA_DIR", None)


class TestCLIStatus:
    def test_status_empty_database(self, tmp_path):
        db_path = tmp_path / "test.duckdb"
        os.environ["DUCKDB_PATH"] = str(db_path)
        os.environ["DATA_DIR"] = str(tmp_path / "data")
        try:
            cli_main(["init"])
            rc = cli_main(["status"])
            assert rc == 0
        finally:
            os.environ.pop("DUCKDB_PATH", None)
            os.environ.pop("DATA_DIR", None)


class TestCLIAccept:
    def test_accept_json_output(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.acceptance.ALL_CHECKS", ALL_CHECKS[:3])
        rc = cli_main(["accept", "--json"])
        assert rc == 0

    def test_accept_text_output(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.acceptance.ALL_CHECKS", ALL_CHECKS[:3])
        rc = cli_main(["accept"])
        assert rc == 0


class TestAcceptanceModule:
    def test_all_checks_have_required_fields(self):
        results = run_acceptance()
        assert "checks" in results
        assert "passed" in results
        assert "failed" in results
        assert "total" in results
        assert "overall" in results
        assert results["total"] == len(ALL_CHECKS)

    def test_each_check_has_id_name_status(self):
        results = run_acceptance()
        for check in results["checks"]:
            assert "id" in check
            assert "name" in check
            assert "status" in check
            assert check["status"] in ("pass", "fail")

    def test_check_ids_are_unique(self):
        results = run_acceptance()
        ids = [c["id"] for c in results["checks"]]
        assert len(ids) == len(set(ids)), "Duplicate check IDs"

    def test_check_count(self):
        assert len(ALL_CHECKS) >= 13, f"Expected >=13 checks, got {len(ALL_CHECKS)}"
