
# ============================================================
# 中文名称: 价值因子 (HML)
# 简要说明: Fama-French三因子模型中的价值因子(High Minus Low)，做多高账面市值比做空低账面市值比的收益。此处使用负的252日收益作为代理。
# 典型用途: 捕获价值股相对于成长股的超额收益，用于价值投资策略。
# ============================================================
"""academic HML: value factor as inverse 252-day return (long-term reversal proxy).

Reference:
    Fama, E. F., & French, K. R. (1993). "Common risk factors in the returns on
    stocks and bonds." Journal of Financial Economics, 33(1), 3-56.

This is a price-based proxy: the original HML (High Minus Low) sorts on book-
to-market, which requires fundamental book equity. We use the negative of the
trailing 252-day return — value names tend to be long-term underperformers
whose prices have declined relative to book value. Higher z-scores = larger
long-term drawdowns (deeper value).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import delta, safe_div

__alpha_meta__ = {
    'id': 'academic_hml',
    'nickname': '[PRICE PROXY] FF1993 HML — value via inverse 252d return',
    'theme': ['value'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(-(\mathrm{close}_t - \mathrm{close}_{t-252}) / \mathrm{close}_{t-252}\bigr)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 252,
    'notes': (
        '[PRICE PROXY] for the Fama-French (1993) HML (High Minus Low) value factor. '
        'The original definition uses book-to-market ratio from fundamental data; here '
        'we use the negative 252-day total return as a long-term reversal proxy, then '
        'cross-sectional z-score per date for long-short ranking. Top z-scores = '
        'long-term underperformers (deeper value). Canonical 252d window; declared '
        'decay_horizon=60 due to registry schema cap (le=60); real signal horizon=252.'
    ),
}


def _cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Per-row z-score: (x - row_mean) / row_std; zero/NaN std rows -> NaN."""
    mean = df.mean(axis=1, skipna=True)
    std = df.std(axis=1, ddof=1, skipna=True)
    centered = df.sub(mean, axis=0)
    result = centered.div(std.where(std > 0), axis=0)
    return result.replace([np.inf, -np.inf], np.nan)


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return inverse 252-day return cross-sectional z-score per stock.

    Uses the canonical 252-day window without silent shrink on short panels.
    Short panels produce an all-NaN result, which the registry surfaces as a
    >95% NaN error (RegistryError) so the user sees "insufficient history"
    instead of a misleading shrunk-window value.
    """
    close = panel['close']
    ret = safe_div(delta(close, 252), close.shift(252))
    return _cross_sectional_zscore(-ret)
