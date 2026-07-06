from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


_AGENT_ROOT = Path(__file__).resolve().parents[1]


def _load_example_module():
    path = _AGENT_ROOT / "src" / "skills" / "fundamental-filter" / "example_signal_engine.py"
    spec = importlib.util.spec_from_file_location("fundamental_filter_example", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_example_signal_engine_uses_statement_fundamental_columns() -> None:
    module = _load_example_module()
    dates = pd.bdate_range("2024-05-06", periods=3)

    good = pd.DataFrame(
        {
            "open": [10.0, 10.1, 10.2],
            "high": [10.5, 10.6, 10.7],
            "low": [9.8, 9.9, 10.0],
            "close": [10.2, 10.3, 10.4],
            "volume": [1000, 1100, 1200],
            "income_total_revenue": [500.0, 500.0, 500.0],
            "income_n_income": [50.0, 50.0, 50.0],
            "balancesheet_total_hldr_eqy_exc_min_int": [300.0, 300.0, 300.0],
            "fina_indicator_roe": [12.0, 12.0, 12.0],
        },
        index=dates,
    )
    weak = good.copy()
    weak["income_n_income"] = [-10.0, -10.0, -10.0]

    engine = module.SignalEngine(roe_min=8.0)
    signals = engine.generate({"000001.SZ": good, "600000.SH": weak})

    assert signals["000001.SZ"].tolist() == [1.0, 1.0, 1.0]
    assert signals["600000.SH"].tolist() == [0.0, 0.0, 0.0]
