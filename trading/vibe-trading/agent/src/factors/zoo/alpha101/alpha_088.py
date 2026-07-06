
# ============================================================
# 中文名称: Kakushadze Alpha #88
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第88号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #88.

Formula (paper appendix): min(rank(decay_linear((rank(open)+rank(low))-(rank(high)+rank(close)),8)), Ts_Rank(decay_linear(correlation(Ts_Rank(close,8),Ts_Rank(adv60,20),8),7),3))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 88.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
    decay_linear,
    delta,
    rank,
    safe_div,
    scale,
    signed_power,
    ts_argmax,
    ts_argmin,
    ts_corr,
    ts_cov,
    ts_max,
    ts_mean,
    ts_min,
    ts_rank,
    ts_std,
)

ALPHA_ID = "alpha101_088"

__alpha_meta__ = {
    'id': 'alpha101_088',
    'nickname': 'Kakushadze Alpha #88',
    'theme': ['volume'],
    'formula_latex': 'min(rank(decay_linear((rank(open)+rank(low))-(rank(high)+rank(close)),8)), Ts_Rank(decay_linear(correlation(Ts_Rank(close,8),Ts_Rank(adv60,20),8),7),3))',
    'columns_required': ['open', 'high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 94,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    adv60 = ts_mean(volume, 60)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    a = rank(decay_linear((rank(open_) + rank(low)) - (rank(high) + rank(close)), 8))
    b = ts_rank(decay_linear(ts_corr(ts_rank(close, 8), ts_rank(adv60, 20), 8), 7), 3)
    arr_a = a.to_numpy(dtype=np.float64, na_value=np.nan)
    arr_b = b.to_numpy(dtype=np.float64, na_value=np.nan)
    out = pd.DataFrame(np.fmin(arr_a, arr_b), index=close.index, columns=close.columns)
    return out
