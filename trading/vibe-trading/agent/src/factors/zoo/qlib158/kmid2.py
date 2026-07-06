# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: K线中部相对位置
# 简要说明: (close - open) / (high - low)，收盘价在当日振幅中的相对位置。
# 典型用途: 衡量收盘强度，值接近1表示收盘接近最高点，多方主导。
# ============================================================
"""qlib158 KMID2: formula = (\\mathrm{close} - \\mathrm{open}) / (\\mathrm{high} - \\mathrm{low})."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_kmid2',
    'theme': ['microstructure'],
    'formula_latex': '(\\\\mathrm{close} - \\\\mathrm{open}) / (\\\\mathrm{high} - \\\\mathrm{low})',
    'columns_required': ['open', 'high', 'low', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 1,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 KMID2 on the supplied OHLCV panel."""
    o = panel['open']
    c = panel['close']
    h = panel['high']
    lo = panel['low']
    return safe_div(c - o, h - lo)
