"""Unit normalization utilities.

Key rules:
- Volume: canonical unit is SHARES
  - Tushare vol is in hands (手) -> multiply by 100
  - AKShare 成交量 is in hands -> multiply by 100
  - BaoStock volume is already in shares -> no conversion
- Amount: canonical unit is CNY (yuan)
  - Tushare amount is in thousand yuan (千元) -> multiply by 1000
  - AKShare 成交额 is already in yuan -> no conversion
  - BaoStock amount is in yuan -> no conversion
"""

from typing import Optional


def normalize_volume(
    volume: float | int | None,
    source: str,
    original_unit: str = "hands",
) -> tuple[Optional[int], str]:
    """Normalize volume to shares.

    Returns (volume_in_shares, unit_label).
    """
    if volume is None:
        return None, "shares"

    if source in ("tushare", "akshare"):
        if original_unit == "hands":
            return int(volume * 100), "shares"
        elif original_unit == "shares":
            return int(volume), "shares"
        else:
            return int(volume), original_unit

    if source == "baostock":
        # BaoStock volume is already in shares
        return int(volume), "shares"

    # Unknown source: assume already in shares
    return int(volume), "shares"


def normalize_amount(
    amount: float | None,
    source: str,
    original_unit: str = "thousand_yuan",
) -> tuple[Optional[float], str]:
    """Normalize amount to CNY (yuan).

    Returns (amount_in_yuan, unit_label).
    """
    if amount is None:
        return None, "yuan"

    if source == "tushare":
        if original_unit == "thousand_yuan":
            return float(amount * 1000), "yuan"
        elif original_unit == "yuan":
            return float(amount), "yuan"
        else:
            return float(amount), original_unit

    if source in ("akshare", "baostock"):
        # AKShare and BaoStore amount is already in yuan
        return float(amount), "yuan"

    return float(amount), "yuan"
