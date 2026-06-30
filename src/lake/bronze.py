"""Bronze layer — raw landing zone.

Stores original payloads as JSON/CSV/HTML snapshots.
No transformation, no dedup — just raw persistence with timestamps.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


class BronzeLayer:
    """Raw data landing zone."""

    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_json(
        self, source: str, table: str, data: Any, suffix: str = ""
    ) -> Path:
        """Write raw JSON data to bronze layer."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_path = self.base_dir / source / table
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{ts}{suffix}.json"
        filepath = dir_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str, indent=2)

        return filepath

    def write_dataframe(
        self, source: str, table: str, df: pd.DataFrame, suffix: str = ""
    ) -> Path:
        """Write raw DataFrame to bronze layer as CSV."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_path = self.base_dir / source / table
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{ts}{suffix}.csv"
        filepath = dir_path / filename

        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        return filepath

    def list_raw(self, source: str, table: str) -> list[Path]:
        """List raw files for a source/table combination."""
        dir_path = self.base_dir / source / table
        if not dir_path.exists():
            return []
        return sorted(dir_path.glob("*"))
