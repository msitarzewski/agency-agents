"""Global futures backtest engine (CME / ICE / Eurex).

Market rules:
  - Nearly 24x5 (CME Globex: Sun 17:00 - Fri 16:00 CT, daily pause 16:00-17:00)
  - Margin: initial + maintenance (exchange-set per contract)
  - Limit up/down: dynamic for equity index, fixed for commodities
  - Contract multiplier: per-product (ES=$50/pt, CL=$1000/bbl, GC=$100/oz)
  - Commission: per-contract ($1-3 per side typical)
  - Minimum unit: 1 contract
  - Roll/expiry: not modeled (assumes continuous front-month data)
"""

from __future__ import annotations

import re

import pandas as pd

from backtest.engines.futures_base import FuturesBaseEngine


# ── Contract multiplier (USD per point / per unit) ──

_MULTIPLIER: dict[str, float] = {
    # Equity index (CME)
    "ES": 50, "NQ": 20, "YM": 5, "RTY": 50,
    # Micro equity index
    "MES": 5, "MNQ": 2, "MYM": 0.5, "M2K": 5,
    # Energy (NYMEX)
    "CL": 1000, "NG": 10000, "RB": 42000, "HO": 42000,
    # Metals (COMEX)
    "GC": 100, "SI": 5000, "HG": 25000, "PL": 50, "PA": 100,
    # Micro metals
    "MGC": 10, "SIL": 1000,
    # Grains (CBOT)
    "ZC": 50, "ZS": 50, "ZW": 50, "ZM": 100, "ZL": 600,
    # Bonds (CBOT)
    "ZB": 1000, "ZN": 1000, "ZF": 1000, "ZT": 2000,
    # Currencies (CME)
    "6E": 125000, "6J": 12500000, "6B": 62500, "6A": 100000, "6C": 100000,
    # Softs (ICE)
    "KC": 37500, "SB": 112000, "CC": 10, "CT": 50000,
    # Livestock (CME)
    "LE": 400, "HE": 400, "GF": 500,
    # Eurex
    "FESX": 10, "FDAX": 25, "FGBL": 1000,
}

# ── Margin per contract (approximate USD, initial margin) ──
# Reference table — future use for margin-call checks. Not yet consumed.

_MARGIN_PER_CONTRACT: dict[str, float] = {
    # Equity index
    "ES": 12650, "NQ": 17600, "YM": 8800, "RTY": 6600,
    "MES": 1265, "MNQ": 1760,
    # Energy
    "CL": 6270, "NG": 3300,
    # Metals
    "GC": 9950, "SI": 11000, "HG": 4400, "PL": 3300,
    "MGC": 995,
    # Grains
    "ZC": 1650, "ZS": 2200, "ZW": 1925,
    # Bonds
    "ZB": 4400, "ZN": 2200, "ZF": 1375,
    # Currencies
    "6E": 2475, "6J": 3300, "6B": 2750,
}

# ── Price limit (fraction of prev settlement) ──

_PRICE_LIMIT: dict[str, float] = {
    # Equity index: 7% (Level 1), simplified to single level
    "ES": 0.07, "NQ": 0.07, "YM": 0.07, "RTY": 0.07,
    "MES": 0.07, "MNQ": 0.07,
    # Energy: varies, typically ~$10-15 for CL
    # Not easily expressed as %, skip for most commodities
}

# ── Per-contract commission (USD, one side) ──

_COMMISSION_PER_CONTRACT: dict[str, float] = {
    "ES": 2.25, "NQ": 2.25, "YM": 2.25, "RTY": 2.25,
    "MES": 0.62, "MNQ": 0.62,
    "CL": 2.25, "NG": 2.25,
    "GC": 2.25, "SI": 2.25, "HG": 2.25,
    "MGC": 0.62,
    "ZC": 2.25, "ZS": 2.25, "ZW": 2.25,
    "ZB": 1.52, "ZN": 1.52, "ZF": 1.02,
    "6E": 2.25, "6J": 2.25, "6B": 2.25,
}
_DEFAULT_COMMISSION = 2.50


_MONTH_CODES = set("FGHJKMNQUVXZ")


def _extract_product(symbol: str) -> str:
    """Extract product code from futures symbol.

    Handles CME conventions:
      - Product + month-code + year:  ESZ4, CLF25, GCM2025
      - Product + YYMM:              CL2412, NQ2503
      - Product.exchange:            ES.CME
      - Bare product:                ES

    Args:
        symbol: Futures symbol string.

    Returns:
        Product code (e.g. 'ES', 'CL', 'GC').
    """
    code = symbol.split(".")[0].upper()

    # Pattern 1: product + month-code + year (ESZ4, CLF25, GCM2025)
    m = re.match(r"([A-Z]{2,4})([FGHJKMNQUVXZ])(\d{1,4})$", code)
    if m:
        return m.group(1)

    # Pattern 2: product + YYMM (NQ2503, CL2412)
    m = re.match(r"([A-Z]+)(\d{4})$", code)
    if m:
        return m.group(1)

    # Pattern 3: bare product or fallback
    m = re.match(r"([A-Z]+)", code)
    return m.group(1) if m else code


