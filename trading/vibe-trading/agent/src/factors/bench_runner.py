"""Bench runner: compute IC stats for every alpha in a zoo over one universe.

Extracted from ``agent/scripts/w4a_run_benches.py`` so the same pipeline can be
called by:

- the CLI bench driver (``w4a_run_benches.py``)
- the Web UI background worker (``src/api/alpha_routes.py``)

The math is unchanged — only the carrier moved. Categorisation thresholds:

- ``alive``     : ic_mean > 0.02 and ic_positive_ratio >= 0.55 and |t| > 2
- ``reversed``  : ic_mean < -0.02 and |t| > 2
- ``dead``      : everything else
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Callable, Iterable

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


def t_stat(ic_mean: float, ic_std: float, n: int) -> float:
    """Two-sided t-statistic of the IC series."""
    if not (n > 0 and ic_std > 0 and math.isfinite(ic_std)):
        return 0.0
    return ic_mean / (ic_std / math.sqrt(n))


def categorise(row: dict[str, Any]) -> str:
    """Bucket a per-alpha row into alive / reversed / dead."""
    ic_mean = row["ic_mean"]
    pos = row["ic_positive_ratio"]
    t = t_stat(ic_mean, row["ic_std"], row["ic_count"])
    if ic_mean > 0.02 and pos >= 0.55 and abs(t) > 2:
        return "alive"
    if ic_mean < -0.02 and abs(t) > 2:
        return "reversed"
    return "dead"


def theme_breakdown(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Aggregate alive/reversed/dead counts by theme tag."""
    by_theme: dict[str, dict[str, int]] = {}
    for row in rows:
        cat = row["_category"]
        themes = row.get("theme", []) or ["uncategorised"]
        for theme in themes:
            bucket = by_theme.setdefault(
                theme, {"alive": 0, "reversed": 0, "dead": 0, "count": 0}
            )
            bucket[cat] += 1
            bucket["count"] += 1
    return by_theme


