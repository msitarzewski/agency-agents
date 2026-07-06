# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最低价位置 5日
# 简要说明: ts_argmin(low, 5) / 5，5日内最低价出现位置的归一化指标。
# 典型用途: 值接近0表示最低价出现在近期，接近1表示出现在较早期。
# ============================================================
"""qlib158 IMIN5: formula = \\mathrm{ts\\_argmin}(\\mathrm{low}, 5) / 5."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_argmin

__alpha_meta__ = {
    'id': 'qlib158_imin5',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_argmin}(\\\\mathrm{low}, 5) / 5',
    'columns_required': ['low'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 5,
    'min_warmup_bars': 5,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMIN5 on the supplied OHLCV panel."""
    lo = panel['low']
    return ts_argmin(lo, 5) / float(5)
