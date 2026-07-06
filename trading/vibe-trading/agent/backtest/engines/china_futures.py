"""China futures backtest engine.

Market rules (exchange-level, CFFEX / SHFE / DCE / ZCE / INE / GFEX):
  - T+0: can open and close same day (intraday trading allowed)
  - Margin trading: 5%~15% by product (exchange-set minimum)
  - Price limits: stock-index +-10%, bonds +-2%, commodities +-3%~8%
  - Commission: per-lot fixed or per-notional rate (varies by product)
  - Contract multiplier: product-specific (IF=300, rb=10, au=1000, ...)
  - Minimum trading unit: 1 contract
  - Night session: 21:00-02:30 (varies by product, not enforced in bar-level sim)
"""

from __future__ import annotations

import re

import pandas as pd

from backtest.engines.futures_base import FuturesBaseEngine


# ── Contract multiplier lookup ──

_MULTIPLIER: dict[str, int] = {
    # Stock index futures (CFFEX)
    "IF": 300, "IC": 200, "IH": 300, "IM": 200,
    # Treasury bond futures (CFFEX)
    "T": 10000, "TF": 10000, "TS": 20000, "TL": 10000,
    # Metals (SHFE)
    "au": 1000, "ag": 15, "cu": 5, "al": 5, "zn": 5,
    "pb": 5, "ni": 1, "sn": 1, "ss": 5,
    # Ferrous (SHFE / DCE)
    "rb": 10, "hc": 10, "i": 100, "j": 100, "jm": 60,
    # Energy (SHFE / INE)
    "sc": 1000, "fu": 10, "lu": 10, "bu": 10, "nr": 10,
    # Agriculture (DCE)
    "c": 10, "cs": 10, "m": 10, "y": 10, "a": 10,
    "p": 10, "jd": 10, "lh": 16, "rr": 10, "pg": 20,
    # Agriculture (ZCE)
    "CF": 5, "SR": 10, "TA": 5, "MA": 10, "AP": 10,
    "RM": 10, "OI": 10, "CJ": 5, "PK": 5, "CY": 5,
    # Chemical (DCE / ZCE)
    "pp": 5, "l": 5, "v": 5, "eg": 10, "eb": 5,
    "PF": 5, "SA": 20, "FG": 20, "UR": 20,
    # GFEX
    "si": 5, "lc": 1,
}

# ── Margin rate (exchange minimum) ──

_MARGIN_RATE: dict[str, float] = {
    # CFFEX stock index
    "IF": 0.12, "IC": 0.12, "IH": 0.12, "IM": 0.12,
    # CFFEX bonds
    "T": 0.03, "TF": 0.02, "TS": 0.015, "TL": 0.035,
    # SHFE metals
    "au": 0.08, "ag": 0.09, "cu": 0.08, "al": 0.07,
    "zn": 0.08, "pb": 0.08, "ni": 0.12, "sn": 0.10, "ss": 0.08,
    # Ferrous
    "rb": 0.10, "hc": 0.10, "i": 0.12, "j": 0.12, "jm": 0.12,
    # Energy
    "sc": 0.10, "fu": 0.10, "lu": 0.10, "bu": 0.10,
    # Agriculture
    "c": 0.07, "cs": 0.07, "m": 0.08, "y": 0.08, "a": 0.08,
    "p": 0.08, "jd": 0.08, "lh": 0.12,
    # Textiles / chemical
    "CF": 0.07, "SR": 0.07, "TA": 0.07, "MA": 0.07,
    "pp": 0.07, "l": 0.07, "v": 0.07, "eg": 0.08,
    "SA": 0.08, "FG": 0.08, "UR": 0.08,
}

# ── Price limit (fraction, ± from settlement) ──

