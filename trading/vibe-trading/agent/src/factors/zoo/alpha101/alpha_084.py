
# ============================================================
# 中文名称: Kakushadze Alpha #84
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第84号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #84.

Formula (paper appendix): SignedPower(Ts_Rank(vwap-ts_max(vwap,15), 21), delta(close,5))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 84.
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

ALPHA_ID = "alpha101_084"

__alpha_meta__ = {
    'id': 'alpha101_084',
    'nickname': 'Kakushadze Alpha #84',
    'theme': ['momentum'],
    'formula_latex': 'SignedPower(Ts_Rank(vwap-ts_max(vwap,15), 21), delta(close,5))',
    'columns_required': ['close', 'vwap'],
    'extras_required': [],
    'requires_sector': False,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 35,
    'notes': "SignedPower with a delta(close,5) exponent can produce non-finite values when the exponent is large; non-finite outputs are clipped to NaN to satisfy the registry's no-inf invariant.",
}


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    vwap = panel["vwap"]


    # Helper aliases (local closures keep the file standalone & purity-safe).
    base = ts_rank(vwap - ts_max(vwap, 15), 21)
    exponent_df = delta(close, 5)
    base_arr = base.to_numpy(dtype=np.float64, na_value=np.nan)
    exp_arr = exponent_df.to_numpy(dtype=np.float64, na_value=np.nan)
    out_arr = np.sign(base_arr) * np.power(np.abs(base_arr), exp_arr)
    out_arr = np.where(np.isfinite(out_arr), out_arr, np.nan)
    out = pd.DataFrame(out_arr, index=close.index, columns=close.columns)
    return out
