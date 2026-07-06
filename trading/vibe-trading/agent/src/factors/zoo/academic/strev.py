
# ============================================================
# 中文名称: 短期反转因子 (STREV)
# 简要说明: 做多过去一个月输家、做空过去一个月赢家的收益。短期(月度)价格存在反转效应。
# 典型用途: 捕获一个月尺度的均值回复，用于短期反转策略。
# ============================================================
"""academic short-term reversal: inverse trailing 21-day return.

Reference:
    Jegadeesh, N. (1990). "Evidence of predictable behavior of security
    returns." The Journal of Finance, 45(3), 881-898.

The canonical one-month reversal factor: stocks with low past-month returns
tend to outperform stocks with high past-month returns over the following
month. Computed directly from prices as the negative of the trailing 21-day
return, then cross-sectional z-scored per date. Higher z-scores = larger
recent losers (the long leg).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import delta, safe_div

__alpha_meta__ = {
    'id': 'academic_strev',
    'nickname': 'Jegadeesh 1990 short-term reversal — inverse 21d return',
    'theme': ['reversal'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(-(\mathrm{close}_t - \mathrm{close}_{t-21}) / \mathrm{close}_{t-21}\bigr)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 21,
    'min_warmup_bars': 21,
    'notes': (
        'Jegadeesh (1990) one-month reversal. Negative trailing 21-day return, '
        'cross-sectional z-score per date for long-short ranking. Top z-scores = '
        'recent one-month losers, which tend to rebound. Constructed directly from '
        'prices, matching the original definition modulo the z-score wrapper.'
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
    """Return inverse 21-day return cross-sectional z-score per stock."""
    close = panel['close']
    ret = safe_div(delta(close, 21), close.shift(21))
    return _cross_sectional_zscore(-ret)
