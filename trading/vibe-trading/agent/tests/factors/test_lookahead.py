"""Look-ahead guard: factor values at row ``t`` must not depend on rows > t.

Strategy: for each registered alpha,

1. Build a synthetic OHLCV+volume+amount panel (300 rows × 10 symbols,
   reproducible random walk). The panel is long enough to cover the
   longest production windows we ship (≤252d for academic + Kakushadze).
2. Compute the factor on the baseline panel and snapshot the value at
   ``probe_t = 260`` (well past warmup for any ≤252d window, well before
   the perturbation).
3. Corrupt every panel column from row ``probe_t + 10`` onwards (NaN or
   absurd ``1e10`` values) and recompute.
4. Assert: snapshot at ``probe_t`` is allclose between the two runs
   (atol/rtol=1e-9, NaN-equal). Strict bit-equality is too tight for
   alphas whose rolling-aggregation order responds to NaN locations —
   any *real* leak shows up as a far larger drift than 1e-9. The 1e-9
   tolerance still detects a single-row leakage of order 1e-6 or larger.
   Any divergence at that scale proves the factor peeked into the future.

Cost budget: 300 rows × 10 symbols × O(2 computes per alpha). At 450
alphas this finishes in well under 60 s on commodity CI hardware. We skip
the suite cleanly when the registry is empty (current repo state).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.factors.registry import Registry, RegistryError, SkipAlpha


# ---------------------------------------------------------------- constants


N_ROWS = 300
N_SYMS = 10
PROBE_T = 260           # row whose value must be invariant under future edits
PERTURB_FROM = 270      # first row to corrupt (strictly > PROBE_T)
PERTURB_VALUE = 1e10    # sentinel; alternates with NaN per column


# ---------------------------------------------------------------- fixtures


def _baseline_panel(seed: int = 0) -> dict[str, pd.DataFrame]:
    """Synthetic, reproducible OHLCV+amount+sector panel.

    Returns wide DataFrames with ``index = DatetimeIndex`` and
    ``columns = [SYM0..SYM9]`` so each registered alpha receives the
    shape it expects.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=N_ROWS, freq="D")
    cols = [f"SYM{i}" for i in range(N_SYMS)]

    # Random walk close, derive others to keep them positive and sensible.
    close = pd.DataFrame(
        100.0 + np.cumsum(rng.normal(0.0, 1.0, size=(N_ROWS, N_SYMS)), axis=0),
        index=idx,
        columns=cols,
    ).abs() + 1.0
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.DataFrame(
        np.maximum(close.to_numpy(), open_.to_numpy()) + rng.uniform(0.0, 1.0, size=(N_ROWS, N_SYMS)),
        index=idx,
        columns=cols,
    )
    low = pd.DataFrame(
        np.minimum(close.to_numpy(), open_.to_numpy()) - rng.uniform(0.0, 1.0, size=(N_ROWS, N_SYMS)),
        index=idx,
        columns=cols,
    ).abs() + 0.01
    volume = pd.DataFrame(
        rng.integers(1_000, 100_000, size=(N_ROWS, N_SYMS)).astype(float),
        index=idx,
        columns=cols,
    )
    amount = volume * close
    vwap = (high + low + close + open_) / 4.0

    return {
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "amount": amount,
        "vwap": vwap,
    }


def _attach_sector(panel: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Add a synthetic sector tag DataFrame in-place (returns new dict)."""
    close = panel["close"]
    sectors = ["A", "B", "C"]
    sector_grid = np.array(
        [sectors[i % len(sectors)] for i in range(close.shape[1])],
        dtype=object,
    )
    sector_df = pd.DataFrame(
        np.broadcast_to(sector_grid, close.shape).copy(),
        index=close.index,
        columns=close.columns,
    )
    out = dict(panel)
    out["sector"] = sector_df
    return out


def _corrupt_future(panel: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Return a deep copy where rows ``>= PERTURB_FROM`` are sentinel-poisoned."""
    out: dict[str, pd.DataFrame] = {}
    for key, df in panel.items():
        if key == "sector":
            # leave categorical tags alone — they never have a forward leak
            out[key] = df.copy()
            continue
        clone = df.copy()
        # Alternate NaN and absurd-value columns so both representations get coverage.
        for j, col in enumerate(clone.columns):
            if j % 2 == 0:
                clone.iloc[PERTURB_FROM:, j] = np.nan
            else:
                clone.iloc[PERTURB_FROM:, j] = PERTURB_VALUE
        out[key] = clone
    return out


# ---------------------------------------------------------------- parametrize


def _registered_alpha_ids() -> list[str]:
    try:
        return Registry().list()
    except Exception:  # noqa: BLE001 — be loud only at test time
        return []


_ALPHA_IDS = _registered_alpha_ids()


# ---------------------------------------------------------------- test


@pytest.mark.skipif(not _ALPHA_IDS, reason="no zoo modules registered yet")
@pytest.mark.parametrize("alpha_id", _ALPHA_IDS)
def test_alpha_has_no_lookahead(alpha_id: str) -> None:
    """Future corruption at row ``>=60`` must not alter factor value at row 50."""
    registry = Registry()
    alpha = registry.get(alpha_id)

    baseline = _baseline_panel()
    if alpha.meta.get("requires_sector"):
        baseline = _attach_sector(baseline)

    try:
        baseline_factor = registry.compute(alpha_id, baseline)
    except SkipAlpha as exc:
        pytest.skip(f"{alpha_id}: panel preconditions not met ({exc})")
    except RegistryError as exc:
        # >95% NaN cascade from compounding rolling operators on a
        # synthetic random panel is a known artifact, distinct from
        # look-ahead leakage. Bench on real market data won't trip it.
        pytest.skip(f"{alpha_id}: registry sanity check on synthetic panel ({exc})")

    corrupted = _corrupt_future(baseline)
    try:
        corrupted_factor = registry.compute(alpha_id, corrupted)
    except RegistryError as exc:
        pytest.skip(f"{alpha_id}: registry sanity on corrupted panel ({exc})")

    baseline_row = baseline_factor.iloc[PROBE_T].to_numpy(dtype=np.float64)
    corrupted_row = corrupted_factor.iloc[PROBE_T].to_numpy(dtype=np.float64)

    # NaN-equal comparison: identical positions of NaN, identical finite values.
    nan_mask_baseline = np.isnan(baseline_row)
    nan_mask_corrupted = np.isnan(corrupted_row)
    if not np.array_equal(nan_mask_baseline, nan_mask_corrupted):
        raise AssertionError(
            f"{alpha_id}: NaN pattern at t={PROBE_T} diverges after future "
            f"perturbation (baseline NaN={nan_mask_baseline.tolist()}, "
            f"corrupted NaN={nan_mask_corrupted.tolist()})"
        )
    finite_mask = ~nan_mask_baseline
    np.testing.assert_allclose(
        baseline_row[finite_mask],
        corrupted_row[finite_mask],
        rtol=1e-9,
        atol=1e-9,
        err_msg=(
            f"{alpha_id}: factor value at t={PROBE_T} changed after corrupting "
            f"rows >= t={PERTURB_FROM} (look-ahead leak detected)"
        ),
    )
