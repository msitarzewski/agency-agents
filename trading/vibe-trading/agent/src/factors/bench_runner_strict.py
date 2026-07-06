"""Strict bench runner: IC + random control + train/test OOS split.

Companion to ``bench_runner.py``. The math in ``run_bench()`` is unchanged
— this module adds a stricter category gate that requires a same-universe
random-control comparison and (optionally) an out-of-sample split before
an alpha is allowed to graduate to ``confirmed_alive``.

Why this exists
---------------

``bench_runner.categorise()`` currently labels an alpha ``alive`` whenever
its raw IC mean exceeds 0.02, the IC-positive ratio exceeds 0.55, and the
single-sample t-stat exceeds 2. That gate accepts factors whose IC is
driven by a shared cross-sectional beta (e.g. market or size) rather than
genuine alpha — the IC and t-stat will both pass even when a random shuffle
of the same factor produces a comparable IC, because the test is
benchmarked against zero, not against a same-universe random control.

The bili_stock A-share study (Soli22de/Bili_Stock, 9-month audit of 12
single factors and 191 GTJA variants) found this gate is the dominant
source of false-positive alphas in A-share research: every factor passed
the raw IC test at some parameter setting, but only 1 of 12 survived a
parallel random-control comparison.

This module makes the random control an explicit, mandatory step. The
heuristic follows Harvey-Liu-Zhu (2016) "...and the Cross-Section of
Expected Returns": once you correct for multiple testing across the
factor zoo, the median |t| threshold for a published factor needs to be
~3.5, not 2.0. We achieve the same effect with a same-universe random
shuffle rather than a multiple-testing correction.

API contract
------------

``run_bench_strict()`` returns the same top-level keys as ``run_bench()``
plus:

- ``train_rows`` / ``test_rows`` (when ``oos_split`` is provided)
- ``random_ic_mean`` / ``alpha_t`` per alpha row
- ``confirmed_alive`` / ``train_only`` / ``reversed_strict`` / ``noise``
  category counts

Existing ``run_bench()`` is untouched. The strict path is opt-in via the
dedicated function; the original behaviour is preserved for any caller
that still wants the cheaper gate.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal

import numpy as np
import pandas as pd

from src.factors.factor_analysis_core import compute_ic_series
from src.factors.registry import (
    Registry,
    RegistryError,
    SkipAlpha,
    get_default_registry,
)
from src.tools.alpha_bench_tool import _compute_forward_returns, _load_universe_panel

logger = logging.getLogger(__name__)


ProgressCb = Callable[[int, int, str], None]
"""Signature: ``on_progress(n_done, n_total, current_alpha_id)``."""

StrictCategory = Literal[
    "confirmed_alive",  # signal beats random in full sample AND in OOS (when provided)
    "train_only",        # signal beats random in train, fails in test
    "reversed_strict",   # signal IC < random IC with negative alpha_t < -2
    "noise",             # alpha_t in [-2, 2]; indistinguishable from random
]


@dataclass(frozen=True, slots=True)
class StrictThresholds:
    """Tunable gate parameters for ``categorise_strict()``.

    ``alpha_t_threshold`` defaults to 2.0 to stay backward-comparable with the
    existing ``categorise()`` gate; raising it to 3.5 implements the
    Harvey-Liu-Zhu (2016) multiple-testing recommendation when running the
    full 455-alpha zoo.
    """

    alpha_t_threshold: float = 2.0
    min_ic_count: int = 30  # need enough periods for a meaningful t-stat


# ── Random control helpers ─────────────────────────────────────────────────


def _shuffle_within_rows(
    df: pd.DataFrame, *, seed: int
) -> pd.DataFrame:
    """Cross-sectionally permute finite values within each row.

    This preserves the per-date cross-sectional distribution of the factor
    while destroying the actual signal→instrument mapping. The result is a
    "factor with no information" that has the same statistical envelope as
    the original — which is what makes it a fair null hypothesis baseline
    for IC computation.

    Non-finite cells (``NaN``, ``+inf``, ``-inf``) are pinned in place. We
    treat infinities the same as NaN here even though
    ``Registry._validate_output`` rejects infinities upstream — this keeps
    the shuffle robust against third-party zoo plugins that bypass the
    standard registry path and keeps the IC of the shuffled factor
    insensitive to whether the cell happened to land on the inf or just
    next to it.

    Args:
        df: Factor frame, index=date, columns=instrument codes.
        seed: RNG seed for reproducibility.

    Returns:
        A new DataFrame with the same index/columns but with each row's
        finite values randomly reassigned to other finite positions in
        the same row. Non-finite positions stay non-finite.
    """
    rng = np.random.default_rng(seed)
    values = df.to_numpy(copy=True)
    n_rows, _ = values.shape
    for i in range(n_rows):
        row = values[i]
        mask = np.isfinite(row)
        if mask.sum() < 2:
            continue
        permuted = rng.permutation(row[mask])
        row[mask] = permuted
        values[i] = row
    return pd.DataFrame(values, index=df.index, columns=df.columns)


def compute_random_ic_series(
    factor_df: pd.DataFrame,
    return_df: pd.DataFrame,
    *,
    n_seeds: int = 5,
    base_seed: int = 42,
) -> pd.Series:
    """Mean IC series across ``n_seeds`` row-shuffled random controls.

    Returns one IC value per date, averaged across **all** ``n_seeds``
    seeds on dates where every seed produced a valid IC. Dates where any
    seed dropped out (e.g. fewer than ``_MIN_VALID_PER_DATE=5`` paired
    non-NaN cells) are excluded from the output via an inner join — the
    random control is supposed to be a stable per-date baseline, so a
    "1-seed average on some dates, 5-seed on others" mix would silently
    inflate variance on the borderline dates.

    Empty input or zero common dates yields an empty Series.
    """
    if factor_df.empty or return_df.empty:
        return pd.Series(dtype=float)
    seeds = [base_seed + i for i in range(max(1, n_seeds))]
    ic_frames: list[pd.Series] = []
    for s in seeds:
        shuffled = _shuffle_within_rows(factor_df, seed=s)
        ic = compute_ic_series(shuffled, return_df)
        if not ic.empty:
            ic_frames.append(ic)
    if not ic_frames:
        return pd.Series(dtype=float)
    # Inner join so every retained date is the mean of all available seeds
    # uniformly — see docstring rationale above.
    combined = pd.concat(ic_frames, axis=1, join="inner")
    return combined.mean(axis=1)


def alpha_series_paired(
    signal_ic: pd.Series, random_ic: pd.Series
) -> pd.Series:
    """Per-date paired alpha = signal_IC - random_IC, on the common index."""
    common = signal_ic.index.intersection(random_ic.index)
    if common.empty:
        return pd.Series(dtype=float)
    return (signal_ic.loc[common] - random_ic.loc[common]).dropna()


def t_stat(series: pd.Series) -> float:
    """One-sample t-stat against zero (returns 0.0 if undefined)."""
    n = len(series)
    if n < 2:
        return 0.0
    std = float(series.std(ddof=1))
    if not (std > 0 and math.isfinite(std)):
        return 0.0
    return float(series.mean() / (std / math.sqrt(n)))


# ── Theme breakdown (strict-aware version of bench_runner.theme_breakdown) ──


def _theme_breakdown_strict(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Aggregate strict-category counts per theme tag.

    Mirrors ``bench_runner.theme_breakdown`` but with the strict
    ``confirmed_alive`` / ``train_only`` / ``reversed_strict`` / ``noise``
    buckets, plus legacy ``alive`` / ``reversed`` / ``dead`` aliases so
    existing dashboards keep working without code changes.
    """
    by_theme: dict[str, dict[str, int]] = {}
    for row in rows:
        cat = row.get("_category", "noise")
        themes = row.get("theme", []) or ["uncategorised"]
        for theme in themes:
            bucket = by_theme.setdefault(
                theme,
                {
                    "confirmed_alive": 0,
                    "train_only": 0,
                    "reversed_strict": 0,
                    "noise": 0,
                    "alive": 0,
                    "reversed": 0,
                    "dead": 0,
                    "count": 0,
                },
            )
            bucket[cat] = bucket.get(cat, 0) + 1
            bucket["count"] += 1
            # Legacy aliases mirror the bucket aliasing in the entry dict.
            if cat == "confirmed_alive":
                bucket["alive"] += 1
            elif cat == "reversed_strict":
                bucket["reversed"] += 1
            elif cat in ("noise", "train_only"):
                bucket["dead"] += 1
    return by_theme