_PRICE_LIMIT: dict[str, float] = {
    # CFFEX stock index ±10%
    "IF": 0.10, "IC": 0.10, "IH": 0.10, "IM": 0.10,
    # CFFEX bonds ±2% (simplified)
    "T": 0.02, "TF": 0.012, "TS": 0.005, "TL": 0.035,
}
_DEFAULT_PRICE_LIMIT = 0.05  # most commodities ±4%~7%, use 5% as default

# ── Commission structure ──
# ("rate", pct) = per-notional  |  ("fixed", amount_per_lot) = per-contract

_COMMISSION: dict[str, tuple[str, float]] = {
    # CFFEX stock index: ~0.0023% of notional
    "IF": ("rate", 0.000023), "IC": ("rate", 0.000023),
    "IH": ("rate", 0.000023), "IM": ("rate", 0.000023),
    # CFFEX bonds
    "T": ("fixed", 3.0), "TF": ("fixed", 3.0), "TS": ("fixed", 3.0),
    # Metals
    "au": ("fixed", 10.0), "ag": ("fixed", 3.0), "cu": ("fixed", 5.0),
    "al": ("fixed", 3.0), "zn": ("fixed", 3.0), "ni": ("fixed", 3.0),
    # Ferrous
    "rb": ("rate", 0.0001), "hc": ("rate", 0.0001), "i": ("rate", 0.0001),
    "j": ("rate", 0.0001), "jm": ("rate", 0.0001),
    # Energy
    "sc": ("fixed", 20.0), "fu": ("rate", 0.00005),
    # Agriculture
    "c": ("fixed", 1.2), "cs": ("fixed", 1.5), "m": ("fixed", 1.5),
    "y": ("fixed", 2.5), "a": ("fixed", 2.0), "p": ("fixed", 2.5),
    "jd": ("rate", 0.00015), "lh": ("rate", 0.0002),
    # Textiles / chemical
    "CF": ("fixed", 4.3), "SR": ("fixed", 3.0), "TA": ("fixed", 3.0),
    "MA": ("fixed", 2.0), "pp": ("fixed", 1.0), "l": ("fixed", 1.0),
    "v": ("fixed", 1.0), "SA": ("fixed", 3.5), "FG": ("fixed", 3.0),
}
_DEFAULT_COMMISSION: tuple[str, float] = ("fixed", 5.0)


def _extract_product(symbol: str) -> str:
    """Extract product code from futures symbol.

    Examples:
        'IF2406.CFFEX' -> 'IF'
        'rb2410.SHFE'  -> 'rb'
        'au2412'       -> 'au'

    Args:
        symbol: Futures symbol string.

    Returns:
        Product code (e.g. 'IF', 'rb', 'au').
    """
    code = symbol.split(".")[0]
    m = re.match(r"([A-Za-z]+)", code)
    return m.group(1) if m else code


