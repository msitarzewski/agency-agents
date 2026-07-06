
# ============================================================
# 中文名称: GTJA #51 - 量价协方差排名
# 简要说明: (-1*RANK(CORR(HIGH,MEAN(VOLUME,20),5))*RANK(CORR(CLOSE,MEAN(VOLUME,50),1)))，两种量价相关的排名乘积取负。
# 典型用途: 不同时间尺度量价关系的综合反转信号。
# ============================================================
"""GTJA Alpha #51.

Formula: SUM(up_move,12)/(SUM(up_move,12)+SUM(dn_move,12))
Source: 国泰君安 191 alpha 研报 (2014), alpha 51."""

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
    "id": "gtja191_051",
    "theme": ['reversal'],
    "formula_latex": 'SUM(up_move,12)/(SUM(up_move,12)+SUM(dn_move,12))',
    "columns_required": ['high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 12,
    "min_warmup_bars": 13,
    "notes": 'Up-range share over 12 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    h = panel["high"]
    l = panel["low"]
    hl = h + l
    phl = h.shift(1) + l.shift(1)
    move = pd.DataFrame(
        np.maximum(np.abs(h.to_numpy() - h.shift(1).to_numpy()),
                   np.abs(l.to_numpy() - l.shift(1).to_numpy())),
        index=h.index, columns=h.columns,
    )
    up = move.where(hl > phl, 0.0)
    dn = move.where(hl < phl, 0.0)
    s_up = up.rolling(12, min_periods=12).sum()
    s_dn = dn.rolling(12, min_periods=12).sum()
    return safe_div(s_up, s_up + s_dn)
