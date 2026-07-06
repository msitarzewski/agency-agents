
# ============================================================
# 中文名称: Amihud非流动性因子 (ILLIQ)
# 简要说明: 单位成交额带来的价格冲击越大，流动性越差，预期收益越高(流动性溢价)。Amihud(2002)。
# 典型用途: 捕获非流动性溢价，做多流动性差的股票，用于流动性风格分析。
# ============================================================
"""academic Amihud illiquidity: average absolute return per dollar of volume.

Reference:
    Amihud, Y. (2002). "Illiquidity and stock returns: cross-section and
    time-series effects." Journal of Financial Markets, 5(1), 31-56.

The Amihud (2002) ILLIQ measure: the daily ratio of absolute return to dollar
volume, averaged over a trailing window, captures the price impact of trading.
Illiquid stocks (high ILLIQ) command a return premium. Computed over a 21-day
window then cross-sectional z-scored per date. Higher z-scores = less liquid
names (the long leg of the illiquidity premium).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import safe_div, ts_mean

__alpha_meta__ = {
    'id': 'academic_illiq',
    'nickname': 'Amihud 2002 illiquidity — |return| per dollar volume',
    'theme': ['liquidity'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(\mathrm{ts\_mean}(|r_t| / (\mathrm{close}_t \cdot \mathrm{volume}_t),\,21)\bigr)',
    'columns_required': ['close', 'volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 21,
    'min_warmup_bars': 22,
    'notes': (
        'Amihud (2002) ILLIQ. Daily |simple return| divided by dollar volume '
        '(close * volume), averaged over a trailing 21-day window, then '
        'cross-sectional z-score per date for long-short ranking. Top z-scores = '
        'least liquid names, which carry the illiquidity premium. Uses a 1-day '
        'return (one extra warmup bar over the 21-day average window).'
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
    """Return 21-day Amihud illiquidity cross-sectional z-score per stock."""
    close = panel['close']
    volume = panel['volume']
    daily_ret = safe_div(close - close.shift(1), close.shift(1))
    dollar_volume = close * volume
    illiq = safe_div(daily_ret.abs(), dollar_volume)
    return _cross_sectional_zscore(ts_mean(illiq, 21))
