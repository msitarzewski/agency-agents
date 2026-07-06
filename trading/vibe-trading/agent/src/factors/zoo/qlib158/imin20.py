# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最低价位置 20日
# 简要说明: ts_argmin(low, 20) / 20，20日内最低价出现位置的归一化指标。
# 典型用途: 值接近0表示最低价出现在近期，接近1表示出现在较早期。
# ============================================================
"""qlib158 IMIN20: formula = \\mathrm{ts\\_argmin}(\\mathrm{low}, 20) / 20."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_argmin

__alpha_meta__ = {
    'id': 'qlib158_imin20',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_argmin}(\\\\mathrm{low}, 20) / 20',
    'columns_required': ['low'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMIN20 on the supplied OHLCV panel."""
    lo = panel['low']
    return ts_argmin(lo, 20) / float(20)
