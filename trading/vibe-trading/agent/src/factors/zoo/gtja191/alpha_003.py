
# ============================================================
# 中文名称: GTJA #3 - 条件量价反转
# 简要说明: (-1 * CORR(RANK(OPEN), RANK(VOLUME), 10))，开盘价与成交量秩相关的负值。
# 典型用途: 开盘量价关系异常识别，用于日内反转交易。
# ============================================================
"""GTJA Alpha #3.

Formula: SUM((CLOSE=DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),6)
Source: 国泰君安 191 alpha 研报 (2014), alpha 3."""

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
    "id": "gtja191_003",
    "theme": ['momentum'],
    "formula_latex": 'SUM((CLOSE=DELAY(CLOSE,1)?0:CLOSE-(CLOSE>DELAY(CLOSE,1)?MIN(LOW,DELAY(CLOSE,1)):MAX(HIGH,DELAY(CLOSE,1)))),6)',
    "columns_required": ['close', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 6,
    "min_warmup_bars": 7,
    "notes": 'Wilder-style accumulation of signed daily moves over 6 days.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    h = panel["high"]
    l = panel["low"]
    pc = c.shift(1)
    up = c > pc
    dn = c < pc
    ref = pd.DataFrame(np.where(up, np.minimum(l, pc), np.where(dn, np.maximum(h, pc), c)),
                       index=c.index, columns=c.columns)
    move = (c - ref).where(up | dn, 0.0)
    return move.rolling(6, min_periods=6).sum()
