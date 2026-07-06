
# ============================================================
# 中文名称: 盈利能力因子 (RMW)
# 简要说明: Fama-French五因子模型中的盈利能力因子(Robust Minus Weak)，做多高盈利做空低盈利公司的收益。
# 典型用途: 捕获高盈利能力公司相对于低盈利能力公司的超额收益。
# ============================================================
"""academic RMW: profitability factor as inverse 60-day return volatility.

Reference:
    Fama, E. F., & French, K. R. (2015). "A five-factor asset pricing model."
    Journal of Financial Economics, 116(1), 1-22.

This is a price-based proxy: the original RMW (Robust Minus Weak) sorts on
operating profitability from income statements. We use the negative of trailing
60-day realized return volatility — robust (profitable) firms historically
exhibit lower idiosyncratic volatility (the "low-vol anomaly" overlap). Higher
z-scores = lower volatility = quality proxy.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import delta, safe_div, ts_std

__alpha_meta__ = {
    'id': 'academic_rmw',
    'nickname': '[PRICE PROXY] FF2015 RMW — quality via inverse 60d volatility',
    'theme': ['quality'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(-\mathrm{ts\_std}((\mathrm{close}_t - \mathrm{close}_{t-1}) / \mathrm{close}_{t-1},\,60)\bigr)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
    'notes': (
        '[PRICE PROXY] for the Fama-French (2015) RMW (Robust Minus Weak) '
        'profitability factor. The original definition uses operating profitability '
        'from fundamental data; here we use the negative of 60-day return volatility '
        'as a low-vol-quality proxy, then cross-sectional z-score per date for '
        'long-short ranking. Top z-scores = lower vol (quality / robust).'
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
    """Return inverse 60-day return-volatility z-score per stock."""
    close = panel['close']
    ret_1d = safe_div(delta(close, 1), close.shift(1))
    vol_60 = ts_std(ret_1d, 60)
    return _cross_sectional_zscore(-vol_60)
