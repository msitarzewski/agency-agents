
# ============================================================
# 中文名称: 投资风格因子 (CMA)
# 简要说明: Fama-French五因子模型中的投资因子(Conservative Minus Aggressive)，做多保守投资做空激进投资公司的收益。
# 典型用途: 捕获低投资公司相对于高投资公司的超额收益。
# ============================================================
"""academic CMA: investment factor as inverse 60-day volume growth.

Reference:
    Fama, E. F., & French, K. R. (2015). "A five-factor asset pricing model."
    Journal of Financial Economics, 116(1), 1-22.

This is a price-based proxy: the original CMA (Conservative Minus Aggressive)
sorts on asset growth from balance-sheet data. We use the negative of 60-day
log-volume change — firms aggressively scaling activity tend to show rising
trading volume; conservative firms show stable / shrinking volume. Higher
z-scores = volume contraction (conservative).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import delta, ts_mean

__alpha_meta__ = {
    'id': 'academic_cma',
    'nickname': '[PRICE PROXY] FF2015 CMA — investment via inverse volume growth',
    'theme': ['quality'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(-\Delta_{60}\log(\mathrm{ts\_mean}(\mathrm{volume},\,60) + 1)\bigr)',
    'columns_required': ['volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 120,
    'notes': (
        '[PRICE PROXY] for the Fama-French (2015) CMA (Conservative Minus '
        'Aggressive) investment factor. The original definition uses total-asset '
        'growth from fundamental data; here we use the negative 60-day change in '
        'log average volume as an activity-growth proxy, then cross-sectional '
        'z-score per date for long-short ranking. Top z-scores = volume contraction '
        '(conservative / low-growth proxy).'
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
    """Return inverse 60-day log-volume change z-score per stock.

    Uses the canonical 60-bar rolling mean + 60-bar delta windows without
    silent shrink on short panels. Short panels produce all-NaN; the
    registry surfaces this as >95% NaN (RegistryError) so the user sees
    "insufficient history" rather than a misleading shrunk-window value.
    """
    volume = panel['volume']
    log_avg_vol = np.log(ts_mean(volume, 60) + 1.0)
    growth = delta(log_avg_vol, 60)
    return _cross_sectional_zscore(-growth)
