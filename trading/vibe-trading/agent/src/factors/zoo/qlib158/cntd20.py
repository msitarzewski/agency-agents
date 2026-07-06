# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 涨跌天数差 20日
# 简要说明: CNTP_20 - CNTN_20，20日内上涨天数与下跌天数之差。
# 典型用途: 综合衡量20日内的涨跌方向，正值表示多头天数占优。
# ============================================================
"""qlib158 CNTD20: formula = \\mathrm{CNTP}_20 - \\mathrm{CNTN}_20."""
from __future__ import annotations

import pandas as pd

__alpha_meta__ = {
    'id': 'qlib158_cntd20',
    'theme': ['reversal'],
    'formula_latex': '\\\\mathrm{CNTP}_20 - \\\\mathrm{CNTN}_20',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 CNTD20 on the supplied OHLCV panel."""
    c = panel['close']
    up = (c > c.shift(1)).astype('float64')
    dn = (c < c.shift(1)).astype('float64')
    up_w = up.rolling(window=20, min_periods=20).mean()
    dn_w = dn.rolling(window=20, min_periods=20).mean()
    return up_w - dn_w
