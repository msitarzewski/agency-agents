"""Numerical regression for sampled GTJA Alpha 1-100 modules.

Five alphas (1, 5, 17, 42, 80) cover the operator surface — log/rank/corr,
ts_rank composition, signed_power, rolling std, and pure volume change —
so a regression here catches most operator-mapping mistakes. The seeded
panel and golden CSVs are reproducible via the docstring of the conftest.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.factors.registry import Registry


GOLDENS_DIR = Path(__file__).resolve().parent / "fixtures" / "goldens"

SAMPLED_IDS = ("gtja191_001", "gtja191_005", "gtja191_017", "gtja191_042", "gtja191_080")


def _seeded_panel() -> dict[str, pd.DataFrame]:
    """Same seeded panel used to generate the goldens (np.random.RandomState(42)).

    30 rows × 5 codes; A-share convention amount = volume * close * 100.
    """
    rng = np.random.RandomState(42)
    n_rows = 30
    codes = ["A", "B", "C", "D", "E"]
    idx = pd.date_range("2024-01-01", periods=n_rows, freq="D")

    close_arr = 100.0 + np.cumsum(rng.normal(0, 1, (n_rows, 5)), axis=0)
    close_arr = np.abs(close_arr) + 1.0
    close = pd.DataFrame(close_arr, index=idx, columns=codes)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.DataFrame(
        np.maximum(close.to_numpy(), open_.to_numpy()) + rng.uniform(0, 1, (n_rows, 5)),
        index=idx, columns=codes,
    )
    low = pd.DataFrame(
        np.minimum(close.to_numpy(), open_.to_numpy()) - rng.uniform(0, 1, (n_rows, 5)),
        index=idx, columns=codes,
    ).abs() + 0.01
    volume = pd.DataFrame(
        rng.randint(1000, 100000, (n_rows, 5)).astype(float),
        index=idx, columns=codes,
    )
    amount = volume * close * 100.0
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume, "amount": amount}


@pytest.mark.parametrize("alpha_id", SAMPLED_IDS)
def test_gtja191_sample_matches_golden(alpha_id: str) -> None:
    """Recompute the sampled alpha and check it matches the committed golden CSV."""
    golden_path = GOLDENS_DIR / f"{alpha_id}.csv"
    assert golden_path.is_file(), f"missing golden fixture: {golden_path}"

    expected = pd.read_csv(golden_path, index_col=0, parse_dates=True)
    expected.index.freq = None

    registry = Registry()
    actual = registry.compute(alpha_id, _seeded_panel())

    # CSV round-trip may not preserve exact float bits; we still want a tight
    # tolerance so any operator-mapping regression is caught.
    np.testing.assert_allclose(
        actual.to_numpy(dtype=np.float64),
        expected.to_numpy(dtype=np.float64),
        rtol=1e-6,
        equal_nan=True,
        err_msg=f"{alpha_id}: numerical regression vs golden",
    )
