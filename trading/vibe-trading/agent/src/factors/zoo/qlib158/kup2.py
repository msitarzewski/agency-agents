# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 上影线相对比率
# 简要说明: (high - max(open,close)) / (high - low)，衡量上影线在整根K线中的占比。
# 典型用途: 用于识别冲高回落形态，上影线占比高表明上方阻力较大。
# ============================================================
"""qlib158 KUP2: formula = (\\mathrm{high} - \\max(\\mathrm{open}, \\mathrm{close})) / (\\mathrm{high} - \\mathrm{low})."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_kup2',
    'theme': ['microstructure'],
    'formula_latex': '(\\\\mathrm{high} - \\\\max(\\\\mathrm{open}, \\\\mathrm{close})) / (\\\\mathrm{high} - \\\\mathrm{low})',
    'columns_required': ['open', 'high', 'low', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 1,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 KUP2 on the supplied OHLCV panel."""
    o = panel['open']
    c = panel['close']
    h = panel['high']
    lo = panel['low']
    upper = o.where(o >= c, c)
    return safe_div(h - upper, h - lo)
