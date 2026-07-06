"""Golden-fixture regression tests for the GTJA-191 part-2 port (alphas 101-191).

Five representative alphas spanning the 101-191 range are pinned against
CSV goldens generated from a seeded synthetic panel. ``assert_allclose`` with
``rtol=1e-6, equal_nan=True`` detects any drift in either the operator algebra
or the alpha formula transcription.

Note on panel size: the task spec calls for a 30-row × 5-column panel, but
``gtja191_130`` requires a 40-day rolling volume mean (warmup ≥ 60 bars by
the registry's ``min_warmup_bars`` field), so a 30-row panel returns >95 %
NaN and fails the registry's sanity check. We use ``N=80`` here as the
minimum row count that lets all five sample alphas produce a non-trivial
output. The seed (``np.random.RandomState(42)``) is unchanged.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.factors.registry import Registry


GOLDENS_DIR = Path(__file__).parent / "fixtures" / "goldens"
SAMPLED_ALPHAS = (
    "gtja191_101",
    "gtja191_130",
    "gtja191_150",
    "gtja191_175",
    "gtja191_191",
)


def _build_panel() -> dict[str, pd.DataFrame]:
    """Reproducible 80-row × 5-symbol OHLCV+amount+benchmark panel (seed=42)."""
    rng = np.random.RandomState(42)
    n_rows, n_syms = 80, 5
    idx = pd.date_range("2024-01-01", periods=n_rows, freq="D")
    cols = [f"SYM{i}" for i in range(n_syms)]
    close = (
        pd.DataFrame(
            100.0 + np.cumsum(rng.normal(0, 1, (n_rows, n_syms)), axis=0),
            index=idx,
            columns=cols,
        ).abs()
        + 1.0
    )
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.DataFrame(
        np.maximum(close.to_numpy(), open_.to_numpy())
        + rng.uniform(0, 1, (n_rows, n_syms)),
        index=idx,
        columns=cols,
    )
    low = (
        pd.DataFrame(
            np.minimum(close.to_numpy(), open_.to_numpy())
            - rng.uniform(0, 1, (n_rows, n_syms)),
            index=idx,
            columns=cols,
        ).abs()
        + 0.01
    )
    volume = pd.DataFrame(
        rng.uniform(1e5, 1e7, (n_rows, n_syms)), index=idx, columns=cols
    )
    amount = volume * close
    benchmark_close = pd.DataFrame(
        np.tile(close.mean(axis=1).to_numpy().reshape(-1, 1), (1, n_syms)),
        index=idx,
        columns=cols,
    )
    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "amount": amount,
        "benchmark_close": benchmark_close,
    }


@pytest.fixture(scope="module")
def panel() -> dict[str, pd.DataFrame]:
    return _build_panel()


@pytest.fixture(scope="module")
def registry() -> Registry:
    return Registry()


@pytest.mark.parametrize("alpha_id", SAMPLED_ALPHAS)
def test_gtja191_sample_matches_golden(
    alpha_id: str,
    panel: dict[str, pd.DataFrame],
    registry: Registry,
) -> None:
    """Each sample alpha must reproduce its pinned CSV golden bit-equivalently."""
    out = registry.compute(alpha_id, panel)
    golden_path = GOLDENS_DIR / f"{alpha_id}.csv"
    assert golden_path.is_file(), f"golden fixture missing: {golden_path}"
    golden = pd.read_csv(golden_path, index_col=0, parse_dates=True)
    golden.columns = list(golden.columns)
    assert out.shape == golden.shape, (
        f"{alpha_id}: shape {out.shape} != golden {golden.shape}"
    )
    np.testing.assert_allclose(
        out.to_numpy(dtype=np.float64),
        golden.to_numpy(dtype=np.float64),
        rtol=1e-6,
        equal_nan=True,
        err_msg=f"{alpha_id} drift vs. golden",
    )