def run_bench(
    zoo: str,
    universe: str,
    period: str,
    top: int = 20,
    on_progress: ProgressCb | None = None,
    registry: Registry | None = None,
    only: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Run a bench end-to-end and return the API-shaped summary.

    Args:
        zoo: Zoo id (e.g. ``gtja191``, ``alpha101``, ``qlib158``).
        universe: Universe key understood by ``_load_universe_panel``
            (e.g. ``csi300``, ``sp500``, ``btc-usdt``).
        period: ``YYYY-YYYY`` or ``YYYY-MM-DD/YYYY-MM-DD`` window.
        top: Number of top-IR alphas to keep in ``top5_by_ir`` and
            ``dead_examples`` (capped at ``top``).
        on_progress: Optional callback fired after every alpha completes
            (success or skip). Signature: ``(n_done, n_total, alpha_id)``.
        registry: Optional pre-built registry (test injection); defaults to a
            fresh ``Registry()``.
        only: Optional subset of alpha ids to evaluate. When provided, the zoo's
            alpha list is restricted to this set — used by ``alpha compare`` to
            bench just a handful of named alphas instead of the whole zoo. Ids
            not registered under ``zoo`` are silently dropped from the subset.

    Returns:
        Dict with keys: ``status``, ``zoo``, ``universe``, ``period``,
        ``n_alphas_tested``, ``n_skipped``, ``alive``, ``reversed``, ``dead``,
        ``by_theme``, ``top5_by_ir``, ``dead_examples``, ``wall_seconds`` —
        and on failure: ``status="error"``, ``error``.
    """
    start = time.monotonic()
    entry: dict[str, Any] = {
        "status": "pending",
        "zoo": zoo,
        "universe": universe,
        "period": period,
    }

    reg = registry if registry is not None else get_default_registry()
    alpha_ids = reg.list(zoo=zoo)
    if not alpha_ids:
        entry["status"] = "error"
        entry["error"] = f"no alphas registered under zoo={zoo!r}"
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    if only is not None:
        only_set = {str(aid) for aid in only}
        alpha_ids = [aid for aid in alpha_ids if aid in only_set]
        if not alpha_ids:
            entry["status"] = "error"
            entry["error"] = f"none of the requested alphas are registered under zoo={zoo!r}"
            entry["wall_seconds"] = round(time.monotonic() - start, 2)
            return entry

    try:
        panel = _load_universe_panel(universe, period)
    except (ValueError, NotImplementedError, RuntimeError) as exc:
        entry["status"] = "error"
        entry["error"] = f"universe load failed: {exc}"
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    try:
        return_df = _compute_forward_returns(panel)
    except Exception as exc:  # noqa: BLE001
        entry["status"] = "error"
        entry["error"] = f"forward returns failed: {exc}"
        entry["wall_seconds"] = round(time.monotonic() - start, 2)
        return entry

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    n_total = len(alpha_ids)
    for idx, aid in enumerate(alpha_ids, start=1):
        try:
            factor_df = reg.compute(aid, panel)
            ic = compute_ic_series(factor_df, return_df)
            if ic.empty:
                skipped.append(
                    {"id": aid, "reason": "empty IC series", "kind": "typed"}
                )
            else:
                ic_mean = float(ic.mean())
                ic_std = float(ic.std())
                ir = ic_mean / ic_std if ic_std > 0 else 0.0
                meta = reg.get(aid).meta or {}
                rows.append(
                    {
                        "id": aid,
                        "ic_mean": round(ic_mean, 6),
                        "ic_std": round(ic_std, 6),
                        "ir": round(ir, 4),
                        "ic_positive_ratio": round(float((ic > 0).mean()), 4),
                        "ic_count": int(len(ic)),
                        "theme": meta.get("theme", []),
                        "formula_latex": meta.get("formula_latex", ""),
                    }
                )
        except (SkipAlpha, RegistryError, RuntimeError, KeyError, ValueError) as exc:
            skipped.append({"id": aid, "reason": str(exc), "kind": "typed"})
        except Exception as exc:  # noqa: BLE001
            logger.exception("bench: unexpected failure on %s", aid)
            skipped.append(
                {"id": aid, "reason": f"unexpected: {exc}", "kind": "unexpected"}
            )

        if on_progress is not None:
            try:
                on_progress(idx, n_total, aid)
            except Exception:  # noqa: BLE001 — never let progress break the loop
                logger.exception("on_progress callback raised; ignoring")

    for row in rows:
        row["_category"] = categorise(row)

    counts = {"alive": 0, "reversed": 0, "dead": 0}
    for row in rows:
        counts[row["_category"]] += 1

    rows_by_ir = sorted(rows, key=lambda r: r["ir"], reverse=True)
    rows_by_ic = sorted(rows, key=lambda r: r["ic_mean"])

    def _slim(r: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": r["id"],
            "ic_mean": r["ic_mean"],
            "ir": r["ir"],
            "theme": r["theme"],
            "formula_latex": r["formula_latex"],
            "category": r["_category"],
        }

    # Forward universe metadata (e.g. survivorship_bias flag from sp500
    # loader). Panel meta lives in panel["_meta"] when the loader chooses to
    # set it; absence is fine.
    universe_meta_raw = panel.get("_meta") if isinstance(panel, dict) else None
    universe_meta: dict[str, Any] = {}
    if universe_meta_raw is not None:
        try:
            # Could be a pandas object or a plain dict.
            if hasattr(universe_meta_raw, "to_dict"):
                universe_meta = dict(universe_meta_raw.to_dict())
            else:
                universe_meta = dict(universe_meta_raw)
        except Exception:  # noqa: BLE001
            universe_meta = {"raw": str(universe_meta_raw)}

    entry.update(
        {
            "status": "ok",
            "n_alphas_tested": len(rows),
            "n_skipped": len(skipped),
            "alive": counts["alive"],
            "reversed": counts["reversed"],
            "dead": counts["dead"],
            "by_theme": theme_breakdown(rows),
            "top5_by_ir": [_slim(r) for r in rows_by_ir[: min(5, top)]],
            "dead_examples": [_slim(r) for r in rows_by_ic[:5]],
            "rows": rows,
            "skipped": skipped,
            "meta": universe_meta,
            "wall_seconds": round(time.monotonic() - start, 2),
        }
    )
    return entry
