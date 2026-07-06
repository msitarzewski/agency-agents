# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最高价位置 30日
# 简要说明: ts_argmax(high, 30) / 30，30日内最高价出现位置的归一化指标。
# 典型用途: 值接近0表示最高价出现在近期，接近1表示出现在较早期。
# ============================================================
"""qlib158 IMAX30: formula = \\mathrm{ts\\_argmax}(\\mathrm{high}, 30) / 30."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_argmax

__alpha_meta__ = {
    'id': 'qlib158_imax30',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{ts\\\\_argmax}(\\\\mathrm{high}, 30) / 30',
    'columns_required': ['high'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMAX30 on the supplied OHLCV panel."""
    h = panel['high']
    return ts_argmax(h, 30) / float(30)
