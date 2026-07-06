
# ============================================================
# 中文名称: GTJA Alpha #77
# 简要说明: 国泰君安191短周期交易型alpha因子第77号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #77.

Formula: MIN(RANK(DECAYLINEAR(((HIGH+LOW)/2+HIGH-(VWAP+HIGH)),20)),RANK(DECAYLINEAR(CORR(((HIGH+LOW)/2),MEAN(VOLUME,40),3),6)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 77."""

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
    "id": "gtja191_077",
    "theme": ['volume'],
    "formula_latex": 'MIN(RANK(DECAYLINEAR(((HIGH+LOW)/2+HIGH-(VWAP+HIGH)),20)),RANK(DECAYLINEAR(CORR(((HIGH+LOW)/2),MEAN(VOLUME,40),3),6)))',
    "columns_required": ['high', 'low', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 37,
    "notes": '40d MA truncated to 30d.',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    l = panel["low"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    mid = (h + l) / 2.0
    p1 = rank(decay_linear(mid + h - (vw + h), 20))
    p2 = rank(decay_linear(ts_corr(mid, ts_mean(v, 30), 3), 6))
    return pd.DataFrame(np.minimum(p1.to_numpy(), p2.to_numpy()),
                        index=h.index, columns=h.columns)
