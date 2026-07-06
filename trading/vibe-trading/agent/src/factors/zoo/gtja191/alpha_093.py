
# ============================================================
# 中文名称: GTJA Alpha #93
# 简要说明: 国泰君安191短周期交易型alpha因子第93号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #93.

Formula: SUM((OPEN>=DELAY(OPEN,1)?0:MAX(OPEN-LOW,OPEN-DELAY(OPEN,1))),20)
Source: 国泰君安 191 alpha 研报 (2014), alpha 93."""

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
    "id": "gtja191_093",
    "theme": ['microstructure'],
    "formula_latex": 'SUM((OPEN>=DELAY(OPEN,1)?0:MAX(OPEN-LOW,OPEN-DELAY(OPEN,1))),20)',
    "columns_required": ['open', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 22,
    "notes": 'Sum of downside range moves over 20 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    l = panel["low"]
    po = o.shift(1)
    move = pd.DataFrame(np.maximum((o - l).to_numpy(), (o - po).to_numpy()),
                        index=o.index, columns=o.columns)
    keep = move.where(o < po, 0.0)
    return keep.rolling(20, min_periods=20).sum()
