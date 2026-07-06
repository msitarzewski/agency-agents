"""Forex (FX spot / CFD) backtest engine.

Market rules:
  - 24x5 (Mon Sydney open to Fri NYC close)
  - Spread replaces explicit commission (bid-ask)
  - Leverage: 50:1 to 500:1 (configurable)
  - Standard lot = 100,000 units of base currency
  - Swap (overnight rollover interest) at daily close
  - No price limits, no restrictions on direction
  - PnL in quote currency (converted via exit price for cross pairs)
"""

from __future__ import annotations

import pandas as pd

from backtest.engines.base import BaseEngine
# ``_normalize_symbol`` lives in ``_market_hooks`` (single source of truth);
# re-imported here so external callers (tests) keep their existing import path.
from backtest.engines._market_hooks import _normalize_symbol, calc_forex_swap


# ── Typical spreads in pips (1 pip = 0.0001 for most pairs, 0.01 for JPY) ──

_SPREAD_PIPS: dict[str, float] = {
    # Majors
    "EUR/USD": 1.0, "GBP/USD": 1.2, "USD/JPY": 1.0, "USD/CHF": 1.3,
    "AUD/USD": 1.2, "USD/CAD": 1.5, "NZD/USD": 1.5,
    # Crosses
    "EUR/GBP": 1.5, "EUR/JPY": 1.5, "GBP/JPY": 2.5, "EUR/CHF": 1.8,
    "AUD/JPY": 2.0, "CHF/JPY": 2.5, "EUR/AUD": 2.0, "GBP/AUD": 3.0,
    "EUR/CAD": 2.5, "GBP/CAD": 3.5, "AUD/CAD": 2.5, "NZD/JPY": 2.5,
    # Exotics (wider spreads)
    "USD/TRY": 15.0, "USD/ZAR": 10.0, "USD/MXN": 8.0,
    "USD/SGD": 3.0, "USD/HKD": 3.0, "USD/CNH": 5.0,
}
_DEFAULT_SPREAD_PIPS = 2.0

# Standard lot size
STANDARD_LOT = 100_000


def _pip_value(symbol: str) -> float:
    """Size of 1 pip for the pair.

    Args:
        symbol: Forex pair (e.g. 'EUR/USD', 'USD/JPY').

    Returns:
        1 pip in price terms (0.0001 or 0.01 for JPY pairs).
    """
    quote = symbol.split("/")[1] if "/" in symbol else symbol[3:6]
    return 0.01 if quote.upper() == "JPY" else 0.0001


class ForexEngine(BaseEngine):
    """Forex engine for spot / CFD pairs.

    Config keys:
      - leverage: default 100.0 (100:1)
      - spread_pips_override: override spread for all pairs
      - lot_size: default 100000 (standard lot)
      - swap_enabled: default True
      - slippage_pips: additional slippage beyond spread, default 0.3
    """

    def __init__(self, config: dict):
        config = {**config, "leverage": config.get("leverage", 100.0)}
        super().__init__(config)
        self.spread_override = config.get("spread_pips_override")
        self.lot_size: float = config.get("lot_size", STANDARD_LOT)
        self.swap_enabled: bool = config.get("swap_enabled", True)
        self.slippage_pips: float = config.get("slippage_pips", 0.3)
        self._last_swap_dates: dict = {}  # per-symbol swap tracking

    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """Forex: 24x5, no restrictions."""
        return True

    def round_size(self, raw_size: float, price: float) -> float:
        """Round to micro-lot granularity (0.01 lots = 1000 units).

        Position size is in currency units (not lots) for PnL compatibility.
        Round to nearest 1000 units (micro lot).
        """
        return max(int(raw_size / 1000) * 1000, 0)

    def calc_commission(self, size: float, price: float, _direction: int, is_open: bool) -> float:
        """Forex: spread is the cost, embedded in slippage. No explicit commission.

        Some ECN brokers charge per-lot commission; for simplicity, zero here.
        The cost is captured via apply_slippage (half-spread applied to execution).
        ``_direction`` is unused — reserved for future ECN per-lot fee
        modelling (asymmetric long/short funding).
        """
        return 0.0

    def apply_slippage(self, price: float, direction: int) -> float:
        """Apply half-spread + slippage using _active_symbol for correct pip/spread."""
        return self.apply_slippage_for_symbol(self._active_symbol, price, direction)

    def apply_slippage_for_symbol(self, symbol: str, price: float, direction: int) -> float:
        """Symbol-aware slippage with correct spread.

        Args:
            symbol: Forex pair.
            price: Mid price.
            direction: 1 (buy) or -1 (sell).

        Returns:
            Slipped price.
        """
        pair = _normalize_symbol(symbol)
        pip = _pip_value(pair)

        if self.spread_override is not None:
            spread_pips = self.spread_override
        else:
            spread_pips = _SPREAD_PIPS.get(pair, _DEFAULT_SPREAD_PIPS)

        total_pips = (spread_pips / 2) + self.slippage_pips
        return price + direction * total_pips * pip

    def on_bar(self, symbol: str, bar: pd.Series, timestamp: pd.Timestamp) -> None:
        """Apply daily swap/rollover at end of trading day."""
        if not self.swap_enabled:
            return
        swap = calc_forex_swap(
            symbol, timestamp, self.positions,
            self.lot_size, self._last_swap_dates,
        )
        self.capital += swap

    def get_contract_multiplier(self, symbol: str) -> float:
        """Forex: multiplier is 1.0 (size is in currency units)."""
        return 1.0
