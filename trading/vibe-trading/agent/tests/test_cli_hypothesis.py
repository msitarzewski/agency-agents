"""Tests for the ``vibe-trading hypothesis`` CLI subcommands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from src.hypotheses import HypothesisRegistry
from src.hypotheses.cli_handlers import (
    add_subparser,
    dispatch,
)


def _make_registry(tmp_path: Path) -> tuple[HypothesisRegistry, Path]:
    storage = tmp_path / "hypotheses.json"
    return HypothesisRegistry(path=storage), storage


def _seed(reg: HypothesisRegistry) -> list[str]:
    """Seed three hypotheses spanning multiple statuses; return their ids."""
    a = reg.create(
        title="Mean-reversion on CSI300",
        thesis="Short-horizon dispersion → reversion edge.",
        universe="csi300",
        data_sources=["tushare"],
        skills=["factor-research"],
    )
    b = reg.create(
        title="Earnings drift on US large caps",
        thesis="Post-earnings drift in SPY components.",
        status="testing",
        universe="sp500",
    )
    c = reg.create(
        title="BTC funding skew",
        thesis="Perp funding extremes mean-revert.",
        status="validated",
        universe="btc-usdt",
    )
    return [a.hypothesis_id, b.hypothesis_id, c.hypothesis_id]


def _build_args(**kwargs: object) -> argparse.Namespace:
    """Build a Namespace pre-populated with sane defaults that ``_registry``
    and handlers expect to read."""
    defaults: dict[str, object] = {
        "path": None,
        "verbose": False,
        "json": False,
        "status": None,
        "limit": 50,
        "note": "",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestParserWiring:
    def test_subparser_registers_three_commands(self) -> None:
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        hyp_parser = add_subparser(sub)
        # Parse each subcommand to confirm wiring.
        for sub_cmd in ("list", "show", "invalidate"):
            assert hyp_parser is not None
        args = parser.parse_args(["hypothesis", "list", "--status", "rejected"])
        assert args.hypothesis_command == "list"
        assert args.status == "rejected"
        args = parser.parse_args(["hypothesis", "show", "hyp_xyz"])
        assert args.hypothesis_command == "show"
        assert args.hypothesis_id == "hyp_xyz"
        args = parser.parse_args(
            ["hypothesis", "invalidate", "hyp_xyz", "--note", "data leak"]
        )
        assert args.hypothesis_command == "invalidate"
        assert args.note == "data leak"

    def test_dispatch_without_subcommand_returns_one(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        args = _build_args(path=str(tmp_path / "h.json"), hypothesis_command=None)
        assert dispatch(args) == 1


class TestList:
    def test_empty_registry(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        args = _build_args(
            path=str(tmp_path / "h.json"), hypothesis_command="list"
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "No hypotheses found" in out

    def test_lists_all(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(path=str(storage), hypothesis_command="list")
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "Mean-reversion on CSI300" in out
        assert "Earnings drift on US large caps" in out
        assert "BTC funding skew" in out

    def test_status_filter(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(
            path=str(storage), hypothesis_command="list", status="validated"
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "BTC funding skew" in out
        assert "Earnings drift" not in out
        assert "Mean-reversion" not in out

    def test_status_filter_with_no_matches(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(
            path=str(storage), hypothesis_command="list", status="rejected"
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert "No hypotheses found status=rejected" in out

    def test_limit(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(path=str(storage), hypothesis_command="list", limit=1)
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        # Exactly one of the three seeded titles is shown; which one wins
        # depends on updated_at order, which can tie at second resolution.
        seeded_titles = (
            "Mean-reversion on CSI300",
            "Earnings drift on US large caps",
            "BTC funding skew",
        )
        shown = [t for t in seeded_titles if t in out]
        assert len(shown) == 1, f"expected exactly one row, got {shown}"
        assert "Hypotheses (1)" in out

    def test_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(
            path=str(storage), hypothesis_command="list", json=True
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        payload = json.loads(out)
        assert isinstance(payload, list)
        assert len(payload) == 3
        titles = {item["title"] for item in payload}
        assert "Mean-reversion on CSI300" in titles


class TestShow:
    def test_shows_existing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        ids = _seed(reg)
        args = _build_args(
            path=str(storage),
            hypothesis_command="show",
            hypothesis_id=ids[0],
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert ids[0] in out
        assert "Mean-reversion on CSI300" in out
        assert "Short-horizon dispersion" in out

    def test_missing_returns_one(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(
            path=str(storage),
            hypothesis_command="show",
            hypothesis_id="hyp_does_not_exist",
        )
        rc = dispatch(args)
        captured = capsys.readouterr()
        assert rc == 1
        assert "hypothesis not found" in captured.err

    def test_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        ids = _seed(reg)
        args = _build_args(
            path=str(storage),
            hypothesis_command="show",
            hypothesis_id=ids[1],
            json=True,
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        payload = json.loads(out)
        assert payload["hypothesis_id"] == ids[1]
        assert payload["status"] == "testing"


class TestInvalidate:
    def test_invalidates_with_note(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        ids = _seed(reg)
        args = _build_args(
            path=str(storage),
            hypothesis_command="invalidate",
            hypothesis_id=ids[0],
            note="Data leakage in feature set.",
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        assert ids[0] in out

        # Reload and verify persisted state.
        reg2 = HypothesisRegistry(path=storage)
        hyp = next(h for h in reg2.list() if h.hypothesis_id == ids[0])
        assert hyp.status == "rejected"
        assert hyp.invalidation_notes == "Data leakage in feature set."

    def test_invalidates_without_note_leaves_existing_note(
        self, tmp_path: Path
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        hyp = reg.create(
            title="Old idea",
            thesis="Stale thesis.",
            invalidation_notes="Original note.",
        )
        args = _build_args(
            path=str(storage),
            hypothesis_command="invalidate",
            hypothesis_id=hyp.hypothesis_id,
            note="",
        )
        rc = dispatch(args)
        assert rc == 0
        reg2 = HypothesisRegistry(path=storage)
        loaded = next(
            h for h in reg2.list() if h.hypothesis_id == hyp.hypothesis_id
        )
        assert loaded.status == "rejected"
        assert loaded.invalidation_notes == "Original note."

    def test_missing_returns_one(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        _seed(reg)
        args = _build_args(
            path=str(storage),
            hypothesis_command="invalidate",
            hypothesis_id="hyp_missing",
            note="",
        )
        rc = dispatch(args)
        captured = capsys.readouterr()
        assert rc == 1
        assert "hypothesis not found" in captured.err

    def test_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg, storage = _make_registry(tmp_path)
        ids = _seed(reg)
        args = _build_args(
            path=str(storage),
            hypothesis_command="invalidate",
            hypothesis_id=ids[2],
            note="Funding skew anomaly disappeared.",
            json=True,
        )
        rc = dispatch(args)
        out = capsys.readouterr().out
        assert rc == 0
        payload = json.loads(out)
        assert payload["hypothesis_id"] == ids[2]
        assert payload["status"] == "rejected"
        assert payload["invalidation_notes"] == (
            "Funding skew anomaly disappeared."
        )
