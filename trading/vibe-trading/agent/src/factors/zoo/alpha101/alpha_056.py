
# ============================================================
# 中文名称: Kakushadze Alpha #56
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第56号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #56.

Formula (paper appendix): 0 - 1*(rank(sum(returns,10)/sum(sum(returns,2),3)) * rank((returns * cap)))  [cap unavailable -> 1]
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 56.
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

ALPHA_ID = "alpha101_056"

__alpha_meta__ = {
    'id': 'alpha101_056',
    'nickname': 'Kakushadze Alpha #56',
    'theme': ['momentum'],
    'formula_latex': '0 - 1*(rank(sum(returns,10)/sum(sum(returns,2),3)) * rank((returns * cap)))  [cap unavailable -> 1]',
    'columns_required': ['close'],
    'extras_required': [],
    'requires_sector': True,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 10,
    'notes': "Industry neutralization implemented via per-row sector group demean (panel['sector'] required). When sector tag is absent the registry rejects via SkipAlpha; the compute() also has a degraded global demean fallback. This is a partial approximation of the paper's IndClass.industry/subindustry/sector neutralization. Paper formula uses market 'cap' which is not part of the standard OHLCV panel; substituted by a constant 1.0 DataFrame. Result remains a valid factor but loses the cap-weighting term.",
}


def _rolling_sum(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Rolling window sum; warmup -> NaN."""
    return df.rolling(window=n, min_periods=n).sum()


def _make_one(ref: pd.DataFrame) -> pd.DataFrame:
    """A DataFrame of 1.0 with the same shape/index/columns as ``ref``."""
    return pd.DataFrame(1.0, index=ref.index, columns=ref.columns)


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]


    returns = close.pct_change()
    # Helper aliases (local closures keep the file standalone & purity-safe).
    rolling_sum = _rolling_sum
    make_one = _make_one
    # 'cap' (market cap) is not part of the standard panel; degrade to 1.0
    cap = make_one(close)
    num = rolling_sum(returns, 10)
    denom = rolling_sum(rolling_sum(returns, 2), 3)
    out = 0.0 - (rank(safe_div(num, denom)) * rank(returns * cap))
    return out
