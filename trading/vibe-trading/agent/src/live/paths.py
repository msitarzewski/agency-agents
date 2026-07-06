"""Filesystem layout for the live trading channel.

All live-channel state is rooted at ``<runtime_root>/live`` (where
``runtime_root`` defaults to ``~/.vibe-trading``, the same root the swarm
config and persistent memory resolve, via :func:`src.config.paths.get_runtime_root`).

Layout (see the live-trading SPEC §2)::

    <runtime_root>/live/robinhood/oauth/        # OAuth token cache (0700/0600)
    <runtime_root>/live/robinhood/mandate.json  # committed mandate (0600)
    <runtime_root>/live/robinhood/trade_counter.json
    <runtime_root>/live/HALT                     # kill-switch sentinel
    <runtime_root>/live/audit.jsonl              # live-action ledger (append-only)
"""

from __future__ import annotations

from pathlib import Path

from src.config.paths import get_runtime_root


def live_root() -> Path:
    """Return the root directory for all live-channel state.

    Returns:
        ``<runtime_root>/live``. The directory is NOT created here; callers
        that write create their own subtree with the correct ``0700`` perms.
    """
    return get_runtime_root() / "live"


def broker_dir(broker: str) -> Path:
    """Return the per-broker state directory under the live root.

    Args:
        broker: Broker key, e.g. ``"robinhood"``. Normalized to lower-case and
            stripped so a stray ``"Robinhood "`` resolves to the same dir.

    Returns:
        ``<runtime_root>/live/<broker>``. Not created here.

    Raises:
        ValueError: If ``broker`` is empty/whitespace or contains a path
            separator or ``..`` segment (a broker key is never a path).
    """
    key = broker.strip().lower()
    if not key:
        raise ValueError("broker key must not be empty")
    if "/" in key or "\\" in key or ".." in key:
        raise ValueError(f"invalid broker key: {broker!r}")
    return live_root() / key
