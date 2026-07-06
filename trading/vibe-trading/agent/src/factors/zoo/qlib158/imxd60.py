# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 极值跨度 60日
# 简要说明: (ts_argmax(high, 60) - ts_argmin(low, 60)) / 60，最高与最低出现位置的时间差。
# 典型用途: 衡量60日内从最低点到最高点所需的时间，反映趋势持续性。
# ============================================================
"""qlib158 IMXD60: formula = (\\mathrm{ts\\_argmax}(\\mathrm{high}, 60) - \\mathrm{ts\\_argmin}(\\mathrm{low}, 60)) / 60."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_argmax, ts_argmin

__alpha_meta__ = {
    'id': 'qlib158_imxd60',
    'theme': ['momentum'],
    'formula_latex': '(\\\\mathrm{ts\\\\_argmax}(\\\\mathrm{high}, 60) - \\\\mathrm{ts\\\\_argmin}(\\\\mathrm{low}, 60)) / 60',
    'columns_required': ['high', 'low'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 60,
    'min_warmup_bars': 60,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMXD60 on the supplied OHLCV panel."""
    h = panel['high']
    lo = panel['low']
    return (ts_argmax(h, 60) - ts_argmin(lo, 60)) / float(60)
