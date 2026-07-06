"""Golden-fixture regression tests for sampled qlib158 alphas.

We pin 5 alphas across the family taxonomy (K-bar, momentum, momentum-std,
volume-microstructure, volume-volatility) against CSV fixtures generated
from a fixed-seed panel. Any algebraic drift in the operators, in
``safe_div``, or in a per-family formula will break exactly one of the
parametrized cases — making the bisect surface as small as possible.

Panel construction matches the spec in the task brief:
    np.random.RandomState(42), 30 rows × 5 codes, OHLCV synthesised the
    same way as ``test_lookahead._baseline_panel`` (random walk close;
    open from shift; high/low bracketing; volume integer-cast).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.factors.registry import Registry


GOLDEN_DIR = Path(__file__).parent / "fixtures" / "goldens"


# ---------------------------------------------------------------- fixtures


def _build_panel(seed: int = 42, n_rows: int = 30, n_cols: int = 5) -> dict[str, pd.DataFrame]:
    """Deterministic panel matching the golden generation procedure."""
    rs = np.random.RandomState(seed)
    idx = pd.date_range("2024-01-01", periods=n_rows, freq="D")
    cols = [f"S{i}" for i in range(n_cols)]
    close = pd.DataFrame(
        100.0 + np.cumsum(rs.normal(0.0, 1.0, size=(n_rows, n_cols)), axis=0),
        index=idx, columns=cols,
    ).abs() + 1.0
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.DataFrame(
        np.maximum(close.to_numpy(), open_.to_numpy()) + rs.uniform(0.0, 1.0, size=(n_rows, n_cols)),
        index=idx, columns=cols,
    )
    low = pd.DataFrame(
        np.minimum(close.to_numpy(), open_.to_numpy()) - rs.uniform(0.0, 1.0, size=(n_rows, n_cols)),
        index=idx, columns=cols,
    ).abs() + 0.01
    volume = pd.DataFrame(
        rs.randint(1000, 100_000, size=(n_rows, n_cols)).astype(float),
        index=idx, columns=cols,
    )
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume}


@pytest.fixture(scope="module")
def panel() -> dict[str, pd.DataFrame]:
    return _build_panel()


@pytest.fixture(scope="module")
def registry() -> Registry:
    return Registry()


# ---------------------------------------------------------------- cases


SAMPLED_ALPHAS = [
    "qlib158_kmid",      # K-bar microstructure
    "qlib158_ma5",       # momentum / moving average
    "qlib158_std20",     # momentum / volatility window
    "qlib158_corr10",    # volume × close correlation
    "qlib158_vsumd20",   # volume directional sum delta
]


@pytest.mark.parametrize("alpha_id", SAMPLED_ALPHAS)
def test_alpha_matches_golden(alpha_id: str, panel: dict[str, pd.DataFrame], registry: Registry) -> None:
    """Compute the alpha and compare against the pinned golden CSV."""
    actual = registry.compute(alpha_id, panel)

    golden_path = GOLDEN_DIR / f"{alpha_id}.csv"
    assert golden_path.is_file(), f"missing golden fixture: {golden_path}"

    expected = pd.read_csv(golden_path, index_col=0, parse_dates=True)

    # Column / shape match
    assert list(actual.columns) == list(expected.columns), (
        f"{alpha_id}: column mismatch actual={list(actual.columns)} "
        f"expected={list(expected.columns)}"
    )
    assert actual.shape == expected.shape, (
        f"{alpha_id}: shape mismatch actual={actual.shape} expected={expected.shape}"
    )

    # Value equality at 1e-6 relative tolerance, NaN-equal.
    np.testing.assert_allclose(
        actual.to_numpy(dtype=np.float64),
        expected.to_numpy(dtype=np.float64),
        rtol=1e-6,
        atol=1e-9,
        equal_nan=True,
        err_msg=f"{alpha_id}: values diverged from golden fixture",
    )