class ChinaFuturesEngine(FuturesBaseEngine):
    """China futures engine covering CFFEX / SHFE / DCE / ZCE / INE / GFEX.

    Config keys:
      - slippage: default 0.0005
      - margin_rate_override: override margin rate for all products
      - commission_override: override commission for all products
    """

    def __init__(self, config: dict):
        # Derive leverage from margin rate of first code, or use config override
        margin_override = config.get("margin_rate_override")
        if margin_override:
            leverage = 1.0 / margin_override
        else:
            codes = config.get("codes", [])
            if codes:
                product = _extract_product(codes[0])
                mr = _MARGIN_RATE.get(product, 0.10)
                leverage = 1.0 / mr
            else:
                leverage = 10.0  # ~10% margin default
        config = {**config, "leverage": leverage}
        super().__init__(config)
        self.slippage_rate: float = config.get("slippage", 0.0005)
        self._commission_override = config.get("commission_override")

    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """China futures: T+0, both directions, price-limit enforced.

        Args:
            symbol: Futures code.
            direction: 1 (long), -1 (short), 0 (close).
            bar: Current bar data.

        Returns:
            True if allowed.
        """
        # T+0: no same-day sell restriction
        # Both long and short allowed

        # Price limit check
        pct_chg = _calc_pct_change(bar)
        if pct_chg is not None:
            product = _extract_product(symbol)
            limit = _PRICE_LIMIT.get(product, _DEFAULT_PRICE_LIMIT)
            if direction == 1 and pct_chg >= limit - 0.001:
                return False  # limit-up: can't open long / can't buy
            if direction == -1 and pct_chg <= -limit + 0.001:
                return False  # limit-down: can't open short
            if direction == 0:
                pos = self.positions.get(symbol)
                if pos is not None:
                    # Can't close long at limit-down, can't close short at limit-up
                    if pos.direction == 1 and pct_chg <= -limit + 0.001:
                        return False
                    if pos.direction == -1 and pct_chg >= limit - 0.001:
                        return False
        return True

    def round_size(self, raw_size: float, price: float) -> float:
        """Minimum 1 contract, integer lots only."""
        return max(int(raw_size), 0)

    def calc_commission(self, size: float, price: float, _direction: int, is_open: bool) -> float:
        """Commission varies by product: fixed per-lot or percentage of notional.

        ``_direction`` is unused — reserved for future open/close-fee
        asymmetry (some products charge different rates for close-today).
        """
        if self._commission_override is not None:
            return size * price * self._commission_override
        return self.calc_commission_for_symbol(self._active_symbol, size, price, is_open)

    def calc_commission_for_symbol(
        self, symbol: str, size: float, price: float, is_open: bool,
    ) -> float:
        """Symbol-aware commission calculation.

        Args:
            symbol: Futures code.
            size: Number of contracts.
            price: Execution price.
            is_open: True for opening trade.

        Returns:
            Commission in RMB.
        """
        product = _extract_product(symbol)
        mode, value = _COMMISSION.get(product, _DEFAULT_COMMISSION)
        cm = _MULTIPLIER.get(product, 10)
        if mode == "rate":
            return size * price * cm * value
        return size * value

    def apply_slippage(self, price: float, direction: int) -> float:
        """Futures slippage."""
        return price * (1 + direction * self.slippage_rate)

    def get_contract_multiplier(self, symbol: str) -> float:
        """Look up contract multiplier from product code."""
        product = _extract_product(symbol)
        return float(_MULTIPLIER.get(product, 10))

    def get_margin_rate(self, symbol: str) -> float:
        """Look up exchange margin rate for a product.

        Args:
            symbol: Futures symbol.

        Returns:
            Margin rate (e.g. 0.10 for 10%).
        """
        product = _extract_product(symbol)
        return _MARGIN_RATE.get(product, 0.10)


# ── Helpers ──


# Note: china_a uses close/pre_close-only; global_futures prioritises
# close/pre_close before settle. This China-futures variant prefers
# settle/pre_settle because tushare reports settlement as the canonical
# daily price for domestic contracts. See those modules for the equity /
# global-futures equivalents.
def _calc_pct_change(bar: pd.Series):
    """Calculate bar price change percentage.

    Priority: settle/pre_settle (futures native) > close/pre_close > pct_chg.
    pct_chg from tushare is always in percentage points (0.5 = 0.5%).
    """
    # Prefer settlement prices (unambiguous for futures)
    settle = bar.get("settle")
    pre_settle = bar.get("pre_settle")
    if settle is not None and pre_settle is not None and pre_settle > 0:
        return (float(settle) - float(pre_settle)) / float(pre_settle)

    close = bar.get("close")
    pre_close = bar.get("pre_close")
    if close is not None and pre_close is not None and pre_close > 0:
        return (float(close) - float(pre_close)) / float(pre_close)

    # tushare pct_chg is in percentage points (e.g. 0.5 = 0.5%)
    if "pct_chg" in bar.index:
        val = bar["pct_chg"]
        if pd.notna(val):
            return float(val) / 100.0

    return None
