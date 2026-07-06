
# ============================================================
# 中文名称: GTJA #4 - 条件止损信号
# 简要说明: (-1 * Ts_Rank(rank(low), 9))，最低价9日时间序列排名取负。
# 典型用途: 价格持续创近期新低时发出超卖信号。
# ============================================================
"""GTJA Alpha #4.

Formula: ((((SUM(CLOSE,8)/8)+STD(CLOSE,8))<(SUM(CLOSE,2)/2))?(-1):((SUM(CLOSE,2)/2<(SUM(CLOSE,8)/8-STD(CLOSE,8)))?1:((1<(VOLUME/MEAN(VOLUME,20)))?1:(-1))))
Source: 国泰君安 191 alpha 研报 (2014), alpha 4."""

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
    "id": "gtja191_004",
    "theme": ['momentum', 'volume'],
    "formula_latex": '((((SUM(CLOSE,8)/8)+STD(CLOSE,8))<(SUM(CLOSE,2)/2))?(-1):((SUM(CLOSE,2)/2<(SUM(CLOSE,8)/8-STD(CLOSE,8)))?1:((1<(VOLUME/MEAN(VOLUME,20)))?1:(-1))))',
    "columns_required": ['close', 'volume'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 8,
    "min_warmup_bars": 20,
    "notes": 'Breakout signal: short-MA vs long-MA +/- 1 std, volume-relative tiebreaker. Output in {-1, +1}.',
}

def compute(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    v = panel["volume"]
    ma8 = ts_mean(c, 8)
    ma2 = ts_mean(c, 2)
    sd8 = ts_std(c, 8)
    vmean20 = ts_mean(v, 20)
    upper = ma8 + sd8
    lower = ma8 - sd8
    cond_top = upper < ma2
    cond_bot = ma2 < lower
    vol_strong = (v / vmean20) > 1.0
    res = np.where(cond_top, -1.0,
                   np.where(cond_bot, 1.0,
                            np.where(vol_strong, 1.0, -1.0)))
    return pd.DataFrame(res, index=c.index, columns=c.columns).astype(float)
