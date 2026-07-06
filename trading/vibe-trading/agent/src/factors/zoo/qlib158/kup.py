# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 上影线比率
# 简要说明: (high - max(open,close)) / open，衡量上影线长度相对于开盘价的比率。
# 典型用途: 反映日内卖出压力，上影线较长意味着高位有抛压。
# ============================================================
"""qlib158 KUP: formula = (\\mathrm{high} - \\max(\\mathrm{open}, \\mathrm{close})) / \\mathrm{open}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div

__alpha_meta__ = {
    'id': 'qlib158_kup',
    'theme': ['microstructure'],
    'formula_latex': '(\\\\mathrm{high} - \\\\max(\\\\mathrm{open}, \\\\mathrm{close})) / \\\\mathrm{open}',
    'columns_required': ['open', 'high', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 1,
    'min_warmup_bars': 1,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 KUP on the supplied OHLCV panel."""
    o = panel['open']
    c = panel['close']
    h = panel['high']
    upper = o.where(o >= c, c)
    return safe_div(h - upper, o)
