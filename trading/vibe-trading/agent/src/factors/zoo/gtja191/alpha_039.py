
# ============================================================
# 中文名称: GTJA #39 - 量价反转排名
# 简要说明: (-1*RANK(CORR(RANK(HIGH),RANK(VOLUME),7)) * RANK(CORR(RANK(LOW),RANK(VOLUME),7)))，高低价与成交量秩相关的乘积取负排名。
# 典型用途: 综合上下两端量价关系的反转信号。
# ============================================================
"""GTJA Alpha #39.

Formula: ((RANK(DECAYLINEAR(DELTA(CLOSE,2),8)) - RANK(DECAYLINEAR(CORR(((VWAP*0.3)+(OPEN*0.7)),SUM(MEAN(VOLUME,180),37),14),12)))*-1)
Source: 国泰君安 191 alpha 研报 (2014), alpha 39."""

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
    "id": "gtja191_039",
    "theme": ['volume'],
    "formula_latex": '((RANK(DECAYLINEAR(DELTA(CLOSE,2),8)) - RANK(DECAYLINEAR(CORR(((VWAP*0.3)+(OPEN*0.7)),SUM(MEAN(VOLUME,180),37),14),12)))*-1)',
    "columns_required": ['close', 'open', 'volume', 'amount'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 14,
    "min_warmup_bars": 63,
    "notes": '180d / 37d windows approximated with 30d / 10d. See notes.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    o = panel["open"]
    v = panel["volume"]
    vw = safe_div(panel["amount"], v * 100.0 + 1.0)
    p1 = rank(decay_linear(delta(c, 2), 8))
    blend = vw * 0.3 + o * 0.7
    vmean = ts_mean(v, 30).rolling(10, min_periods=10).sum()
    p2 = rank(decay_linear(ts_corr(blend, vmean, 14), 12))
    return -1.0 * (p1 - p2)
