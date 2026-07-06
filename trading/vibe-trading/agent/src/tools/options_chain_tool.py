"""Read-only options-chain tool backed by the shared Yahoo Finance client.

Surfaces the calls/puts ladder for a US-listed underlying (strike, bid/ask,
last price, volume, open interest, implied volatility, and the in/out-of-money
flag) for a single expiration. All HTTP routes through
:func:`backtest.loaders.yahoo_client.get_options`, which throttles per host and
reuses one session, so the agent never hits Yahoo un-spaced.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backtest.loaders import yahoo_client
from src.agent.tools import BaseTool

# Upper bound on contracts emitted per side so a deep chain cannot blow up the
# tool payload handed back to the model.
_MAX_CONTRACTS_PER_SIDE = 60

# Yahoo contract fields we surface, mapped to our snake_case envelope keys.
_CONTRACT_FIELDS = (
    ("contractSymbol", "contract_symbol"),
    ("strike", "strike"),
    ("lastPrice", "last_price"),
    ("bid", "bid"),
    ("ask", "ask"),
    ("volume", "volume"),
    ("openInterest", "open_interest"),
    ("impliedVolatility", "implied_volatility"),
    ("inTheMoney", "in_the_money"),
    ("expiration", "expiration"),
)


class OptionsChainTool(BaseTool):
    """Fetch a US equity option chain (calls + puts) with greeks-grade fields."""

    name = "get_options_chain"
    description = (
        "Fetch the US-listed options chain (calls and puts) for one expiration "
        "via Yahoo Finance: per-contract strike, bid/ask, last price, volume, "
        "open interest, implied volatility, and in-the-money flag, plus the list "
        "of available expirations (epoch seconds). Read-only US options data. "
        'Example: get_options_chain(ticker="AAPL").'
    )
    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": (
                    "US underlying symbol, e.g. 'AAPL' or 'AAPL.US' (the .US "
                    "suffix is stripped). Required."
                ),
            },
            "expiration": {
                "type": "integer",
                "description": (
                    "Optional expiration as Unix epoch seconds (one of the "
                    "values from the returned expirations list). Omit for the "
                    "nearest expiration."
                ),
            },
        },
        "required": ["ticker"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Return a JSON-string envelope with the calls/puts chain.

        Args:
            **kwargs: ``ticker`` (str, required) and optional ``expiration``
                (int epoch seconds).

        Returns:
            A JSON string. On success:
            ``{"ok": true, "market": "us", "source": "yahoo", "data": {...}}``
            where ``data`` carries ``ticker``, ``expirations``, ``expiration``,
            ``calls``, ``puts``, and per-side counts. On failure:
            ``{"ok": false, "error": str}``.
        """
        ticker = str(kwargs.get("ticker") or "").strip()
        if not ticker:
            return _error("ticker is required")

        expiration = kwargs.get("expiration")
        normalized_expiration = _coerce_expiration(expiration)
        if expiration is not None and normalized_expiration is None:
            return _error("expiration must be Unix epoch seconds (integer)")

        try:
            result = yahoo_client.get_options(
                ticker, expiration=normalized_expiration
            )
        except Exception as exc:  # noqa: BLE001 - surface as error envelope
            return _error(f"yahoo options request failed: {exc}")

        return _success(ticker, result)


def _coerce_expiration(value: Any) -> Optional[int]:
    """Coerce an epoch-second expiration to ``int``; ``None`` when absent/bad."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _success(ticker: str, result: Dict[str, Any]) -> str:
    """Build the success envelope from a quote-chain ``result[0]`` mapping."""
    expirations = [
        epoch for epoch in (result.get("expirationDates") or []) if epoch is not None
    ]
    options = result.get("options") or []
    block = options[0] if options else {}

    calls = _contracts(block.get("calls"))
    puts = _contracts(block.get("puts"))

    data = {
        "ticker": ticker,
        "expiration": block.get("expirationDate"),
        "expirations": expirations,
        "calls_count": len(calls),
        "puts_count": len(puts),
        "calls": calls,
        "puts": puts,
    }
    return json.dumps(
        {"ok": True, "market": "us", "source": "yahoo", "data": data},
        ensure_ascii=False,
    )


def _contracts(raw: Any) -> List[Dict[str, Any]]:
    """Normalize a Yahoo calls/puts array into capped snake_case rows."""
    if not isinstance(raw, list):
        return []
    rows: List[Dict[str, Any]] = []
    for entry in raw[:_MAX_CONTRACTS_PER_SIDE]:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {our_key: entry.get(yahoo_key) for yahoo_key, our_key in _CONTRACT_FIELDS}
        )
    return rows


def _error(message: str) -> str:
    """Render a failure envelope as a JSON string."""
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
