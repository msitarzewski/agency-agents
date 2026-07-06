
# ============================================================
# 中文名称: 52周高点因子 (HIGH52W)
# 简要说明: 当前价格越接近过去52周(252日)最高价，未来收益越高。George & Hwang(2004)的52周高点动量。
# 典型用途: 捕获基于52周高点锚定的动量效应，用于动量投资策略。
# ============================================================
"""academic 52-week-high momentum: closeness of price to its 252-day high.

Reference:
    George, T. J., & Hwang, C.-Y. (2004). "The 52-Week High and Momentum
    Investing." The Journal of Finance, 59(5), 2145-2176.

Stocks trading near their 52-week high tend to earn higher future returns —
the ratio of current price to the trailing 252-day high predicts momentum
better than past returns alone. Computed as close / ts_max(close, 252), then
cross-sectional z-scored per date. Higher z-scores = closer to the 52-week
high (the long leg).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import safe_div, ts_max

__alpha_meta__ = {
    'id': 'academic_high52w',
    'nickname': 'George-Hwang 2004 52-week-high momentum',
    'theme': ['momentum'],
    'formula_latex': r'\mathrm{zscore}_{x}\bigl(\mathrm{close}_t / \mathrm{ts\_max}(\mathrm{close},\,252)\bigr)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 252,
    'notes': (
        'George & Hwang (2004) 52-week-high momentum. Ratio of current close to the '
        'trailing 252-day maximum close, cross-sectional z-score per date for '
        'long-short ranking. Top z-scores = names trading nearest their 52-week high. '
        'Canonical 252d window; declared decay_horizon=60 due to registry schema cap '
        '(le=60); real signal horizon spans months.'
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
    """Return close-to-252d-high ratio cross-sectional z-score per stock."""
    close = panel['close']
    ratio = safe_div(close, ts_max(close, 252))
    return _cross_sectional_zscore(ratio)
