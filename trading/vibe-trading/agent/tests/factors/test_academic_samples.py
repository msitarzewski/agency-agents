"""Golden-output regression for ``zoo/academic`` factors.

Generates the same seeded panel used to bake the golden CSVs in
``tests/factors/fixtures/goldens/academic_*.csv`` and asserts the live
``Registry.compute()`` output is numerically identical (``rtol=1e-6``,
NaNs treated as equal). Three representative factors are exercised here;
the remaining academic factors are covered by the AST purity gate plus
the registry health check.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.factors.registry import Registry

_GOLDEN_DIR = Path(__file__).parent / "fixtures" / "goldens"


def _build_panel() -> dict[str, pd.DataFrame]:
    """Recreate the exact seeded panel used to write the golden CSVs."""
    rng = np.random.RandomState(42)
    n_rows, n_cols = 300, 8
    codes = [f"C{i:02d}" for i in range(n_cols)]
    dates = pd.date_range("2024-01-01", periods=n_rows, freq="B")

    log_rets = rng.normal(0, 0.02, size=(n_rows, n_cols))
    close = pd.DataFrame(
        100 * np.exp(np.cumsum(log_rets, axis=0)), index=dates, columns=codes
    )
    high = close * (1 + np.abs(rng.normal(0, 0.005, size=(n_rows, n_cols))))
    low = close * (1 - np.abs(rng.normal(0, 0.005, size=(n_rows, n_cols))))
    open_ = close.shift(1).fillna(close.iloc[0])
    volume = pd.DataFrame(
        rng.uniform(1e5, 1e7, size=(n_rows, n_cols)), index=dates, columns=codes
    )
    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def _load_golden(alpha_id: str) -> pd.DataFrame:
    path = _GOLDEN_DIR / f"{alpha_id}.csv"
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df


@pytest.mark.parametrize(
    "alpha_id",
    ["academic_mkt_rf", "academic_smb", "academic_carhart_mom"],
)
def test_academic_factor_matches_golden(alpha_id: str) -> None:
    registry = Registry()
    panel = _build_panel()
    result = registry.compute(alpha_id, panel)
    golden = _load_golden(alpha_id)

    assert list(result.columns) == list(golden.columns), (
        f"{alpha_id}: column mismatch"
    )
    assert result.shape == golden.shape, f"{alpha_id}: shape mismatch"

    np.testing.assert_allclose(
        result.to_numpy(dtype=np.float64),
        golden.to_numpy(dtype=np.float64),
        rtol=1e-6,
        equal_nan=True,
        err_msg=f"{alpha_id} output diverged from golden",
    )
