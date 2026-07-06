
# ============================================================
# 中文名称: Kakushadze Alpha #71
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第71号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #71.

Formula (paper appendix): max(Ts_Rank(decay_linear(correlation(Ts_Rank(close,3), Ts_Rank(adv180,12), 18), 4), 16), Ts_Rank(decay_linear((rank((low+open)-(2*vwap))^2, 16), 4))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 71.
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

ALPHA_ID = "alpha101_071"

__alpha_meta__ = {
    'id': 'alpha101_071',
    'nickname': 'Kakushadze Alpha #71',
    'theme': ['volume', 'reversal'],
    'formula_latex': 'max(Ts_Rank(decay_linear(correlation(Ts_Rank(close,3), Ts_Rank(adv180,12), 18), 4), 16), Ts_Rank(decay_linear((rank((low+open)-(2*vwap))^2, 16), 4))',
    'columns_required': ['open', 'low', 'close', 'volume', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 226,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    open_ = panel["open"]
    low = panel["low"]
    volume = panel["volume"]
    vwap = panel["vwap"]
    adv180 = ts_mean(volume, 180)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    a = ts_rank(decay_linear(ts_corr(ts_rank(close, 3), ts_rank(adv180, 12), 18), 4), 16)
    inner = signed_power(rank((low + open_) - (vwap + vwap)), 2.0)
    b = ts_rank(decay_linear(inner, 16), 4)
    arr_a = a.to_numpy(dtype=np.float64, na_value=np.nan)
    arr_b = b.to_numpy(dtype=np.float64, na_value=np.nan)
    out = pd.DataFrame(np.fmax(arr_a, arr_b), index=close.index, columns=close.columns)
    return out
