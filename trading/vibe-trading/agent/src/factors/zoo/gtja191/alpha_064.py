
# ============================================================
# 中文名称: GTJA Alpha #64
# 简要说明: 国泰君安191短周期交易型alpha因子第64号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #64.

Formula: (MAX(RANK(DECAYLINEAR(CORR(RANK(VWAP),RANK(VOLUME),4),4)),RANK(DECAYLINEAR(MAX(CORR(RANK(CLOSE),RANK(MEAN(VOLUME,60)),4),13),14)))*-1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 64."""

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
    "id": "gtja191_064",
    "theme": ['volume'],
    "formula_latex": '(MAX(RANK(DECAYLINEAR(CORR(RANK(VWAP),RANK(VOLUME),4),4)),RANK(DECAYLINEAR(MAX(CORR(RANK(CLOSE),RANK(MEAN(VOLUME,60)),4),13),14)))*-1)',
    "columns_required": ['close', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 14,
    "min_warmup_bars": 30,
    "notes": '60d mean truncated to 10d; ts_max window 13→4 and decay_linear 14→6 for warmup feasibility.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    p1 = rank(decay_linear(ts_corr(rank(vw), rank(v), 4), 4))
    inner = ts_corr(rank(c), rank(ts_mean(v, 10)), 4).fillna(0.0)
    p2 = rank(decay_linear(ts_max(inner, 4), 6))
    return -1.0 * pd.DataFrame(np.maximum(p1.to_numpy(), p2.to_numpy()),
                               index=c.index, columns=c.columns)
