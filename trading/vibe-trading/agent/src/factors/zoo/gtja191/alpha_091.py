
# ============================================================
# 中文名称: GTJA Alpha #91
# 简要说明: 国泰君安191短周期交易型alpha因子第91号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #91.

Formula: ((-1*RANK((CLOSE-MAX(CLOSE,5))))*RANK(CORR(MEAN(VOLUME,40),LOW,5)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 91."""

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
    "id": "gtja191_091",
    "theme": ['volume', 'reversal'],
    "formula_latex": '((-1*RANK((CLOSE-MAX(CLOSE,5))))*RANK(CORR(MEAN(VOLUME,40),LOW,5)))',
    "columns_required": ['close', 'low', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 35,
    "notes": '40d mean truncated to 30d.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    l = panel["low"]
    v = panel["volume"]
    return -1.0 * rank(c - ts_max(c, 5)) * rank(ts_corr(ts_mean(v, 30), l, 5))
