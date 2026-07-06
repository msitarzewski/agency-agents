"""Global equity (US / HK) backtest engine.

Market rules:
  US:
    - T+0, long/short allowed
    - Zero commission (retail brokers)
    - Fractional shares supported (round to 0.01)
    - Low slippage (high liquidity)
  HK:
    - T+0, long/short allowed
    - Stamp tax 0.1% bilateral + levies
    - Lot-size rounding (simplified to 100 shares)
    - Higher slippage than US
"""

from __future__ import annotations

import pandas as pd

from backtest.engines.base import BaseEngine


class GlobalEquityEngine(BaseEngine):
    """US / HK equity engine, selected by *market* parameter.

    Config keys:
      - slippage_us: default 0.0005
      - slippage_hk: default 0.001
      - hk_stamp_tax: default 0.001 (0.1% bilateral)
      - hk_commission: default 0.00015 (万1.5)
      - hk_levy: default 0.0000565 (SFC + FRC)
      - hk_settlement: default 0.00002 (CCASS)
    """

    def __init__(self, config: dict, market: str = "us"):
        config = {**config, "leverage": config.get("leverage", 1.0)}
        super().__init__(config)
        self.market = market

        # US defaults
        self.slippage_us: float = config.get("slippage_us", 0.0005)
        # HK defaults
        self.slippage_hk: float = config.get("slippage_hk", 0.001)
        self.hk_stamp_tax: float = config.get("hk_stamp_tax", 0.001)
        self.hk_commission: float = config.get("hk_commission", 0.00015)
        self.hk_levy: float = config.get("hk_levy", 0.0000565)
        self.hk_settlement: float = config.get("hk_settlement", 0.00002)

    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """US/HK: T+0, both directions allowed."""
        return True

    def round_size(self, raw_size: float, price: float) -> float:
        """US: fractional shares (0.01). HK: 100-share lots."""
        if self.market == "hk":
            return max(int(raw_size / 100) * 100, 0)
        return round(max(raw_size, 0.0), 2)

    def calc_commission(self, size: float, price: float, _direction: int, is_open: bool) -> float:
        """US: zero commission. HK: stamp tax + levies.

        ``_direction`` is unused — reserved for future short-borrow fees
        (US Reg-T margin, HK SBL costs).
        """
        if self.market == "hk":
            notional = size * price
            comm = notional * self.hk_commission       # broker commission
            comm += notional * self.hk_stamp_tax       # stamp tax bilateral
            comm += notional * self.hk_levy            # SFC + FRC levies
            comm += notional * self.hk_settlement      # CCASS settlement
            return comm
        # US: zero commission (SEC fee negligible)
        return 0.0

    def apply_slippage(self, price: float, direction: int) -> float:
        """US: low slippage. HK: moderate slippage."""
        rate = self.slippage_hk if self.market == "hk" else self.slippage_us
        return price * (1 + direction * rate)
