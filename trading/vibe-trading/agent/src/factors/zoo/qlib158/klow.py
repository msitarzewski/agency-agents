# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 下影线比率
# 简要说明: (min(open,close) - low) / open，衡量下影线长度相对于开盘价的比率。
# 典型用途: 反映日内买方支撑力度，下影线较长意味着低位有买盘承接。
# ============================================================
"""qlib158 KLOW: formula = (\\min(\\mathrm{open}, \\mathrm{close}) - \\mathrm{low}) / \\mathrm{open}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_klow',
    'theme': ['microstructure'],
    'formula_latex': '(\\\\min(\\\\mathrm{open}, \\\\mathrm{close}) - \\\\mathrm{low}) / \\\\mathrm{open}',
    'columns_required': ['open', 'low', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 1,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 KLOW on the supplied OHLCV panel."""
    o = panel['open']
    c = panel['close']
    lo = panel['low']
    lower = o.where(o <= c, c)
    return safe_div(lower - lo, o)
