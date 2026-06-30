"""Symbol normalization utilities.

Canonical format: XXXXXX.SH / XXXXXX.SZ / XXXXXX.BJ / XXXXXX.HK
"""

import re
from typing import Optional


# Exchange prefixes and their canonical suffixes
EXCHANGE_MAP = {
    "sh": "SH",
    "sz": "SZ",
    "bj": "BJ",
    "hk": "HK",
}

# Board inference rules based on code prefix
BOARD_RULES = [
    ("60", "main", "SH"),      # Shanghai main board
    ("68", "star", "SH"),      # STAR Market
    ("00", "main", "SZ"),      # Shenzhen main board
    ("30", "chinext", "SZ"),   # ChiNext
    ("92", "bse", "BJ"),       # Beijing Stock Exchange
    ("83", "bse", "BJ"),       # BSE (older range)
    ("87", "bse", "BJ"),       # BSE (newer range)
    ("43", "bse", "BJ"),       # BSE (legacy NEEQ)
]


def normalize_symbol(raw: str, source: str = "unknown") -> str:
    """Normalize any symbol variant to canonical XXXXXX.SH/SZ/BJ/HK format.

    Handles:
    - Tushare: 600519.SH (already canonical)
    - BaoStock: sh.600519
    - AKShare: 600519 (bare, infer exchange)
    - Generic: sh600519, SH600519
    """
    if not raw:
        raise ValueError("Symbol cannot be empty")

    s = raw.strip().upper()

    # Already canonical: 600519.SH
    if re.match(r"^\d{6}\.(SH|SZ|BJ|HK)$", s):
        return s

    # BaoStock style: sh.600519
    m = re.match(r"^(SH|SZ|BJ|HK)\.(\d{6})$", s)
    if m:
        return f"{m.group(2)}.{m.group(1)}"

    # Prefixed without dot: sh600519
    m = re.match(r"^(SH|SZ|BJ|HK)(\d{6})$", s)
    if m:
        return f"{m.group(2)}.{m.group(1)}"

    # Bare 6-digit code: infer exchange from prefix
    m = re.match(r"^(\d{6})$", s)
    if m:
        code = m.group(1)
        exchange = infer_exchange(code)
        if exchange:
            return f"{code}.{exchange}"
        raise ValueError(f"Cannot infer exchange for code: {code}")

    # Hong Kong: 5-digit or 4-digit
    m = re.match(r"^0(\d{4})$", s)
    if m:
        return f"0{m.group(1)}.HK"

    raise ValueError(f"Cannot normalize symbol: {raw} (source={source})")


def denormalize_symbol(canonical: str, target: str = "baostock") -> str:
    """Convert canonical symbol to a source-specific format.

    target: 'baostock' -> sh.600519, 'tushare' -> 600519.SH, 'bare' -> 600519
    """
    parts = canonical.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid canonical symbol: {canonical}")

    code, exchange = parts[0], parts[1]

    if target == "baostock":
        return f"{exchange.lower()}.{code}"
    elif target == "tushare":
        return canonical  # Tushare uses canonical format
    elif target == "bare":
        return code
    elif target == "akshare":
        return code  # AKShare typically uses bare codes
    else:
        raise ValueError(f"Unknown target format: {target}")


def infer_exchange(code: str) -> Optional[str]:
    """Infer exchange from a 6-digit stock code."""
    for prefix, board, exchange in BOARD_RULES:
        if code.startswith(prefix):
            return exchange
    return None


def infer_board(code: str) -> Optional[str]:
    """Infer board from a 6-digit stock code."""
    for prefix, board, exchange in BOARD_RULES:
        if code.startswith(prefix):
            return board
    return None
