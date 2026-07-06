"""Pure formatting helpers for the CLI surface.

These mirror the formatting conventions used in the web app (see
``frontend/src/lib/format.ts``) so a duration printed in the CLI reads the
same as one printed in the chat bubble:

* ``format_duration(ms_or_s)`` → ``"230ms" | "1.4s" | "4m 12s"``
* ``format_tokens(n)`` → ``"1.2k tokens" | "452 tokens"``
* ``abbreviate_num(n)`` → ``"$0.003" | "12.4M" | "452"``

All functions are pure and tolerate ``None`` / negative inputs so callers can
hand them raw counter values without pre-validation.
"""

from __future__ import annotations

from typing import Union

Number = Union[int, float]


# ---------------------------------------------------------------------------
# Duration
# ---------------------------------------------------------------------------


def format_duration(value: Number | None, *, unit: str = "ms") -> str:
    """Render a duration as a short, human-readable string.

    Args:
        value: Numeric duration. Treated as milliseconds by default — this
            matches the rest of the codebase (tool callbacks, ``elapsed_ms``
            in ``cli/_legacy.py``, the spinner clock). Pass ``unit="s"`` if
            you already have seconds.
        unit: Either ``"ms"`` (default) or ``"s"``.

    Returns:
        Compact label, e.g. ``"230ms"``, ``"1.4s"``, ``"2m 05s"``. ``None``
        and negative values render as ``"—"``.
    """

    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if v < 0:
        return "—"

    if unit == "s":
        seconds = v
    elif unit == "ms":
        seconds = v / 1000.0
    else:
        raise ValueError(f"unit must be 'ms' or 's', got {unit!r}")

    if seconds < 1.0:
        return f"{int(round(seconds * 1000))}ms"
    if seconds < 60:
        # 1.4s, 12.0s — keep one decimal to communicate sub-second jitter
        return f"{seconds:.1f}s"
    minutes, rem = divmod(int(round(seconds)), 60)
    if minutes < 60:
        return f"{minutes}m {rem:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


def format_tokens(count: Number | None) -> str:
    """Render a token count with a thousands-suffix.

    Args:
        count: Integer-ish token count. ``None`` / negatives → ``"0 tokens"``.

    Returns:
        E.g. ``"452 tokens"``, ``"1.2k tokens"``, ``"3.4M tokens"``.
    """

    if count is None:
        return "0 tokens"
    try:
        n = int(count)
    except (TypeError, ValueError):
        return "0 tokens"
    if n <= 0:
        return "0 tokens"

    if n < 1_000:
        return f"{n} tokens"
    if n < 1_000_000:
        return f"{n / 1_000:.1f}k tokens"
    if n < 1_000_000_000:
        return f"{n / 1_000_000:.1f}M tokens"
    return f"{n / 1_000_000_000:.1f}B tokens"


# ---------------------------------------------------------------------------
# Generic abbreviation (dollars / counts / sizes)
# ---------------------------------------------------------------------------


def abbreviate_num(value: Number | None, *, currency: str | None = None) -> str:
    """Abbreviate a number with magnitude suffix.

    Use this for status-bar numbers where horizontal space is scarce. Currency
    amounts under ``$1`` keep 3-decimal precision so per-call cost reads
    sensibly (e.g. ``$0.003``).

    Args:
        value: Raw number to abbreviate. ``None`` → ``"—"``.
        currency: Optional currency symbol prefix (e.g. ``"$"``). When set,
            small fractional values keep 3 decimals.

    Returns:
        Abbreviated string. Examples::

            abbreviate_num(452)          → "452"
            abbreviate_num(12_400)       → "12.4k"
            abbreviate_num(3_200_000)    → "3.2M"
            abbreviate_num(0.003, currency="$") → "$0.003"
            abbreviate_num(1.42,  currency="$") → "$1.42"
    """

    if value is None:
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"

    prefix = currency or ""
    sign = "-" if n < 0 else ""
    n_abs = abs(n)

    if currency is not None and n_abs < 1.0:
        # 3 decimals communicates per-token / per-call cost precision
        return f"{sign}{prefix}{n_abs:.3f}"

    if n_abs < 1_000:
        if currency is not None or not float(n_abs).is_integer():
            return f"{sign}{prefix}{n_abs:.2f}".rstrip("0").rstrip(".")
        return f"{sign}{prefix}{int(n_abs)}"

    for unit, divisor in (("k", 1_000), ("M", 1_000_000), ("B", 1_000_000_000), ("T", 1_000_000_000_000)):
        if n_abs < divisor * 1_000:
            return f"{sign}{prefix}{n_abs / divisor:.1f}{unit}"

    return f"{sign}{prefix}{n_abs:.1e}"


__all__ = ["format_duration", "format_tokens", "abbreviate_num"]
