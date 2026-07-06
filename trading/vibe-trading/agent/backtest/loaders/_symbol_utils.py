"""Shared symbol-type detection utilities for loaders.

Exchange-listed ETF / LOF prefix codes (same pattern across loaders):
  SH: 50/51/52/56/58 (ETFs), SZ: 15/16 (ETFs + LOFs).
"""

from __future__ import annotations

_ETF_PREFIXES = frozenset({"15", "16", "50", "51", "52", "56", "58"})


def _is_etf_listed(code: str) -> bool:
    """Detect exchange-listed ETF / LOF symbols (e.g. 510050.SH, 159915.SZ)."""
    upper = code.upper()
    if not upper.endswith((".SH", ".SZ")):
        return False
    digits = upper.split(".")[0]
    if len(digits) != 6 or not digits.isdigit():
        return False
    return digits[:2] in _ETF_PREFIXES
