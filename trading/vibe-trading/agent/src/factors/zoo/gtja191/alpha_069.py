
# ============================================================
# 中文名称: GTJA Alpha #69
# 简要说明: 国泰君安191短周期交易型alpha因子第69号，详见公式定义。
# 典型用途: 在A股市场经中性化处理后用于选股或股指期货日内交易。
# ============================================================
"""GTJA Alpha #69.

Formula: (SUM(DTM,20)>SUM(DBM,20)?(SUM(DTM,20)-SUM(DBM,20))/SUM(DTM,20):(SUM(DTM,20)=SUM(DBM,20)?0:(SUM(DTM,20)-SUM(DBM,20))/SUM(DBM,20)))
Source: 国泰君安 191 alpha 研报 (2014), alpha 69."""

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
    "id": "gtja191_069",
    "theme": ['microstructure'],
    "formula_latex": '(SUM(DTM,20)>SUM(DBM,20)?(SUM(DTM,20)-SUM(DBM,20))/SUM(DTM,20):(SUM(DTM,20)=SUM(DBM,20)?0:(SUM(DTM,20)-SUM(DBM,20))/SUM(DBM,20)))',
    "columns_required": ['open', 'high', 'low'],
    "extras_required": [],
    "requires_sector": False,
    "universe": ["equity_cn"],
    "frequency": ["1d"],
    "decay_horizon": 20,
    "min_warmup_bars": 22,
    "notes": 'DTM/DBM as in GTJA spec.',
}

def compute(panel: dict) -> pd.DataFrame:
    o = panel["open"]
    h = panel["high"]
    l = panel["low"]
    po = o.shift(1)
    dtm = pd.DataFrame(np.where(o <= po, 0.0,
                                np.maximum((h - o).to_numpy(), (o - po).to_numpy())),
                       index=o.index, columns=o.columns)
    dbm = pd.DataFrame(np.where(o >= po, 0.0,
                                np.maximum((o - l).to_numpy(), (o - po).to_numpy())),
                       index=o.index, columns=o.columns)
    sd = dtm.rolling(20, min_periods=20).sum()
    sb = dbm.rolling(20, min_periods=20).sum()
    res = pd.DataFrame(np.where(sd > sb, (safe_div(sd - sb, sd)).to_numpy(),
                                np.where(sd < sb, (safe_div(sd - sb, sb)).to_numpy(), 0.0)),
                       index=o.index, columns=o.columns)
    return res
