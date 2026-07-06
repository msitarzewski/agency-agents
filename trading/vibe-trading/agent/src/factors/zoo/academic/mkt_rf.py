
# ============================================================
# 中文名称: 市场超额收益因子 (Mkt-RF)
# 简要说明: Fama-French三因子模型中的市场因子，代表市场组合相对于无风险利率的超额收益。
# 典型用途: 作为市场基准beta，用于资产定价模型中衡量系统性风险暴露。
# ============================================================
"""academic MKT_RF: market factor as 21-day return, cross-sectionally z-scored.

Reference:
    Sharpe, W. F. (1964). "Capital Asset Prices: A Theory of Market Equilibrium
    under Conditions of Risk." The Journal of Finance, 19(3), 425-442.

This is a price-based proxy: the original CAPM market factor is the
value-weighted excess return of the market portfolio. We approximate the
per-stock market-factor exposure as the 21-day total return cross-sectionally
z-scored, suitable for ranking long-short portfolios.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import delta, safe_div

__alpha_meta__ = {
    'id': 'academic_mkt_rf',
    'nickname': '[PRICE PROXY] Market factor (Sharpe 1964) — 21d demeaned return',
    'theme': ['momentum'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl((\mathrm{close}_t - \mathrm{close}_{t-21}) / \mathrm{close}_{t-21}\bigr)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 21,
    'min_warmup_bars': 21,
    'notes': (
        '[PRICE PROXY] for the Sharpe (1964) / Fama-French market factor (MKT-RF). '
        'The original definition uses value-weighted market excess returns; here we '
        'use a 21-day per-stock total return and cross-sectional z-score per date '
        'for long-short ranking. Top z-scores = strong recent winners; bottom = losers.'
    ),
}


def _cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Per-row z-score: (x - row_mean) / row_std; zero/NaN std rows -> NaN."""
    mean = df.mean(axis=1, skipna=True)
    std = df.std(axis=1, ddof=1, skipna=True)
    centered = df.sub(mean, axis=0)
    # std.where(std > 0) turns 0 / NaN std rows into NaN, which propagates
    # through div to NaN — no silent inf.
    result = centered.div(std.where(std > 0), axis=0)
    return result.replace([np.inf, -np.inf], np.nan)


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return 21-day return cross-sectional z-score per stock."""
    close = panel['close']
    ret = safe_div(delta(close, 21), close.shift(21))
    return _cross_sectional_zscore(ret)
