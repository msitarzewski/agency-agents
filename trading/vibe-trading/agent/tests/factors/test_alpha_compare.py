"""Unit + integration tests for ``vibe-trading alpha compare``.

Two layers are covered:

1. **``run_bench(only=...)`` filter** — the small backward-compatible rail that
   restricts a zoo's IC loop to a named subset, so ``compare`` benches just the
   handful of alphas asked for. Exercised with a registry-injected, panel-stubbed
   integration test (no network — factors tests run socket-disabled).
2. **``cmd_alpha_compare`` handler** — target resolution (ids / ``--all`` /
   ``--zoo``), de-duplication, the ``<2`` guard, cross-zoo grouping, ranking +
   ``delta_*_vs_best`` math, alternate ``--sort`` keys, unknown-id skipping, and
   the all-skipped error envelope. ``run_bench`` and ``Registry`` are stubbed so
   the handler logic is tested in isolation from the bench math.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.factors import cli_handlers, compare_runner
from src.factors.bench_runner import run_bench


# ── run_bench(only=...) integration ─────────────────────────────────────────


class _ThreeAlphaRegistry:
    """Registry stub exposing the slice ``run_bench`` uses, with 3 alphas."""

    def __init__(self) -> None:
        self._ids = ["a_one", "a_two", "a_three"]

    def list(self, *, zoo: str) -> list[str]:  # noqa: ARG002
        return list(self._ids)

    def get(self, aid: str) -> Any:
        class _Handle:
            meta = {"theme": ["test"], "formula_latex": f"stub_{aid}"}

        return _Handle()

    def compute(self, aid: str, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
        # Distinct deterministic frame per alpha so IC series are non-empty.
        close = panel["close"]
        seed = self._ids.index(aid)
        return pd.DataFrame(
            np.random.default_rng(seed).normal(size=close.shape),
            index=close.index,
            columns=close.columns,
        )


def _stub_panel(monkeypatch: pytest.MonkeyPatch, n_rows: int = 80, n_cols: int = 8) -> None:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=n_rows, freq="D")
    cols = [f"S{i}" for i in range(n_cols)]
    close = pd.DataFrame(
        100.0 + np.cumsum(rng.normal(size=(n_rows, n_cols)), axis=0),
        index=idx,
        columns=cols,
    )
    panel = {
        "close": close, "high": close * 1.01, "low": close * 0.99,
        "open": close, "volume": close * 0 + 1_000_000,
        "vwap": close, "amount": close * 1_000_000,
    }
    monkeypatch.setattr(
        "src.factors.bench_runner._load_universe_panel",
        lambda universe, period: panel,  # noqa: ARG005
    )
    monkeypatch.setattr(
        "src.factors.bench_runner._compute_forward_returns",
        lambda panel_in: panel_in["close"].pct_change().shift(-1),
    )


def test_run_bench_only_restricts_to_subset(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_panel(monkeypatch)
    result = run_bench(
        zoo="z", universe="csi300", period="2024-2024",
        only=["a_two", "a_three"], registry=_ThreeAlphaRegistry(),
    )
    assert result["status"] == "ok"
    benched = {r["id"] for r in result["rows"]}
    assert benched == {"a_two", "a_three"}
    assert "a_one" not in benched


def test_run_bench_only_none_benches_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_panel(monkeypatch)
    result = run_bench(
        zoo="z", universe="csi300", period="2024-2024",
        only=None, registry=_ThreeAlphaRegistry(),
    )
    assert {r["id"] for r in result["rows"]} == {"a_one", "a_two", "a_three"}


def test_run_bench_only_unknown_ids_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_panel(monkeypatch)
    result = run_bench(
        zoo="z", universe="csi300", period="2024-2024",
        only=["does_not_exist"], registry=_ThreeAlphaRegistry(),
    )
    assert result["status"] == "error"
    assert "requested alphas" in result["error"]


# ── cmd_alpha_compare handler ───────────────────────────────────────────────


class _FakeRegistry:
    """Maps alpha id → zoo; ``get`` raises for unknown ids (like the real one)."""

    def __init__(self, id_to_zoo: dict[str, str]) -> None:
        self._id_to_zoo = id_to_zoo

    def list(self, zoo: str | None = None, **_kw: Any) -> list[str]:
        ids = sorted(self._id_to_zoo)
        if zoo is not None:
            ids = [i for i in ids if self._id_to_zoo[i] == zoo]
        return ids

    def get(self, aid: str) -> Any:
        if aid not in self._id_to_zoo:
            raise KeyError(aid)
        handle = argparse.Namespace()
        handle.zoo = self._id_to_zoo[aid]
        return handle


def _fake_run_bench(metrics: dict[str, dict[str, Any]], *, status_by_zoo: dict[str, str] | None = None):
    """Build a ``run_bench`` double returning canned rows for the ``only`` ids."""

    def _fake(*, zoo: str, universe: str, period: str, top: int, only: list[str], registry: Any, on_progress: Any = None) -> dict[str, Any]:  # noqa: ARG001
        if status_by_zoo and zoo in status_by_zoo:
            return {"status": "error", "error": status_by_zoo[zoo]}
        rows, skipped = [], []
        for aid in only:
            if aid in metrics:
                rows.append({"id": aid, **metrics[aid]})
            else:
                skipped.append({"id": aid, "reason": "empty IC series"})
        return {"status": "ok", "zoo": zoo, "rows": rows, "skipped": skipped}

    return _fake


def _metrics(ic_mean: float, ic_std: float, ir: float, pos: float = 0.5, n: int = 200) -> dict[str, Any]:
    return {"ic_mean": ic_mean, "ic_std": ic_std, "ir": ir, "ic_positive_ratio": pos, "ic_count": n}


def _args(**kw: Any) -> argparse.Namespace:
    base = {
        "alpha_ids": [], "compare_all": False, "zoo": None,
        "universe": "csi300", "period": "2020-2025", "sort": "ir", "verbose": False,
    }
    base.update(kw)
    return argparse.Namespace(**base)


def _wire(monkeypatch: pytest.MonkeyPatch, id_to_zoo: dict[str, str], fake_bench: Any) -> None:
    monkeypatch.setattr(cli_handlers, "Registry", lambda: _FakeRegistry(id_to_zoo))
    monkeypatch.setattr("src.factors.bench_runner.run_bench", fake_bench)


def _run(capsys: pytest.CaptureFixture[str], args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    rc = cli_handlers.cmd_alpha_compare(args)
    out = capsys.readouterr().out
    return rc, json.loads(out)


def test_compare_ranks_by_ir_descending(monkeypatch, capsys) -> None:
    id_to_zoo = {"alpha101_1": "alpha101", "alpha101_2": "alpha101", "alpha101_3": "alpha101"}
    metrics = {
        "alpha101_1": _metrics(0.01, 0.05, 0.20),
        "alpha101_2": _metrics(0.03, 0.05, 0.60),  # best IR
        "alpha101_3": _metrics(0.02, 0.05, 0.40),
    }
    _wire(monkeypatch, id_to_zoo, _fake_run_bench(metrics))
    rc, env = _run(capsys, _args(alpha_ids=["alpha101_1", "alpha101_2", "alpha101_3"]))

    assert rc == 0
    assert env["status"] == "ok"
    assert env["sort"] == "ir"
    assert [r["id"] for r in env["ranking"]] == ["alpha101_2", "alpha101_3", "alpha101_1"]
    assert env["winner"] == "alpha101_2"
    assert env["ranking"][0]["delta_ir_vs_best"] == 0.0
    assert env["ranking"][1]["delta_ir_vs_best"] == pytest.approx(-0.20)
    assert env["ranking"][2]["delta_ir_vs_best"] == pytest.approx(-0.40)
    assert env["n_compared"] == 3
    assert env["n_skipped"] == 0


def test_compare_alternate_sort_key_reorders(monkeypatch, capsys) -> None:
    id_to_zoo = {"a": "alpha101", "b": "alpha101"}
    # b wins on IR but a wins on ic_mean — sorting by ic_mean flips the winner.
    metrics = {"a": _metrics(0.09, 0.05, 0.20), "b": _metrics(0.04, 0.05, 0.80)}
    _wire(monkeypatch, id_to_zoo, _fake_run_bench(metrics))
    rc, env = _run(capsys, _args(alpha_ids=["a", "b"], sort="ic_mean"))

    assert rc == 0
    assert env["sort"] == "ic_mean"
    assert env["winner"] == "a"
    assert "delta_ic_mean_vs_best" in env["ranking"][0]
    assert env["ranking"][1]["delta_ic_mean_vs_best"] == pytest.approx(-0.05)


def test_compare_groups_across_zoos(monkeypatch, capsys) -> None:
    id_to_zoo = {"alpha101_1": "alpha101", "gtja191_5": "gtja191"}
    metrics = {"alpha101_1": _metrics(0.02, 0.05, 0.40), "gtja191_5": _metrics(0.03, 0.05, 0.60)}

    calls: list[tuple[str, tuple[str, ...]]] = []

    fake = _fake_run_bench(metrics)

    def _tracking(*, zoo, universe, period, top, only, registry, on_progress=None):  # noqa: ANN001, ARG001
        calls.append((zoo, tuple(only)))
        return fake(
            zoo=zoo, universe=universe, period=period, top=top, only=only,
            registry=registry, on_progress=on_progress,
        )

    _wire(monkeypatch, id_to_zoo, _tracking)
    rc, env = _run(capsys, _args(alpha_ids=["alpha101_1", "gtja191_5"]))

    assert rc == 0
    # One run_bench call per zoo, each scoped to its own ids.
    assert sorted(calls) == [("alpha101", ("alpha101_1",)), ("gtja191", ("gtja191_5",))]
    assert {r["id"] for r in env["ranking"]} == {"alpha101_1", "gtja191_5"}
    assert env["winner"] == "gtja191_5"


def test_compare_unknown_id_is_skipped(monkeypatch, capsys) -> None:
    id_to_zoo = {"known_1": "alpha101", "known_2": "alpha101"}
    metrics = {"known_1": _metrics(0.02, 0.05, 0.40), "known_2": _metrics(0.03, 0.05, 0.60)}
    _wire(monkeypatch, id_to_zoo, _fake_run_bench(metrics))
    rc, env = _run(capsys, _args(alpha_ids=["known_1", "known_2", "ghost_9"]))

    assert rc == 0
    assert {r["id"] for r in env["ranking"]} == {"known_1", "known_2"}
    skipped_ids = {s["id"] for s in env["skipped"]}
    assert "ghost_9" in skipped_ids
    assert env["n_skipped"] == 1


def test_compare_dedupes_repeated_ids(monkeypatch, capsys) -> None:
    id_to_zoo = {"a": "alpha101", "b": "alpha101"}
    metrics = {"a": _metrics(0.02, 0.05, 0.40), "b": _metrics(0.03, 0.05, 0.60)}
    _wire(monkeypatch, id_to_zoo, _fake_run_bench(metrics))
    rc, env = _run(capsys, _args(alpha_ids=["a", "b", "a", "b"]))

    assert rc == 0
    assert env["n_compared"] == 2


def test_compare_requires_at_least_two(monkeypatch, capsys) -> None:
    _wire(monkeypatch, {"solo": "alpha101"}, _fake_run_bench({"solo": _metrics(0.02, 0.05, 0.40)}))
    rc = cli_handlers.cmd_alpha_compare(_args(alpha_ids=["solo"]))
    assert rc == 1


def test_compare_no_targets_errors(monkeypatch, capsys) -> None:
    _wire(monkeypatch, {}, _fake_run_bench({}))
    rc = cli_handlers.cmd_alpha_compare(_args(alpha_ids=[]))
    assert rc == 1


def test_compare_all_evaluations_skipped_errors(monkeypatch, capsys) -> None:
    id_to_zoo = {"a": "alpha101", "b": "alpha101"}
    # Bench fails for the whole zoo → both ids end up skipped, no rows.
    fake = _fake_run_bench({}, status_by_zoo={"alpha101": "universe load failed: no token"})
    _wire(monkeypatch, id_to_zoo, fake)
    rc, env = _run(capsys, _args(alpha_ids=["a", "b"]))

    assert rc == 1
    assert env["status"] == "error"
    assert env["n_skipped"] if "n_skipped" in env else True
    assert {s["id"] for s in env["skipped"]} == {"a", "b"}


def test_compare_all_flag_resolves_every_alpha(monkeypatch, capsys) -> None:
    id_to_zoo = {"a": "alpha101", "b": "gtja191"}
    metrics = {"a": _metrics(0.02, 0.05, 0.40), "b": _metrics(0.03, 0.05, 0.60)}
    _wire(monkeypatch, id_to_zoo, _fake_run_bench(metrics))
    rc, env = _run(capsys, _args(compare_all=True))

    assert rc == 0
    assert env["n_compared"] == 2


def test_compare_zoo_flag_filters_targets(monkeypatch, capsys) -> None:
    id_to_zoo = {"a": "alpha101", "b": "alpha101", "c": "gtja191"}
    metrics = {k: _metrics(0.02, 0.05, 0.40 + i * 0.1) for i, k in enumerate(["a", "b", "c"])}
    _wire(monkeypatch, id_to_zoo, _fake_run_bench(metrics))
    rc, env = _run(capsys, _args(zoo="alpha101"))

    assert rc == 0
    assert {r["id"] for r in env["ranking"]} == {"a", "b"}  # c (gtja191) excluded


# ── compare_runner.compare_alphas core (direct) ─────────────────────────────


def test_core_progress_counts_globally_across_zoos(monkeypatch) -> None:
    id_to_zoo = {"a": "alpha101", "b": "alpha101", "c": "gtja191"}
    metrics = {k: _metrics(0.02, 0.05, 0.40) for k in id_to_zoo}

    def _fake(*, zoo, universe, period, top, only, registry, on_progress=None):  # noqa: ANN001, ARG001
        rows = []
        for i, aid in enumerate(only, start=1):
            rows.append({"id": aid, **metrics[aid]})
            if on_progress is not None:
                on_progress(i, len(only), aid)  # per-zoo local count
        return {"status": "ok", "zoo": zoo, "rows": rows, "skipped": []}

    monkeypatch.setattr("src.factors.bench_runner.run_bench", _fake)
    seen: list[tuple[int, int, str]] = []
    env = compare_runner.compare_alphas(
        ["a", "b", "c"], "csi300", "2020-2025", sort="ir",
        registry=_FakeRegistry(id_to_zoo),
        on_progress=lambda nd, nt, aid: seen.append((nd, nt, aid)),
    )
    assert env["status"] == "ok"
    # alpha101 (a,b) base 0 → 1,2 ; gtja191 (c) base 2 → 3 — global & monotonic.
    assert [nd for nd, _, _ in seen] == [1, 2, 3]
    assert {nt for _, nt, _ in seen} == {3}  # total is the whole comparison, not per-zoo


def test_core_below_two_returns_error(monkeypatch) -> None:
    env = compare_runner.compare_alphas(
        ["solo"], "csi300", "2020-2025", registry=_FakeRegistry({"solo": "alpha101"}),
    )
    assert env["status"] == "error"
    assert "at least 2" in env["error"]
    assert env["ranking"] == []


def test_core_invalid_sort_falls_back_to_ir(monkeypatch) -> None:
    id_to_zoo = {"a": "alpha101", "b": "alpha101"}
    metrics = {"a": _metrics(0.01, 0.05, 0.20), "b": _metrics(0.03, 0.05, 0.60)}
    monkeypatch.setattr("src.factors.bench_runner.run_bench", _fake_run_bench(metrics))
    env = compare_runner.compare_alphas(
        ["a", "b"], "csi300", "2020-2025", sort="bogus", registry=_FakeRegistry(id_to_zoo),
    )
    assert env["sort"] == "ir"
    assert env["winner"] == "b"
