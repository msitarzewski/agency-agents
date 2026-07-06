"""Tests for the shared OHLC invariant validator and its loader wiring."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pytest

import backtest.loaders.local_loader as local_loader
from backtest.loaders.base import validate_ohlc


def _frame(rows: list[tuple[float, float, float, float, float]]) -> pd.DataFrame:
    """Build an OHLCV frame from (open, high, low, close, volume) rows."""
    index = pd.date_range("2026-01-01", periods=len(rows), freq="D", name="trade_date")
    return pd.DataFrame(
        rows, columns=["open", "high", "low", "close", "volume"], index=index
    )


def test_validate_ohlc_drops_invariant_violations() -> None:
    """high<low, prices<=0, and high/low not bracketing open/close are dropped."""
    frame = _frame(
        [
            (10.0, 11.0, 9.0, 10.5, 1000.0),   # valid
            (10.0, 8.0, 9.0, 10.5, 1000.0),    # high < low -> invalid
            (-1.0, 11.0, 9.0, 10.5, 1000.0),   # non-positive open -> invalid
            (10.0, 10.5, 9.0, 12.0, 1000.0),   # close > high -> invalid
            (10.0, 10.0, 10.0, 10.0, 0.0),     # flat doji, zero volume -> valid
        ]
    )

    cleaned = validate_ohlc(frame)

    assert list(cleaned["close"]) == [10.5, 10.0]
    assert len(cleaned) == 2


def test_validate_ohlc_raise_strategy() -> None:
    """strategy='raise' surfaces the violation instead of silently dropping."""
    frame = _frame([(10.0, 8.0, 9.0, 10.5, 1000.0)])
    with pytest.raises(ValueError):
        validate_ohlc(frame, strategy="raise")


def test_validate_ohlc_warn_strategy_keeps_rows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """strategy='warn' logs but keeps the offending rows."""
    frame = _frame([(10.0, 11.0, 9.0, 10.5, 1000.0), (10.0, 8.0, 9.0, 10.5, 1000.0)])
    with caplog.at_level(logging.WARNING, logger="backtest.loaders.base"):
        kept = validate_ohlc(frame, strategy="warn")
    assert len(kept) == 2
    assert any("ohlc" in rec.message.lower() for rec in caplog.records)


def test_validate_ohlc_passthrough_when_no_ohlc_columns() -> None:
    """A frame without OHLC columns (or empty) is returned unchanged."""
    empty = pd.DataFrame()
    assert validate_ohlc(empty).empty
    other = pd.DataFrame({"value": [1, 2, 3]})
    assert validate_ohlc(other).equals(other)


def test_local_loader_drops_dirty_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A structurally invalid bar in a local file must not reach the backtest."""
    csv_path = tmp_path / "dirty.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Date,Open,High,Low,Close,Volume",
                "2026-01-01,10,11,9,10.5,1000",
                "2026-01-02,10,8,9,10.5,1500",  # high < low -> dirty
                "2026-01-03,12,13,11,12.5,1200",
            ]
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.yaml"
    import yaml

    config_path.write_text(
        yaml.safe_dump(
            {
                "sources": [
                    {
                        "symbol": "AAA.US",
                        "type": "csv",
                        "path": str(csv_path),
                        "columns": {
                            "date": "Date",
                            "open": "Open",
                            "high": "High",
                            "low": "Low",
                            "close": "Close",
                            "volume": "Volume",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(local_loader, "_CONFIG_PATH", config_path)

    frames = local_loader.DataLoader().fetch(["AAA.US"], "2026-01-01", "2026-01-03")

    df = frames["AAA.US"]
    assert list(df["close"]) == [10.5, 12.5]  # the dirty 2026-01-02 bar is gone


def test_sanitize_data_map_guards_every_source() -> None:
    """The runner's central pass drops dirty bars from any loader's frame.

    This is the catch-all boundary: a loader that never calls ``validate_ohlc``
    itself (the large majority) still cannot leak a structurally-invalid bar
    into the backtest, because every fetched map converges through here.
    """
    from backtest.runner import _sanitize_data_map

    data_map = {
        "AAA.US": _frame(
            [
                (10.0, 11.0, 9.0, 10.5, 1000.0),  # valid
                (10.0, 8.0, 9.0, 10.5, 1500.0),   # high < low -> dropped
            ]
        ),
        "BBB.US": _frame([(12.0, 13.0, 11.0, 12.5, 1200.0)]),  # all valid
    }

    cleaned = _sanitize_data_map(data_map)

    assert list(cleaned["AAA.US"]["close"]) == [10.5]  # dirty bar gone
    assert list(cleaned["BBB.US"]["close"]) == [12.5]  # untouched
    assert set(cleaned) == {"AAA.US", "BBB.US"}