# ── Strict categorisation ──────────────────────────────────────────────────


def categorise_strict(
    row: dict[str, Any],
    thresholds: StrictThresholds = StrictThresholds(),
) -> str:
    """Bucket a strict bench row into one of four ``StrictCategory`` values.

    Required keys on ``row``:
        - ``alpha_t_full`` (float)
        - ``alpha_t_train`` (Optional[float])  — None when no OOS split was run
        - ``alpha_t_test`` (Optional[float])   — None when no OOS split was run
        - ``ic_count`` (int)

    Rules:
        - ``alpha_t_full <= -thr``                          → ``reversed_strict``
        - ``alpha_t_full >=  thr`` and (no OOS or ``alpha_t_test >= thr``)
                                                            → ``confirmed_alive``
        - ``alpha_t_full >=  thr`` and ``alpha_t_test <= -thr`` (OOS sign-flip)
                                                            → ``reversed_strict``
        - ``alpha_t_full >=  thr`` and ``alpha_t_test`` in the noise band
                                                            → ``train_only``
        - everything else (including ``ic_count < min_ic_count``) → ``noise``

    The OOS sign-flip case is deliberately bucketed alongside the
    reversed_strict outcome rather than as ``train_only``: a factor that
    inverts in OOS is one of the *strongest* possible signals that the
    train-period alpha was an artefact, and quantitative researchers want
    that distinction surfaced separately from a benign decay-to-zero.
    """
    if row["ic_count"] < thresholds.min_ic_count:
        return "noise"

    t_full = row["alpha_t_full"]
    t_test = row.get("alpha_t_test")
    thr = thresholds.alpha_t_threshold

    # Strict reversed: full sample alpha is significantly negative.
    if t_full <= -thr:
        return "reversed_strict"

    # Confirmed alive requires full-sample alpha_t > thr AND, when OOS was
    # run, the test-period alpha must also clear thr (same sign as train).
    if t_full >= thr:
        if t_test is None or t_test >= thr:
            return "confirmed_alive"
        # OOS sign-flip is the most diagnostic failure — treat as
        # reversed_strict, not train_only.
        if t_test <= -thr:
            return "reversed_strict"
        # Full sample passes but OOS sits in the noise band → train-only.
        return "train_only"

    return "noise"


