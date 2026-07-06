
# ============================================================
# 中文名称: GTJA #21 - 均线斜率
# 简要说明: REGBETA(MEAN(CLOSE,6), SEQUENCE(6))，6日均线的线性回归斜率。
# 典型用途: 短期趋势强度的度量，正斜率表示上涨趋势。
# ============================================================
"""GTJA Alpha #21.

Formula: REGBETA(MEAN(CLOSE,6), SEQUENCE(6))
Source: 国泰君安 191 alpha 研报 (2014), alpha 21."""

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
    "id": "gtja191_021",
    "theme": ['momentum'],
    "formula_latex": 'REGBETA(MEAN(CLOSE,6), SEQUENCE(6))',
    "columns_required": ['close'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 12,
    "notes": 'Rolling 6-day slope of MA6(close) vs time index. REGBETA proxied by ts_cov / ts_std**2.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    ma6 = ts_mean(c, 6)
    # build a sequence DataFrame: 1..N broadcast on every column
    seq = pd.DataFrame(
        np.broadcast_to(np.arange(1, c.shape[0] + 1, dtype=float)[:, None], c.shape).copy(),
        index=c.index, columns=c.columns,
    )
    return safe_div(ts_cov(ma6, seq, 6), ts_std(seq, 6) ** 2)
