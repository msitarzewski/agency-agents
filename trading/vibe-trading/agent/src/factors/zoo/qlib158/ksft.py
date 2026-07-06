# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: K线偏移(标准化开盘价)
# 简要说明: (2*close - high - low) / open，衡量收盘价偏离日内中心的程度。
# 典型用途: K线形态识别，正偏移表明收盘偏向高价位区间。
# ============================================================
"""qlib158 KSFT: formula = (2\\,\\mathrm{close} - \\mathrm{high} - \\mathrm{low}) / \\mathrm{open}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_ksft',
    'theme': ['microstructure'],
    'formula_latex': '(2\\\\,\\\\mathrm{close} - \\\\mathrm{high} - \\\\mathrm{low}) / \\\\mathrm{open}',
    'columns_required': ['open', 'high', 'low', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 1,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 KSFT on the supplied OHLCV panel."""
    o = panel['open']
    c = panel['close']
    h = panel['high']
    lo = panel['low']
    return safe_div(2.0 * c - h - lo, o)
