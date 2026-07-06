
# ============================================================
# 中文名称: GTJA #14 - 上涨动能
# 简要说明: ((-1*rank(delta(returns, 3))) * rank(covariance(rank(close), rank(volume), 5)))，收益变化与量价协方差的组合。
# 典型用途: 收益减速且量价背离时的反转组合信号。
# ============================================================
"""GTJA Alpha #14.

Formula: CLOSE - DELAY(CLOSE,5)
Source: 国泰君安 191 alpha 研报 (2014), alpha 14."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
    decay_linear,
    delta,
    rank,
    safe_div,
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

__alpha_meta__ = {
    "id": "gtja191_014",
    "theme": ['momentum'],
    "formula_latex": 'CLOSE - DELAY(CLOSE,5)',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 6,
    "notes": 'Simple 5d momentum = delta(close, 5).',
}

def compute(panel: dict) -> pd.DataFrame:
    return delta(panel["close"], 5)
