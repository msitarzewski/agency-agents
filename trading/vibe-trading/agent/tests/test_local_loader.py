"""Tests for the config-driven local data loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import backtest.loaders.local_loader as local_loader


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sources: list[dict]) -> None:
    """Point the local loader at a temp config file."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump({"sources": sources}), encoding="utf-8")
    monkeypatch.setattr(local_loader, "_CONFIG_PATH", config_path)


def test_local_loader_fetches_csv_with_local_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Symbols prefixed with local: should resolve to the configured symbol."""
    csv_path = tmp_path / "aapl.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Date,Open,High,Low,Close,Volume",
                "2026-01-01,10,11,9,10.5,1000",
                "2026-01-02,12,13,11,12.5,1500",
            ]
        ),
        encoding="utf-8",
    )
    _configure(
        monkeypatch,
        tmp_path,
        [
            {
                "symbol": "AAPL.US",
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
        ],
    )

    frames = local_loader.DataLoader().fetch(
        ["local:AAPL.US"], "2026-01-01", "2026-01-02"
    )

    assert set(frames) == {"AAPL.US"}
    assert list(frames["AAPL.US"]["close"]) == [10.5, 12.5]


def test_local_loader_fetches_duckdb_without_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DuckDB sources use db_path/query and should not require a path field."""
    duckdb = pytest.importorskip("duckdb")
    db_path = tmp_path / "market.duckdb"
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE prices AS
            SELECT '2026-01-01' AS date, 10.0 AS open, 11.0 AS high,
                   9.0 AS low, 10.5 AS close, 1000.0 AS volume
            UNION ALL
            SELECT '2026-01-02', 12.0, 13.0, 11.0, 12.5, 1500.0
            """
        )
    _configure(
        monkeypatch,
        tmp_path,
        [
            {
                "symbol": "MYINDEX",
                "type": "duckdb",
                "db_path": str(db_path),
                "query": "SELECT * FROM prices",
            }
        ],
    )

    frames = local_loader.DataLoader().fetch(["MYINDEX"], "2026-01-01", "2026-01-02")

    assert set(frames) == {"MYINDEX"}
    assert list(frames["MYINDEX"]["close"]) == [10.5, 12.5]


def test_local_loader_handles_timezone_aware_timestamps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """tz-aware timestamps must not crash the date filter into an empty result.

    Regression: the date-range filter compared a tz-naive Timestamp against a
    tz-aware index, which raised TypeError that was swallowed into empty data.
    """
    csv_path = tmp_path / "tz_aapl.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Date,Open,High,Low,Close,Volume",
                "2026-01-01T00:00:00+00:00,10,11,9,10.5,1000",
                "2026-01-02T00:00:00+00:00,12,13,11,12.5,1500",
            ]
        ),
        encoding="utf-8",
    )
    _configure(
        monkeypatch,
        tmp_path,
        [
            {
                "symbol": "AAPL.US",
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
        ],
    )

    frames = local_loader.DataLoader().fetch(
        ["local:AAPL.US"], "2026-01-01", "2026-01-02"
    )

    assert set(frames) == {"AAPL.US"}
    assert list(frames["AAPL.US"]["close"]) == [10.5, 12.5]