# ── Public entrypoint ──────────────────────────────────────────────────────


def run_bench_strict(
    zoo: str,
    universe: str,
    period: str,
    *,
    random_control: bool,
    n_random_seeds: int = 5,
    oos_split: str | None = None,
    thresholds: StrictThresholds | None = None,
    top: int = 20,
    on_progress: ProgressCb | None = None,
    registry: Registry | None = None,
) -> dict[str, Any]:
    """Strict-mode bench: like ``run_bench`` but with mandatory random control.

    Args:
        zoo: Zoo id (e.g. ``alpha101``, ``gtja191``, ``qlib158``, ``academic``).
        universe: Universe key (``csi300`` / ``sp500`` / ``btc-usdt`` / ...).
        period: ``YYYY-YYYY`` or ``YYYY-MM-DD/YYYY-MM-DD``.
        random_control: ``True`` builds same-universe random controls per
            alpha (recommended). ``False`` is allowed but **must** be passed
            explicitly — passing nothing raises ``TypeError`` because the
            argument is keyword-only and has no default. This mirrors the
            ``random_control`` rail from Soli22de/Bili_Stock's foundation
            backtest engine.
        n_random_seeds: Number of row-shuffled controls per alpha. Larger
            values shrink the random IC variance and tighten the alpha
            t-stat; default 5 is enough for a 455-alpha zoo without making
            the bench more than ~6x slower.
        oos_split: Date string (``YYYY-MM-DD``) splitting train and test.
            ``None`` disables the OOS gate (full sample only).
        thresholds: ``StrictThresholds`` instance. Defaults to
            ``alpha_t_threshold=2.0`` (back-compat). Pass ``3.5`` to apply
            Harvey-Liu-Zhu (2016) multiple-testing correction when bench
            covers a large zoo.
        top: How many top-IR alphas to keep in summary lists.
        on_progress: Optional ``(n_done, n_total, alpha_id)`` callback.
        registry: Optional pre-built registry for tests.

    Returns:
        Dict containing all the keys ``run_bench()`` returns, plus:

        - ``random_control`` (bool)
        - ``n_random_seeds`` (int)
        - ``oos_split`` (str | None)
        - ``alpha_t_threshold`` (float)
        - ``confirmed_alive`` / ``train_only`` / ``reversed_strict`` /
          ``noise`` count keys
        - Each row carries ``alpha_t_full``, ``alpha_t_train`` (when OOS),
          ``alpha_t_test`` (when OOS), ``random_ic_mean``.

    Raises:
        TypeError: If ``random_control`` is omitted (keyword-only, no default).
    """
    if random_control is None:  # pragma: no cover — guarded by signature
        raise TypeError(
            "run_bench_strict requires random_control to be passed explicitly "
            "(True or False). This rail is borrowed from "
            "Soli22de/Bili_Stock's foundation engine after a 9-month audit "
            "where every accidental random_control=None call inflated alpha "
            "by 3-8 percentage points."
        )

    start = time.monotonic()
    thresholds = thresholds or StrictThresholds()
    # Clamp n_random_seeds once and store the actual value used so the
    # wire response doesn't lie about the seed count when callers pass 0
    # (e.g. from a JSON-config import).
    effective_seeds = max(1, int(n_random_seeds))

    # Initialise the full schema up-front so even early-error returns
    # carry zeroed counters and empty lists — downstream consumers can
    # depend on the keys always being present.
    entry: dict[str, Any] = {
        "status": "pending",
        "zoo": zoo,
        "universe": universe,
        "period": period,
        "random_control": random_control,
        "n_random_seeds": effective_seeds,
        "oos_split": oos_split,
        "alpha_t_threshold": thresholds.alpha_t_threshold,
        "n_alphas_tested": 0,
        "n_skipped": 0,
        "confirmed_alive": 0,
        "train_only": 0,
        "reversed_strict": 0,
        "noise": 0,
        # Legacy keys mirror run_bench's surface so existing dashboard
        # paths (alpha_routes._result_for_wire) keep rendering. See C1
        # in the PR's code review notes.
        "alive": 0,
        "reversed": 0,
        "dead": 0,
        "by_theme": {},
        "top5_by_ir": [],
        "top5_by_alpha_t": [],
        "dead_examples": [],
        "rows": [],
        "skipped": [],
        "meta": {},
    }

    def _finish_error(msg: str) -> dict[str, Any]:
        entry["status"] = "error"
        entry["error"] = msg
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    reg = registry if registry is not None else get_default_registry()
    alpha_ids = reg.list(zoo=zoo)
    if not alpha_ids:
        return _finish_error(f"no alphas registered under zoo={zoo!r}")

    try:
        panel = _load_universe_panel(universe, period)
    except (ValueError, NotImplementedError, RuntimeError) as exc:
        return _finish_error(f"universe load failed: {exc}")

    try:
        return_df = _compute_forward_returns(panel)
    except Exception as exc:  # noqa: BLE001
        return _finish_error(f"forward returns failed: {exc}")

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    n_total = len(alpha_ids)

    oos_ts: pd.Timestamp | None = None
    if oos_split is not None:
        try:
            oos_ts = pd.Timestamp(oos_split)
        except (TypeError, ValueError) as exc:
            return _finish_error(f"invalid oos_split {oos_split!r}: {exc}")

    def _fire_progress(idx: int, aid: str) -> None:
        if on_progress is None:
            return
        try:
            on_progress(idx, n_total, aid)
        except Exception:  # noqa: BLE001
            logger.exception("on_progress callback raised; ignoring")

    for idx, aid in enumerate(alpha_ids, start=1):
        try:
            factor_df = reg.compute(aid, panel)
            signal_ic = compute_ic_series(factor_df, return_df)
            if signal_ic.empty:
                skipped.append(
                    {"id": aid, "reason": "empty IC series", "kind": "typed"}
                )
                _fire_progress(idx, aid)
                continue

            if random_control:
                random_ic = compute_random_ic_series(
                    factor_df,
                    return_df,
                    n_seeds=effective_seeds,
                )
            else:
                random_ic = pd.Series(0.0, index=signal_ic.index)

            alpha_full = alpha_series_paired(signal_ic, random_ic)
            alpha_t_full = t_stat(alpha_full)

            alpha_t_train: float | None = None
            alpha_t_test: float | None = None
            ic_count_train: int | None = None
            ic_count_test: int | None = None
            if oos_ts is not None:
                # Train-inclusive, test-exclusive on the boundary date so
                # the OOS guard cannot leak the split bar across buckets.
                # See A1 in the PR's code review notes.
                train_mask = alpha_full.index <= oos_ts
                test_mask = alpha_full.index > oos_ts
                train_slice = alpha_full[train_mask]
                test_slice = alpha_full[test_mask]
                alpha_t_train = t_stat(train_slice)
                alpha_t_test = t_stat(test_slice)
                ic_count_train = int(len(train_slice))
                ic_count_test = int(len(test_slice))

            meta = reg.get(aid).meta or {}
            ic_mean = float(signal_ic.mean())
            ic_std = float(signal_ic.std())
            ir = ic_mean / ic_std if ic_std > 0 else 0.0
            rows.append(
                {
                    "id": aid,
                    "ic_mean": round(ic_mean, 6),
                    "ic_std": round(ic_std, 6),
                    "ir": round(ir, 4),
                    # Sorting uses the unrounded raw values to keep
                    # top-N stable across runs (see A7 in review).
                    "_ir_raw": float(ir),
                    "_alpha_t_full_raw": float(alpha_t_full),
                    "_ic_mean_raw": ic_mean,
                    "ic_positive_ratio": round(float((signal_ic > 0).mean()), 4),
                    "ic_count": int(len(signal_ic)),
                    "ic_count_train": ic_count_train,
                    "ic_count_test": ic_count_test,
                    "random_ic_mean": round(float(random_ic.mean()), 6),
                    "alpha_t_full": round(alpha_t_full, 4),
                    "alpha_t_train": (
                        round(alpha_t_train, 4) if alpha_t_train is not None else None
                    ),
                    "alpha_t_test": (
                        round(alpha_t_test, 4) if alpha_t_test is not None else None
                    ),
                    "theme": meta.get("theme", []),
                    "formula_latex": meta.get("formula_latex", ""),
                }
            )
        except (SkipAlpha, RegistryError, RuntimeError, KeyError, ValueError) as exc:
            skipped.append({"id": aid, "reason": str(exc), "kind": "typed"})
        except Exception as exc:  # noqa: BLE001
            logger.exception("strict bench: unexpected failure on %s", aid)
            skipped.append(
                {"id": aid, "reason": f"unexpected: {exc}", "kind": "unexpected"}
            )

        _fire_progress(idx, aid)

    for row in rows:
        row["_category"] = categorise_strict(row, thresholds)

    counts = {
        "confirmed_alive": 0,
        "train_only": 0,
        "reversed_strict": 0,
        "noise": 0,
    }
    for row in rows:
        counts[row["_category"]] += 1

    rows_by_ir = sorted(rows, key=lambda r: r["_ir_raw"], reverse=True)
    rows_by_alpha = sorted(rows, key=lambda r: r["_alpha_t_full_raw"], reverse=True)
    rows_by_ic = sorted(rows, key=lambda r: r["_ic_mean_raw"])

    def _slim(r: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": r["id"],
            "ic_mean": r["ic_mean"],
            "ir": r["ir"],
            "random_ic_mean": r["random_ic_mean"],
            "alpha_t_full": r["alpha_t_full"],
            "alpha_t_train": r["alpha_t_train"],
            "alpha_t_test": r["alpha_t_test"],
            "theme": r["theme"],
            # Keep formula_latex on the slim payload — the wiki and
            # dashboard render this cell from top5_by_ir entries (see C2
            # in the PR's code review notes).
            "formula_latex": r["formula_latex"],
            "category": r["_category"],
        }

    universe_meta_raw = panel.get("_meta") if isinstance(panel, dict) else None
    universe_meta: dict[str, Any] = {}
    if universe_meta_raw is not None:
        try:
            if hasattr(universe_meta_raw, "to_dict"):
                universe_meta = dict(universe_meta_raw.to_dict())
            else:
                universe_meta = dict(universe_meta_raw)
        except Exception:  # noqa: BLE001
            universe_meta = {"raw": str(universe_meta_raw)}

    # Strip the underscore-prefixed sort helper keys from the wire-bound
    # row payloads so they never appear in JSON responses or persisted
    # results. Keep the rest of the row schema as-is so dashboards see
    # both the strict and legacy fields.
    public_rows: list[dict[str, Any]] = []
    for r in rows:
        public_rows.append(
            {k: v for k, v in r.items() if not k.startswith("_")
             or k == "_category"}
        )

    # Legacy bucket aliasing for backward compat (see C1 in code review):
    #   alive    ← confirmed_alive  (positive, OOS-confirmed)
    #   reversed ← reversed_strict  (negative paired alpha)
    #   dead     ← noise + train_only  (everything that didn't survive)
    legacy_alive = counts["confirmed_alive"]
    legacy_reversed = counts["reversed_strict"]
    legacy_dead = counts["noise"] + counts["train_only"]

    by_theme = _theme_breakdown_strict(rows)

    entry.update(
        {
            "status": "ok",
            "n_alphas_tested": len(rows),
            "n_skipped": len(skipped),
            "confirmed_alive": counts["confirmed_alive"],
            "train_only": counts["train_only"],
            "reversed_strict": counts["reversed_strict"],
            "noise": counts["noise"],
            # Legacy keys for run_bench wire compatibility.
            "alive": legacy_alive,
            "reversed": legacy_reversed,
            "dead": legacy_dead,
            "by_theme": by_theme,
            "top5_by_ir": [_slim(r) for r in rows_by_ir[: min(5, top)]],
            "top5_by_alpha_t": [_slim(r) for r in rows_by_alpha[: min(5, top)]],
            "dead_examples": [_slim(r) for r in rows_by_ic[:5]],
            "rows": public_rows,
            "skipped": skipped,
            "meta": universe_meta,
            "wall_seconds": round(time.monotonic() - start, 2),
        }
    )
    return entry
