# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最小价 30日
# 简要说明: ts_min(low, 30) / close，30日最低价与当前收盘价的比率。
# 典型用途: 衡量当前价格相对于30日最低点的位置，接近1表示接近近期低点。
# ============================================================
"""qlib158 MIN30: formula = \\mathrm{ts\\_min}(\\mathrm{low}, 30) / \\mathrm{close}."""
from __future__ import annotations

import pandas as pd
from src.factors.base import safe_div, ts_min

__alpha_meta__ = {
    'id': 'qlib158_min30',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_min}(\\\\mathrm{low}, 30) / \\\\mathrm{close}',
    'columns_required': ['low', 'close'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 MIN30 on the supplied OHLCV panel."""
    lo = panel['low']
    c = panel['close']
    return safe_div(ts_min(lo, 30), c)
