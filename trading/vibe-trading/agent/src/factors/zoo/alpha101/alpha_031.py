
# ============================================================
# 中文名称: Kakushadze Alpha #31
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第31号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #31.

Formula (paper appendix): rank(rank(rank(decay_linear(-1*rank(rank(delta(close,10))),10)))) + rank(-1*delta(close,3)) + sign(scale(correlation(adv20,low,12)))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 31.
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

ALPHA_ID = "alpha101_031"

__alpha_meta__ = {
    'id': 'alpha101_031',
    'nickname': 'Kakushadze Alpha #31',
    'theme': ['momentum'],
    'formula_latex': 'rank(rank(rank(decay_linear(-1*rank(rank(delta(close,10))),10)))) + rank(-1*delta(close,3)) + sign(scale(correlation(adv20,low,12)))',
    'columns_required': ['low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 25,
    'notes': '',
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    low = panel["low"]
    volume = panel["volume"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    t1 = rank(rank(rank(decay_linear(-1.0 * rank(rank(delta(close, 10))), 10))))
    t2 = rank(-1.0 * delta(close, 3))
    t3 = pd.DataFrame(np.sign(scale(ts_corr(adv20, low, 12)).to_numpy(dtype=np.float64, na_value=np.nan)), index=close.index, columns=close.columns)
    out = t1 + t2 + t3
    return out
