"""Tests for the ``alpha_compare`` agent tool.

Covers id coercion, the tool's JSON-Schema contract, ``execute`` happy/error
paths (with ``compare_alphas`` stubbed so no bench/network runs), and that the
tool is auto-discovered into the default registry.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from src.tools import build_registry
from src.tools.alpha_compare_tool import AlphaCompareTool, _coerce_ids


# ── _coerce_ids ─────────────────────────────────────────────────────────────


def test_coerce_ids_passes_through_list() -> None:
    assert _coerce_ids(["a", "b", "c"]) == ["a", "b", "c"]


def test_coerce_ids_splits_string_on_commas_and_spaces() -> None:
    assert _coerce_ids("a, b   c,d") == ["a", "b", "c", "d"]


def test_coerce_ids_dedupes_preserving_order() -> None:
    assert _coerce_ids(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_coerce_ids_handles_none_and_blanks() -> None:
    assert _coerce_ids(None) == []
    assert _coerce_ids(["", "  ", "x"]) == ["x"]


# ── tool contract ───────────────────────────────────────────────────────────


def test_tool_metadata() -> None:
    tool = AlphaCompareTool()
    assert tool.name == "alpha_compare"
    assert tool.is_readonly is True
    assert tool.repeatable is True
    assert tool.parameters["required"] == ["alpha_ids", "universe", "period"]
    assert tool.parameters["properties"]["sort"]["enum"] == [
        "ir", "ic_mean", "ic_positive_ratio", "ic_count",
    ]


def test_tool_is_auto_discovered() -> None:
    registry = build_registry()
    assert "alpha_compare" in registry.tool_names


# ── execute ─────────────────────────────────────────────────────────────────


def _ok_envelope() -> dict[str, Any]:
    return {
        "status": "ok", "universe": "csi300", "period": "2020-2025", "sort": "ir",
        "n_compared": 2, "n_skipped": 0, "winner": "alpha101_2",
        "ranking": [
            {"rank": 1, "id": "alpha101_2", "zoo": "alpha101", "ir": 0.6, "delta_ir_vs_best": 0.0},
            {"rank": 2, "id": "alpha101_1", "zoo": "alpha101", "ir": 0.2, "delta_ir_vs_best": -0.4},
        ],
        "skipped": [],
    }


def test_execute_happy_path(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake(alpha_ids, universe, period, *, sort="ir", **_kw):  # noqa: ANN001
        captured.update(alpha_ids=alpha_ids, universe=universe, period=period, sort=sort)
        return _ok_envelope()

    monkeypatch.setattr("src.tools.alpha_compare_tool.compare_alphas", _fake)
    out = AlphaCompareTool().execute(
        alpha_ids=["alpha101_1", "alpha101_2", "alpha101_1"],  # dup collapses
        universe="csi300", period="2020-2025", sort="ir",
    )
    env = json.loads(out)
    assert env["status"] == "ok"
    assert env["winner"] == "alpha101_2"
    # ids were coerced/deduped before reaching the core.
    assert captured["alpha_ids"] == ["alpha101_1", "alpha101_2"]
    assert captured["sort"] == "ir"


def test_execute_accepts_inline_string_ids(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.tools.alpha_compare_tool.compare_alphas",
        lambda alpha_ids, *a, **k: {"status": "ok", "n_compared": len(alpha_ids),
                                    "winner": alpha_ids[0], "ranking": [], "skipped": []},
    )
    env = json.loads(AlphaCompareTool().execute(
        alpha_ids="alpha101_1, alpha101_2", universe="csi300", period="2020-2025",
    ))
    assert env["status"] == "ok"
    assert env["n_compared"] == 2


def test_execute_missing_universe_is_error(monkeypatch) -> None:
    # compare_alphas must not even be called when required args are absent.
    monkeypatch.setattr(
        "src.tools.alpha_compare_tool.compare_alphas",
        lambda *a, **k: pytest.fail("compare_alphas should not run without universe"),
    )
    env = json.loads(AlphaCompareTool().execute(
        alpha_ids=["a", "b"], universe="", period="2020-2025",
    ))
    assert env["status"] == "error"
    assert "universe and period" in env["error"]


def test_execute_wraps_unexpected_exception(monkeypatch) -> None:
    def _boom(*_a: Any, **_k: Any):
        raise RuntimeError("kaboom")

    monkeypatch.setattr("src.tools.alpha_compare_tool.compare_alphas", _boom)
    env = json.loads(AlphaCompareTool().execute(
        alpha_ids=["a", "b"], universe="csi300", period="2020-2025",
    ))
    assert env["status"] == "error"
    assert "alpha compare failed" in env["error"]
