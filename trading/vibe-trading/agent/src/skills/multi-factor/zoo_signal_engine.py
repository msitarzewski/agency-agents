"""Composite signal engine over Alpha Zoo factors.

Ingests one or more alphas from the Alpha Zoo registry and combines them into
a single signal panel. Unlike ``example_signal_engine`` (per-symbol API that
takes ``dict[code, OHLCV DataFrame]`` and returns ``dict[code, Series]``), this
engine consumes a wide-panel ``dict[str, pd.DataFrame]`` -- the same shape the
registry's ``Alpha.compute(panel)`` contract uses -- and produces a panel
signal of the same shape as ``panel["close"]``.

Pipeline (executed by ``compute_signal``):

1. For each ``alpha_id`` in ``alpha_ids``, call ``Registry.compute(alpha_id, panel)``.
   Alphas that ``SkipAlpha`` or fail with ``RegistryError`` are logged and
   excluded; their weight is redistributed across the surviving alphas.
2. Optionally cross-sectionally z-score each alpha panel per date.
3. Weighted sum across survivors (equal weights when ``weights is None``).
4. If ``top_n`` and/or ``bottom_n`` are set, convert the composite to
   discrete positions in ``{-1.0, 0.0, +1.0}`` (long top-N, short bottom-N,
   long-short when both are set). Otherwise return the raw composite score
   and let the caller decide how to size positions.

NaN policy: NaN is preserved wherever every alpha is NaN for that cell, or
when the row had no valid cross-sectional data to standardize. We never
silently fill with zero.

Module loading: the multi-factor skill directory contains a hyphen, so this
file is not import-friendly via ``import agent.src.skills.multi-factor``.
``Registry`` is imported lazily inside ``compute_signal`` so the module
loads even when ``src.factors`` is not on ``sys.path`` (callers that only
want the dataclass shape can still import it for inspection/testing).
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _zscore_cross_section(df: pd.DataFrame) -> pd.DataFrame:
    """Per-row z-score (mean 0, std 1). Rows with zero std become NaN.

    Args:
        df: Wide panel, ``index = date``, ``columns = instrument``.

    Returns:
        Standardized panel of the same shape; rows with <2 valid values or
        zero std become all-NaN (never silent zero).
    """
    mean = df.mean(axis=1, skipna=True)
    std = df.std(axis=1, ddof=1, skipna=True)
    std = std.where(std > 1e-12)  # zero std -> NaN
    return df.sub(mean, axis=0).div(std, axis=0)


@dataclass(frozen=True)
class ZooSignalEngine:
    """Composite signal engine over Alpha Zoo factors.

    Attributes:
        alpha_ids: Ordered tuple of alpha IDs to combine.
        weights: Optional per-alpha weights; defaults to equal weights. Must
            match ``len(alpha_ids)`` when given. Surviving-alpha weights are
            re-normalized when any alpha is skipped at compute time.
        standardize: If True, cross-sectionally z-score each alpha per date
            before combining. Recommended whenever alphas have heterogeneous
            scales.
        top_n: If set, the top-N names by composite score on each date take
            ``+1.0`` and everyone else takes ``0.0`` (long-only). Must be
            positive.
        bottom_n: Symmetric short side -- bottom-N names take ``-1.0``. Can
            coexist with ``top_n`` for long-short signals. Must be positive.
    """

    alpha_ids: Tuple[str, ...]
    weights: Optional[Tuple[float, ...]] = None
    standardize: bool = True
    top_n: Optional[int] = None
    bottom_n: Optional[int] = None
    # Optional injected registry (chiefly for tests); when ``None`` we lazily
    # construct ``Registry()`` on first compute_signal call. Typed as ``Any``
    # to avoid dataclass forward-ref resolution at class-creation time when
    # the module is loaded via ``importlib.util.spec_from_file_location``.
    _registry: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.alpha_ids, tuple):
            # Allow list at construction site for ergonomic from_zoo; freeze here.
            object.__setattr__(self, "alpha_ids", tuple(self.alpha_ids))
        if len(self.alpha_ids) == 0:
            raise ValueError("alpha_ids must contain at least one alpha_id")
        if self.weights is not None:
            weights = tuple(self.weights)
            if len(weights) != len(self.alpha_ids):
                raise ValueError(
                    f"weights length {len(weights)} != alpha_ids length {len(self.alpha_ids)}"
                )
            object.__setattr__(self, "weights", weights)
        if self.top_n is not None and self.top_n <= 0:
            raise ValueError(f"top_n must be positive, got {self.top_n}")
        if self.bottom_n is not None and self.bottom_n <= 0:
            raise ValueError(f"bottom_n must be positive, got {self.bottom_n}")

    # ── Constructors ──

    @classmethod
    def from_zoo(
        cls,
        alpha_ids,
        weights=None,
        *,
        standardize: bool = True,
        top_n: Optional[int] = None,
        bottom_n: Optional[int] = None,
        registry: Any = None,
    ) -> "ZooSignalEngine":
        """Build an engine that pulls alphas from the (bundled) Alpha Zoo.

        Args:
            alpha_ids: Alpha IDs to combine, e.g. ``["alpha101_001", "guotai_002"]``.
            weights: Optional per-alpha weights; defaults to equal weights.
            standardize: Cross-sectionally z-score each alpha per date.
            top_n: Long top-N names (positive integer).
            bottom_n: Short bottom-N names (positive integer).
            registry: Pre-built ``Registry`` (chiefly for tests / alternative
                zoo roots). When ``None``, a default ``Registry()`` is built
                lazily on first ``compute_signal`` call.

        Returns:
            An immutable ``ZooSignalEngine`` instance.
        """
        return cls(
            alpha_ids=tuple(alpha_ids),
            weights=tuple(weights) if weights is not None else None,
            standardize=standardize,
            top_n=top_n,
            bottom_n=bottom_n,
            _registry=registry,
        )

    # ── Core compute ──

    def compute_signal(self, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Compose the requested alphas into a single signal panel.

        Args:
            panel: Wide panel dict with at minimum ``panel["close"]`` -- index
                is the date axis, columns are instrument codes. Other keys
                (``open``/``high``/``low``/``volume``/``vwap``/``amount``/...)
                are forwarded to each alpha's ``compute(panel)``.

        Returns:
            DataFrame of the same shape as ``panel["close"]``. When ``top_n``
            and/or ``bottom_n`` are set, values are in ``{-1.0, 0.0, +1.0}``
            (NaN positions become 0). Otherwise the raw composite score is
            returned with NaN preserved.

        Raises:
            ValueError: ``panel`` lacks the ``close`` reference frame.
        """
        ref = panel.get("close")
        if ref is None:
            raise ValueError("panel must contain a 'close' DataFrame to anchor output shape")

        registry = self._registry if self._registry is not None else _default_registry()

        per_alpha: list[pd.DataFrame] = []
        per_alpha_weights: list[float] = []
        for idx, alpha_id in enumerate(self.alpha_ids):
            w = float(self.weights[idx]) if self.weights is not None else 1.0
            try:
                raw = registry.compute(alpha_id, panel)
            except Exception as exc:  # noqa: BLE001 -- isolate per-alpha failure
                # SkipAlpha / RegistryError / KeyError(unknown id) all land here.
                logger.warning(
                    "ZooSignalEngine: alpha %r skipped (%s: %s); redistributing weight",
                    alpha_id, type(exc).__name__, exc,
                )
                continue
            per_alpha.append(_zscore_cross_section(raw) if self.standardize else raw)
            per_alpha_weights.append(w)

        if not per_alpha:
            logger.warning(
                "ZooSignalEngine: no surviving alphas from %d requested; returning all-NaN panel",
                len(self.alpha_ids),
            )
            return pd.DataFrame(np.nan, index=ref.index, columns=ref.columns)

        # Re-normalize weights across survivors so dropping alphas doesn't
        # silently shrink overall signal magnitude.
        total_w = sum(abs(w) for w in per_alpha_weights)
        if total_w <= 1e-12:
            norm_weights = [1.0 / len(per_alpha)] * len(per_alpha)
        else:
            norm_weights = [w / total_w for w in per_alpha_weights]

        # Weighted sum, NaN-aware: a cell where ALL alphas are NaN -> NaN.
        # Cells where at least one alpha is non-NaN use the survivors only,
        # but we also need to scale by the surviving weight per-cell to avoid
        # bias toward alphas that happen to have more coverage. Using
        # ``DataFrame.add(fill_value=0)`` would silently treat NaN as 0;
        # instead we keep NaN strict and let the caller decide.
        composite = per_alpha[0].mul(norm_weights[0])
        for df, w in zip(per_alpha[1:], norm_weights[1:]):
            composite = composite.add(df.mul(w), fill_value=np.nan)

        # Align to reference shape (defensive: registry already enforces shape).
        composite = composite.reindex(index=ref.index, columns=ref.columns)

        if self.top_n is None and self.bottom_n is None:
            return composite

        return self._to_positions(composite)

    def _to_positions(self, composite: pd.DataFrame) -> pd.DataFrame:
        """Convert continuous composite scores to ``{-1, 0, +1}`` positions.

        Args:
            composite: Per-date composite score panel.

        Returns:
            Position panel with the same shape, NaN treated as 0 (no position).
        """
        positions = pd.DataFrame(0.0, index=composite.index, columns=composite.columns)
        ranks_desc = composite.rank(axis=1, method="first", ascending=False, na_option="bottom")
        ranks_asc = composite.rank(axis=1, method="first", ascending=True, na_option="bottom")
        # Rows that have zero valid names take no positions at all.
        valid_row = composite.notna().any(axis=1)

        if self.top_n is not None:
            top_mask = ranks_desc.le(self.top_n) & composite.notna()
            top_mask = top_mask.mul(valid_row, axis=0).astype(bool)
            positions = positions.mask(top_mask, 1.0)

        if self.bottom_n is not None:
            bot_mask = ranks_asc.le(self.bottom_n) & composite.notna()
            bot_mask = bot_mask.mul(valid_row, axis=0).astype(bool)
            # If a name is both top and bottom (degenerate -- only happens
            # when top_n + bottom_n > valid_count), prefer the long side.
            bot_mask = bot_mask & ~positions.gt(0)
            positions = positions.mask(bot_mask, -1.0)

        return positions

    # ── Adapter for current engines ──

    def generate(self, data_map: dict[str, pd.DataFrame]) -> dict[str, pd.Series]:
        """Adapter so the engine plugs into existing ``run_backtest`` pipelines.

        The bundled backtest engines expect ``signal_engine.generate(data_map)``
        returning ``dict[code, Series]``. This method assembles the wide
        panel from ``data_map``, calls ``compute_signal``, and returns the
        per-symbol slices. When ``top_n``/``bottom_n`` is unset, the raw
        composite score is clipped to ``[-1, 1]`` to match the engine's
        weight-normalization contract.

        Args:
            data_map: ``code -> OHLCV DataFrame`` with at least the columns
                ``open``, ``high``, ``low``, ``close``, ``volume``.

        Returns:
            ``code -> signal Series`` aligned to each input's index.
        """
        if not data_map:
            return {}
        codes = list(data_map.keys())
        all_dates = sorted(set().union(*(df.index for df in data_map.values())))
        date_index = pd.DatetimeIndex(all_dates)

        panel: dict[str, pd.DataFrame] = {}
        for col in ("open", "high", "low", "close", "volume", "vwap", "amount"):
            frames: dict[str, pd.Series] = {}
            for code in codes:
                df = data_map[code]
                if col in df.columns:
                    frames[code] = df[col]
            if not frames:
                continue
            panel[col] = pd.DataFrame(frames).reindex(date_index)

        if "close" not in panel:
            raise ValueError("data_map entries must contain a 'close' column")

        composite = self.compute_signal(panel)
        if self.top_n is None and self.bottom_n is None:
            # Clip raw composite to engine's [-1, 1] weight space.
            composite = composite.clip(-1.0, 1.0)

        out: dict[str, pd.Series] = {}
        for code in codes:
            if code in composite.columns:
                series = composite[code].reindex(data_map[code].index).fillna(0.0)
            else:
                series = pd.Series(0.0, index=data_map[code].index)
            out[code] = series
        return out


