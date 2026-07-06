
# ============================================================
# 中文名称: 收益偏度因子 (RETSKEW)
# 简要说明: 过去一段时间日收益分布偏度越低(越负偏)，预期收益越高。Harvey & Siddique(2000)的偏度溢价。
# 典型用途: 捕获特质偏度溢价，做多负偏(类彩票反向)的股票，用于偏度风格分析。
# ============================================================
"""academic return skewness: inverse trailing skewness of daily returns.

Reference:
    Harvey, C. R., & Siddique, A. (2000). "Conditional Skewness in Asset
    Pricing Tests." The Journal of Finance, 55(3), 1263-1295.

Investors pay a premium for positively-skewed (lottery-like) payoffs, so
positively-skewed stocks earn lower subsequent returns and negatively-skewed
stocks earn higher ones. Computed as the negative of the trailing 60-day
skewness of daily returns, then cross-sectional z-scored per date. Higher
z-scores = more negatively-skewed names (the long leg of the skewness premium).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'academic_retskew',
    'nickname': 'Harvey-Siddique 2000 return skewness — inverse 60d skew',
    'theme': ['volatility'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(-\mathrm{skew}_{60}(r_t)\bigr)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 61,
    'notes': (
        'Harvey & Siddique (2000) skewness premium. Negative of the trailing '
        '60-day sample skewness of daily simple returns, cross-sectional z-score '
        'per date for long-short ranking. Top z-scores = most negatively-skewed '
        'names, which command a return premium over lottery-like positively-skewed '
        'names. Uses a 1-day return (one extra warmup bar over the 60-day window).'
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
    """Return inverse 60-day return-skewness cross-sectional z-score per stock."""
    close = panel['close']
    daily_ret = safe_div(close - close.shift(1), close.shift(1))
    skew = daily_ret.rolling(window=60, min_periods=60).skew()
    return _cross_sectional_zscore(-skew)
