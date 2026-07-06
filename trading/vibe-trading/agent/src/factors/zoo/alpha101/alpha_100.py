
# ============================================================
# 中文名称: Kakushadze Alpha #100
# 简要说明: Kakushadze (2015) 101 Formulaic Alphas 中的第100号因子，详见公式定义。
# 典型用途: 作为多因子模型中的alpha信号，经中性化处理后用于选股或股指期货交易。
# ============================================================
"""Kakushadze Alpha #100.

Formula (paper appendix): 0 - 1*((1.5*scale(IN(IN(rank(((close-low)-(high-close))/(high-low)*volume), subind), subind)) - scale(IN(correlation(close, rank(adv20), 5) - rank(ts_argmin(close,30)), subind))) * (volume/adv20))
Source: Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991, eq. 100.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import (
    decay_linear,
    delta,
    rank,
    safe_div,
    scale,
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

ALPHA_ID = "alpha101_100"

__alpha_meta__ = {
    'id': 'alpha101_100',
    'nickname': 'Kakushadze Alpha #100',
    'theme': ['volume', 'momentum'],
    'formula_latex': '0 - 1*((1.5*scale(IN(IN(rank(((close-low)-(high-close))/(high-low)*volume), subind), subind)) - scale(IN(correlation(close, rank(adv20), 5) - rank(ts_argmin(close,30)), subind))) * (volume/adv20))',
    'columns_required': ['high', 'low', 'close', 'volume'],
    'extras_required': [],
    'requires_sector': True,
    'universe': ['equity_us'],
    'frequency': ['1D'],
    'decay_horizon': 5,
    'min_warmup_bars': 30,
    'notes': "Industry neutralization implemented via per-row sector group demean (panel['sector'] required). When sector tag is absent the registry rejects via SkipAlpha; the compute() also has a degraded global demean fallback. This is a partial approximation of the paper's IndClass.industry/subindustry/sector neutralization.",
}


def _ind_neutralize(x: pd.DataFrame, panel: dict) -> pd.DataFrame:
    """Industry/sector neutralize: subtract the row-wise sector group mean.

    If panel has a 'sector' DataFrame (same shape as close), subtract the
    per-sector cross-sectional mean per row. If absent, degrade to global
    cross-sectional demean (subtract row mean). This is a degraded fallback
    relative to the paper's industry/subindustry neutralization; see notes.
    """
    sector_df = panel.get("sector")
    if sector_df is None:
        row_mean = x.mean(axis=1, skipna=True)
        return x.sub(row_mean, axis=0)
    # Per-row group demean. Iterate rows; numpy-fast enough for small panels.
    arr = x.to_numpy(dtype=np.float64, na_value=np.nan).copy()
    sec_arr = sector_df.to_numpy()
    n_rows = arr.shape[0]
    for i in range(n_rows):
        row = arr[i]
        sec_row = sec_arr[i]
        for tag in pd.unique(sec_row):
            mask = sec_row == tag
            vals = row[mask]
            finite = vals[~np.isnan(vals)]
            if finite.size == 0:
                continue
            mean = finite.mean()
            row[mask] = vals - mean
        arr[i] = row
    return pd.DataFrame(arr, index=x.index, columns=x.columns)


def compute(panel: dict) -> pd.DataFrame:
    """Compute the alpha on the OHLCV+ panel and return a wide DataFrame."""
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]
    volume = panel["volume"]
    adv20 = ts_mean(volume, 20)

    # Helper aliases (local closures keep the file standalone & purity-safe).
    ind_neutralize = _ind_neutralize
    money_flow = safe_div(((close - low) - (high - close)), (high - low)) * volume
    t1 = 1.5 * scale(ind_neutralize(ind_neutralize(rank(money_flow), panel), panel))
    t2 = scale(ind_neutralize(ts_corr(close, rank(adv20), 5) - rank(ts_argmin(close, 30)), panel))
    out = 0.0 - ((t1 - t2) * safe_div(volume, adv20))
    return out
