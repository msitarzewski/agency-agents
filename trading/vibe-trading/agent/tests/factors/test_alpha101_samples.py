"""Numerical golden tests for a representative slice of the alpha101 zoo.

Five alphas (#1, #5, #11, #41, #54) are pinned against pre-computed CSV
fixtures in ``fixtures/goldens/``. The fixtures were generated from a
``np.random.RandomState(42)`` 30-row x 5-symbol panel; any change in the
operator semantics or the alpha implementation will surface here.

The chosen alphas span the operator surface:

* alpha101_001 — ``ts_argmax``, ``signed_power``, ``ts_std``, ``rank``
* alpha101_005 — ``rolling_sum`` via ``DataFrame.rolling``, ``rank``, ``abs``
* alpha101_011 — ``ts_max``, ``ts_min``, ``delta``, ``rank``
* alpha101_041 — power on element-wise product, vwap subtraction
* alpha101_054 — ``safe_div`` over a degree-5 polynomial ratio
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.factors.registry import Registry


GOLDEN_DIR = Path(__file__).parent / "fixtures" / "goldens"

SAMPLED_ALPHAS = (
    "alpha101_001",
    "alpha101_005",
    "alpha101_011",
    "alpha101_041",
    "alpha101_054",
)


def _build_panel(n_rows: int = 30, n_cols: int = 5) -> dict[str, pd.DataFrame]:
    """Reproduce the seeded panel used to generate the golden CSVs.

    Keep this in lockstep with the generator block in the docstring of
    ``fixtures/goldens/`` — any drift here breaks every golden assertion.
    """
    rng = np.random.RandomState(42)
    idx = pd.date_range("2024-01-01", periods=n_rows, freq="D")
    cols = [f"S{i}" for i in range(n_cols)]

    close_arr = 100.0 + np.cumsum(rng.randn(n_rows, n_cols), axis=0)
    close = pd.DataFrame(close_arr, index=idx, columns=cols).abs() + 1.0
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.DataFrame(
        np.maximum(close.to_numpy(), open_.to_numpy()) + rng.rand(n_rows, n_cols),
        index=idx,
        columns=cols,
    )
    low = pd.DataFrame(
        np.minimum(close.to_numpy(), open_.to_numpy()) - rng.rand(n_rows, n_cols),
        index=idx,
        columns=cols,
    ).abs() + 0.01
    volume = pd.DataFrame(
        rng.randint(1_000, 100_000, size=(n_rows, n_cols)).astype(float),
        index=idx,
        columns=cols,
    )
    vwap = (high + low + close + open_) / 4.0
    amount = volume * close

    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "amount": amount,
        "vwap": vwap,
    }


def _load_golden(alpha_id: str) -> pd.DataFrame:
    """Load a golden CSV and coerce the index dtype to match the live panel."""
    path = GOLDEN_DIR / f"{alpha_id}.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df.astype(np.float64)


@pytest.fixture(scope="module")
def panel() -> dict[str, pd.DataFrame]:
    """Module-scoped panel reused by every parametrized sample."""
    return _build_panel()


@pytest.fixture(scope="module")
def registry() -> Registry:
    return Registry()


@pytest.mark.parametrize("alpha_id", SAMPLED_ALPHAS)
def test_alpha101_sample_matches_golden(
    alpha_id: str,
    panel: dict[str, pd.DataFrame],
    registry: Registry,
) -> None:
    """Recomputed factor must match the checked-in golden CSV to 1e-6 rtol."""
    actual = registry.compute(alpha_id, panel)
    expected = _load_golden(alpha_id)

    assert actual.shape == expected.shape, (
        f"{alpha_id}: shape mismatch — got {actual.shape}, expected {expected.shape}"
    )
    assert list(actual.columns) == list(expected.columns), (
        f"{alpha_id}: column mismatch — got {list(actual.columns)}, "
        f"expected {list(expected.columns)}"
    )

    actual_arr = actual.to_numpy(dtype=np.float64, na_value=np.nan)
    expected_arr = expected.to_numpy(dtype=np.float64, na_value=np.nan)

    np.testing.assert_allclose(
        actual_arr,
        expected_arr,
        rtol=1e-6,
        atol=1e-9,
        equal_nan=True,
        err_msg=f"{alpha_id}: numerical drift vs golden",
    )


def test_all_sampled_goldens_exist() -> None:
    """Sanity gate: every sampled alpha must have a corresponding golden CSV."""
    missing = [
        alpha_id
        for alpha_id in SAMPLED_ALPHAS
        if not (GOLDEN_DIR / f"{alpha_id}.csv").is_file()
    ]
    assert not missing, f"missing golden CSVs for: {missing}"
