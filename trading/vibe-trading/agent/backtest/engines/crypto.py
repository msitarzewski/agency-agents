"""Crypto perpetual-contract backtest engine.

Market rules:
  - 24/7 trading, no restrictions on direction
  - Maker/Taker fee separation
  - Funding fee settlement every 8 hours (00:00/08:00/16:00 UTC)
  - Forced liquidation when maintenance margin ratio <= 100%
  - Fractional position sizes allowed
"""

from __future__ import annotations

import pandas as pd

from backtest.engines.base import BaseEngine
from backtest.engines._market_hooks import (
    calc_crypto_funding_fee,
    check_crypto_liquidation,
)


class CryptoEngine(BaseEngine):
    """Crypto perpetual contract engine.

    Config keys:
      - leverage: default 1.0
      - maker_rate: default 0.0002
      - taker_rate: default 0.0005
      - slippage: default 0.0005
      - margin_mode: "isolated" (default) or "cross"
      - funding_rate: fixed rate per settlement, default 0.0001
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.maker_rate: float = config.get("maker_rate", 0.0002)
        self.taker_rate: float = config.get("taker_rate", 0.0005)
        self.slippage_rate: float = config.get("slippage", 0.0005)
        self.funding_rate: float = config.get("funding_rate", 0.0001)
        self._funding_applied: set = set()   # (symbol, date, hour) — per-slot dedup
        self._funding_daily_done: set = set()  # (symbol, date) — daily fallback dedup

    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """Crypto: 24/7, long/short/close all allowed."""
        return True

    def round_size(self, raw_size: float, price: float) -> float:
        """Crypto supports fractional sizes, round to 6 decimals."""
        return round(max(raw_size, 0.0), 6)

    def calc_commission(self, size: float, price: float, _direction: int, is_open: bool) -> float:
        """Maker/Taker separated. Opens typically hit taker, closes hit maker.

        ``_direction`` is unused — reserved for future funding-rate asymmetry
        between long/short legs on perp swaps.
        """
        rate = self.taker_rate if is_open else self.maker_rate
        return size * price * rate

    def apply_slippage(self, price: float, direction: int) -> float:
        """Slippage: unfavourable direction."""
        return price * (1 + direction * self.slippage_rate)

    def on_bar(self, symbol: str, bar: pd.Series, timestamp: pd.Timestamp) -> None:
        """Crypto per-bar hooks: funding fee + liquidation check."""
        fee = calc_crypto_funding_fee(
            symbol, bar, timestamp, self.positions,
            self.funding_rate, self._funding_applied, self._funding_daily_done,
        )
        self.capital -= fee

        if check_crypto_liquidation(symbol, bar, self.positions):
            pos = self.positions.get(symbol)
            if pos is not None:
                mark_price = float(bar.get("close", pos.entry_price))
                liq_price = self.apply_slippage(mark_price, -pos.direction)
                self._close_position(symbol, liq_price, timestamp, "liquidation")