# ── Lazy registry construction ──

_DEFAULT_REGISTRY: Any = None


def _default_registry():
    """Build (or reuse) the default bundled-zoo registry on demand.

    Imported lazily so ``zoo_signal_engine`` can be imported by standalone
    tooling that does not have ``src.factors`` on ``sys.path``.
    """
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        from src.factors.registry import Registry  # local import (see module docstring)

        _DEFAULT_REGISTRY = Registry()
    return _DEFAULT_REGISTRY


# ── Smoke test (executed via ``python zoo_signal_engine.py``) ──

if __name__ == "__main__":
    # Build a tiny synthetic panel and confirm the engine survives a registry
    # that holds zero matching alphas (everything is skipped -> all-NaN frame).
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    symbols = ["AAA", "BBB", "CCC"]
    rng = np.random.default_rng(0)
    synthetic_panel: dict[str, pd.DataFrame] = {
        col: pd.DataFrame(
            rng.standard_normal((len(dates), len(symbols))) + 100.0,
            index=dates,
            columns=symbols,
        )
        for col in ("open", "high", "low", "close", "volume")
    }

    class _EmptyRegistry:
        """Mimics ``Registry`` shape; every compute() raises KeyError."""

        def compute(self, alpha_id: str, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
            raise KeyError(f"alpha_id {alpha_id!r} not in registry")

    engine = ZooSignalEngine.from_zoo(
        ["nonexistent_001", "nonexistent_002"],
        registry=_EmptyRegistry(),  # type: ignore[arg-type]
    )
    out = engine.compute_signal(synthetic_panel)
    assert out.shape == synthetic_panel["close"].shape, "shape mismatch"
    assert out.isna().all().all(), "expected all-NaN panel with zero surviving alphas"
    print(f"ok: engine={engine}")
    print(f"ok: output shape={out.shape}, all-NaN={bool(out.isna().all().all())}")

    # Also exercise the long-short branch with a fake registry that returns
    # deterministic alpha panels.
    class _FakeRegistry:
        def compute(self, alpha_id: str, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
            close = panel["close"]
            if alpha_id == "fake_mom":
                return close.pct_change(3)
            if alpha_id == "fake_rev":
                return -close.pct_change(1)
            raise KeyError(alpha_id)

    ls_engine = ZooSignalEngine.from_zoo(
        ["fake_mom", "fake_rev", "missing_001"],
        weights=[0.6, 0.4, 1.0],
        top_n=1,
        bottom_n=1,
        registry=_FakeRegistry(),  # type: ignore[arg-type]
    )
    positions = ls_engine.compute_signal(synthetic_panel)
    assert positions.shape == synthetic_panel["close"].shape
    last_row = positions.iloc[-1]
    assert (last_row == 1.0).sum() == 1, "expected exactly one long"
    assert (last_row == -1.0).sum() == 1, "expected exactly one short"
    print(f"ok: long-short last row={last_row.to_dict()}")
