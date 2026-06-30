"""Unified configuration management for the stock research data foundation.

All settings are loaded from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class Config:
    """Central configuration for the entire project."""

    # --- Paths ---
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    raw_dir: Path = Path(os.getenv("DATA_DIR", "data")) / "raw"
    curated_dir: Path = Path(os.getenv("DATA_DIR", "data")) / "curated"
    extracts_dir: Path = Path(os.getenv("DATA_DIR", "data")) / "extracts"
    db_dir: Path = Path(os.getenv("DB_DIR", "db"))

    # --- Database ---
    duckdb_path: Path = Path(os.getenv("DUCKDB_PATH", "db/market.duckdb"))
    sqlite_path: Path = Path(os.getenv("SQLITE_PATH", "db/state.sqlite"))

    # --- API Tokens ---
    tushare_token: str | None = field(default_factory=lambda: os.getenv("TUSHARE_TOKEN"))

    # --- Sync Schedule ---
    sync_market_daily_cron: str = os.getenv("SYNC_MARKET_DAILY_CRON", "0 18 * * 1-5")
    sync_financials_cron: str = os.getenv("SYNC_FINANCIALS_CRON", "0 20 * * 1-5")
    sync_announcements_cron: str = os.getenv("SYNC_ANNOUNCEMENTS_CRON", "0 10,14 * * 1-5")

    # --- MCP ---
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "stdio")
    mcp_log_level: str = os.getenv("MCP_LOG_LEVEL", "INFO")

    # --- Logging ---
    log_dir: Path = Path(os.getenv("LOG_DIR", "logs"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        """Ensure critical directories exist."""
        for d in [self.data_dir, self.raw_dir, self.curated_dir,
                  self.extracts_dir, self.db_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)


# Singleton instance
config = Config()
