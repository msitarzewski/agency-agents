
# ============================================================
# 中文名称: GTJA #48 - 量价极值
# 简要说明: (-1*RANK(CORR(RANK(HIGH),RANK(VOLUME),6))*RANK(CORR(RANK(LOW),RANK(VOLUME),6)))，高低价与成交量的双相关性排名。
# 典型用途: 上下两端量价关系的一致性或背离判断。
# ============================================================
"""GTJA Alpha #48.

Formula: -1*((RANK((SIGN((CLOSE-DELAY(CLOSE,1)))+SIGN((DELAY(CLOSE,1)-DELAY(CLOSE,2)))+SIGN((DELAY(CLOSE,2)-DELAY(CLOSE,3))))))*SUM(VOLUME,5))/SUM(VOLUME,20)
Source: 国泰君安 191 alpha 研报 (2014), alpha 48."""

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
    "id": "gtja191_048",
    "theme": ['volume', 'momentum'],
    "formula_latex": '-1*((RANK((SIGN((CLOSE-DELAY(CLOSE,1)))+SIGN((DELAY(CLOSE,1)-DELAY(CLOSE,2)))+SIGN((DELAY(CLOSE,2)-DELAY(CLOSE,3))))))*SUM(VOLUME,5))/SUM(VOLUME,20)',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 5,
    "min_warmup_bars": 21,
    "notes": 'Rank of 3d signed momentum sum times 5d/20d volume ratio, negated.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    s = np.sign(c - c.shift(1)) + np.sign(c.shift(1) - c.shift(2)) + np.sign(c.shift(2) - c.shift(3))
    s = pd.DataFrame(s, index=c.index, columns=c.columns)
    sv5 = v.rolling(5, min_periods=5).sum()
    sv20 = v.rolling(20, min_periods=20).sum()
    return -1.0 * rank(s) * safe_div(sv5, sv20)
