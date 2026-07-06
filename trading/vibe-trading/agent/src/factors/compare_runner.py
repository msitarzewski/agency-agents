"""Head-to-head comparison of hand-picked alphas.

Shared core behind the three ``alpha compare`` surfaces:

* ``vibe-trading alpha compare`` (CLI — ``factors/cli_handlers.py``)
* ``POST /alpha/compare`` (Web UI — ``api/alpha_routes.py``)
* the ``alpha_compare`` agent tool (``tools/alpha_compare_tool.py``)

All three resolve a list of alpha ids and delegate the actual work here so the
grouping / bench / ranking logic lives in exactly one place. The core groups the
requested ids by their owning zoo, benches only those ids via
``run_bench(only=...)`` (so comparing three alphas does not bench all 191 in a
zoo), merges the per-alpha IC rows, and ranks them by a chosen metric with a
``delta_<metric>_vs_best`` column.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Iterable

from src.factors import bench_runner
from src.factors.registry import Registry

logger = logging.getLogger(__name__)

#: Metrics a comparison can be ranked by (descending — higher is "better").
SORT_KEYS: tuple[str, ...] = ("ir", "ic_mean", "ic_positive_ratio", "ic_count")

#: Progress callback shape, identical to ``bench_runner.ProgressCb``:
#: ``(n_done, n_total, alpha_id) -> None``, reported across the whole comparison
#: (not per-zoo) so a UI sees one monotonic 0..N bar.
ProgressCb = Callable[[int, int, str], None]


def _sort_value(row: dict[str, Any], key: str) -> float:
    """Numeric sort value for a bench row; missing/garbage coerces to 0.0."""
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _normalise_skip(skip: dict[str, Any]) -> dict[str, Any]:
    """Shape a bench-skipped entry for the compare envelope."""
    return {"id": skip.get("id") or skip.get("alpha_id"), "reason": skip.get("reason", "")}


def _zoo_of(reg: Registry, alpha_id: str) -> str:
    """Look up an alpha's owning zoo (best-effort; '' when unknown)."""
    try:
        return reg.get(alpha_id).zoo
    except Exception:  # noqa: BLE001 — unknown id is a normal "skipped" outcome
        return ""


def _zoo_progress_cb(on_progress: ProgressCb | None, base: int, total: int) -> bench_runner.ProgressCb | None:
    """Wrap a global progress callback so a per-zoo bench reports global counts."""
    if on_progress is None:
        return None

    def _cb(n_done: int, _n_total: int, alpha_id: str) -> None:
        try:
            on_progress(base + n_done, total, alpha_id)
        except Exception:  # noqa: BLE001 — progress must never break the loop
            logger.exception("compare on_progress callback raised; ignoring")

    return _cb


def _error_envelope(
    *, error: str, universe: str, period: str, sort: str, skipped: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build the ``status="error"`` envelope with the standard key set."""
    return {
        "status": "error",
        "error": error,
        "universe": universe,
        "period": period,
        "sort": sort,
        "n_compared": 0,
        "n_skipped": len(skipped),
        "ranking": [],
        "skipped": skipped,
    }


def compare_alphas(
    alpha_ids: Iterable[str],
    universe: str,
    period: str,
    *,
    sort: str = "ir",
    registry: Registry | None = None,
    on_progress: ProgressCb | None = None,
) -> dict[str, Any]:
    """Bench a hand-picked set of alphas head-to-head and rank them.

    Args:
        alpha_ids: The alpha ids to compare (>= 2 after de-duplication). Ids not
            found in the registry are reported under ``skipped``, not raised.
        universe: Universe key (``csi300`` / ``sp500`` / ``btc-usdt``).
        period: ``YYYY-YYYY`` or ``YYYY-MM-DD/YYYY-MM-DD`` window.
        sort: Ranking metric — one of :data:`SORT_KEYS` (default ``"ir"``).
            An unrecognised value falls back to ``"ir"``.
        registry: Optional pre-built registry (test injection); defaults to a
            fresh :class:`Registry`.
        on_progress: Optional ``(n_done, n_total, alpha_id)`` callback fired once
            per evaluated alpha, counting across the whole comparison.

    Returns:
        On success, ``status="ok"`` with ``universe``, ``period``, ``sort``,
        ``n_compared``, ``n_skipped``, ``winner``, ``ranking`` (list of
        ``{rank, id, zoo, ic_mean, ic_std, ir, ic_positive_ratio, ic_count,
        delta_<sort>_vs_best}`` sorted best-first) and ``skipped``. On failure
        (fewer than two resolvable ids, or no alpha could be evaluated),
        ``status="error"`` with an ``error`` message and the same key set.
    """
    reg = registry if registry is not None else Registry()
    if sort not in SORT_KEYS:
        sort = "ir"

    # De-duplicate, preserving first-seen order.
    seen: set[str] = set()
    ids = [a for a in alpha_ids if not (a in seen or seen.add(a))]

    if len(ids) < 2:
        return _error_envelope(
            error=f"need at least 2 alphas to compare (got {len(ids)})",
            universe=universe,
            period=period,
            sort=sort,
            skipped=[],
        )

    # Group requested ids by owning zoo; flag unknown ids as skipped.
    by_zoo: dict[str, list[str]] = {}
    skipped: list[dict[str, Any]] = []
    for aid in ids:
        zoo = _zoo_of(reg, aid)
        if zoo:
            by_zoo.setdefault(zoo, []).append(aid)
        else:
            skipped.append({"id": aid, "reason": "unknown alpha id (not in registry)"})

    total = sum(len(v) for v in by_zoo.values())
    rows: list[dict[str, Any]] = []
    base = 0
    for zoo, zids in sorted(by_zoo.items()):
        sub = bench_runner.run_bench(
            zoo=zoo,
            universe=universe,
            period=period,
            top=len(zids),
            only=zids,
            registry=reg,
            on_progress=_zoo_progress_cb(on_progress, base, total),
        )
        if sub.get("status") == "ok":
            for raw in sub.get("rows", []) or []:
                row = dict(raw)
                row.setdefault("zoo", zoo)
                rows.append(row)
            skipped.extend(sub.get("skipped", []) or [])
        else:
            reason = sub.get("error", "bench failed")
            skipped.extend({"id": aid, "reason": reason} for aid in zids)
        base += len(zids)

    skipped = [_normalise_skip(s) for s in skipped]

    if not rows:
        return _error_envelope(
            error="no requested alphas could be evaluated",
            universe=universe,
            period=period,
            sort=sort,
            skipped=skipped,
        )

    rows_sorted = sorted(rows, key=lambda r: _sort_value(r, sort), reverse=True)
    best = _sort_value(rows_sorted[0], sort)
    delta_key = f"delta_{sort}_vs_best"
    ranking = [
        {
            "rank": rank,
            "id": row.get("id"),
            "zoo": row.get("zoo"),
            "ic_mean": row.get("ic_mean", 0.0),
            "ic_std": row.get("ic_std", 0.0),
            "ir": row.get("ir", 0.0),
            "ic_positive_ratio": row.get("ic_positive_ratio", 0.0),
            "ic_count": row.get("ic_count", 0),
            delta_key: round(_sort_value(row, sort) - best, 6),
        }
        for rank, row in enumerate(rows_sorted, start=1)
    ]

    return {
        "status": "ok",
        "universe": universe,
        "period": period,
        "sort": sort,
        "n_compared": len(ranking),
        "n_skipped": len(skipped),
        "winner": ranking[0]["id"],
        "ranking": ranking,
        "skipped": skipped,
    }
