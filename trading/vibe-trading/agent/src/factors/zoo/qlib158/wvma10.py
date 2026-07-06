# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 成交量加权波动 10日
# 简要说明: ts_std(ret*v, 10) / ts_mean(|ret|*v, 10)，成交量加权的价格波动归一化指标。
# 典型用途: 衡量成交量调整后的价格波动性，值越高表示相对于成交量的价格波动越大。
# ============================================================
"""qlib158 WVMA10: formula = \\mathrm{ts\\_std}(\\mathrm{ret}\\cdot v, 10) / \\mathrm{ts\\_mean}(|\\mathrm{ret}|\\cdot v, 10)."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_mean, ts_std

__alpha_meta__ = {
    'id': 'qlib158_wvma10',
    'theme': ['volume', 'volatility'],
    'formula_latex': '\\\\mathrm{ts\\\\_std}(\\\\mathrm{ret}\\\\cdot v, 10) / \\\\mathrm{ts\\\\_mean}(|\\\\mathrm{ret}|\\\\cdot v, 10)',
    'columns_required': ['close', 'volume'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 10,
    'min_warmup_bars': 10,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 WVMA10 on the supplied OHLCV panel."""
    c = panel['close']
    v = panel['volume']
    ret = safe_div(c, c.shift(1)) - 1.0
    rv = ret * v
    arv = ret.abs() * v
    return safe_div(ts_std(rv, 10), ts_mean(arv, 10))
