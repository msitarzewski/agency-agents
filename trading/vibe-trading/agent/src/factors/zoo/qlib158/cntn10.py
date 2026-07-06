# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 下跌天数计数 10日
# 简要说明: rolling_mean(1[close<close_prev], 10)，10日内下跌天数占比。
# 典型用途: 衡量10日内下跌频率，值高表示持续下跌行情。
# ============================================================
"""qlib158 CNTN10: formula = \\mathrm{rolling\\_mean}(\\mathrm{1}[\\mathrm{close}<\\mathrm{close}_{{-1}}], 10)."""
from __future__ import annotations

import pandas as pd

__alpha_meta__ = {
    'id': 'qlib158_cntn10',
    'theme': ['reversal'],
    'formula_latex': '\\\\mathrm{rolling\\\\_mean}(\\\\mathrm{1}[\\\\mathrm{close}<\\\\mathrm{close}_{{-1}}], 10)',
    'columns_required': ['close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 10,
    'min_warmup_bars': 10,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 CNTN10 on the supplied OHLCV panel."""
    c = panel['close']
    dn = (c < c.shift(1)).astype('float64')
    return dn.rolling(window=10, min_periods=10).mean()