class GlobalFuturesEngine(FuturesBaseEngine):
    """International futures engine (CME/CBOT/NYMEX/COMEX/ICE/Eurex).

    Config keys:
      - slippage: default 0.0003
      - commission_per_contract: override, default varies by product
    """

    def __init__(self, config: dict):
        # Leverage: most futures have 5-15% margin → 7-20x leverage.
        # Price is unknown at init, so use a reasonable fixed default.
        # User can override via config["leverage"].
        leverage = config.get("leverage", 10.0)
        config = {**config, "leverage": leverage}
        super().__init__(config)
        self.slippage_rate: float = config.get("slippage", 0.0003)
        self._comm_override = config.get("commission_per_contract")

    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """Global futures: T+0, both directions, limit checks for equity index.

        Args:
            symbol: Futures symbol.
            direction: 1 (long), -1 (short), 0 (close).
            bar: Current bar data.

        Returns:
            True if allowed.
        """
        product = _extract_product(symbol)
        limit = _PRICE_LIMIT.get(product)
        if limit is None:
            return True  # no price limit for most commodities

        pct_chg = _calc_pct_change(bar)
        if pct_chg is not None:
            if direction == 1 and pct_chg >= limit - 0.001:
                return False  # limit-up
            if direction == -1 and pct_chg <= -limit + 0.001:
                return False  # limit-down
            if direction == 0:
                pos = self.positions.get(symbol)
                if pos is not None:
                    if pos.direction == 1 and pct_chg <= -limit + 0.001:
                        return False
                    if pos.direction == -1 and pct_chg >= limit - 0.001:
                        return False
        return True

    def round_size(self, raw_size: float, price: float) -> float:
        """Integer contracts, minimum 1."""
        return max(int(raw_size), 0)

    def calc_commission(self, size: float, price: float, _direction: int, is_open: bool) -> float:
        """Per-contract fixed commission (uses _active_symbol for product lookup).

        ``_direction`` is unused — reserved for future borrow/financing
        asymmetry on short positions.
        """
        if self._comm_override is not None:
            return size * self._comm_override
        return self.calc_commission_for_symbol(self._active_symbol, size, price, is_open)

    def calc_commission_for_symbol(
        self, symbol: str, size: float, price: float, is_open: bool,
    ) -> float:
        """Symbol-aware commission.

        Args:
            symbol: Futures code.
            size: Number of contracts.
            price: Execution price (unused — fixed per-lot).
            is_open: Opening or closing.

        Returns:
            Commission in USD.
        """
        product = _extract_product(symbol)
        rate = _COMMISSION_PER_CONTRACT.get(product, _DEFAULT_COMMISSION)
        return size * rate

    def apply_slippage(self, price: float, direction: int) -> float:
        """Slippage model for liquid global futures."""
        return price * (1 + direction * self.slippage_rate)

    def get_contract_multiplier(self, symbol: str) -> float:
        """Product-specific contract multiplier."""
        product = _extract_product(symbol)
        return float(_MULTIPLIER.get(product, 50))


# ── Helpers ──


# Note: china_a uses close/pre_close-only; china_futures prioritises
# settle/pre_settle. This global-futures variant prefers close/pre_close
# because CME data feeds (yfinance/IB) expose continuous close more
# reliably than settlement. See those modules for the equity /
# China-futures equivalents.
def _calc_pct_change(bar: pd.Series):
    """Calculate bar price change percentage.

    Priority: close/pre_close > settle/pre_settle > pct_chg.
    Falls back to pct_chg only when price fields are absent.
    """
    close = bar.get("close")
    pre_close = bar.get("pre_close")
    if close is not None and pre_close is not None and pre_close > 0:
        return (float(close) - float(pre_close)) / float(pre_close)

    settle = bar.get("settle")
    pre_settle = bar.get("pre_settle")
    if settle is not None and pre_settle is not None and pre_settle > 0:
        return (float(settle) - float(pre_settle)) / float(pre_settle)

    if "pct_chg" in bar.index:
        val = bar["pct_chg"]
        if pd.notna(val):
            raw = float(val)
            # Heuristic: values > 1 are likely percentage points
            return raw / 100.0 if abs(raw) > 1.0 else raw

    return None
