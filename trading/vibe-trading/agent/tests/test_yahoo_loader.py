"""Tests for yahoo_loader: symbol gating, epoch window, frame normalization.

All network access is mocked at the loader's ``yahoo_client.get_chart`` import
site, so no test ever reaches a live Yahoo endpoint.
"""
from __future__ import annotations

import datetime as dt
from unittest.mock import patch

import pandas as pd

from backtest.loaders.yahoo_loader import (
    DataLoader,
    _epoch_seconds,
    _is_intraday_interval,
    _is_us_or_hk,
    _rows_to_frame,
    _to_yahoo_interval,
)


def _epoch(date_str: str) -> int:
    """UTC-midnight epoch seconds for a date, used to build fake chart rows."""
    day = pd.Timestamp(date_str).date()
    return int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())


def _open_epoch(date_str: str) -> int:
    """Epoch seconds at 14:30 UTC (US market open) on *date_str*.

    Mirrors how Yahoo actually stamps daily bars: at the session open, not at
    midnight. Used to prove daily bars are normalized back to 00:00:00.
    """
    return _epoch(date_str) + 14 * 3600 + 30 * 60


def _row(date_str: str, open_, high, low, close, volume):
    return {
        "trade_date": _epoch(date_str),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def _intraday_stamped_row(date_str: str, open_, high, low, close, volume):
    """A daily bar carrying Yahoo's real session-open epoch (14:30 UTC)."""
    row = _row(date_str, open_, high, low, close, volume)
    row["trade_date"] = _open_epoch(date_str)
    return row


class TestSymbolGating:
    """_is_us_or_hk only accepts US/HK suffixes."""

    def test_accepts_us(self):
        assert _is_us_or_hk("AAPL.US") is True
        assert _is_us_or_hk("aapl.us") is True

    def test_accepts_hk(self):
        assert _is_us_or_hk("00700.HK") is True
        assert _is_us_or_hk("00700.hk") is True

    def test_rejects_others(self):
        assert _is_us_or_hk("601398.SH") is False
        assert _is_us_or_hk("BTC-USDT") is False
        assert _is_us_or_hk("") is False


class TestIntervalMap:
    """_to_yahoo_interval maps project intervals to Yahoo's strings."""

    def test_daily(self):
        assert _to_yahoo_interval("1D") == "1d"

    def test_hourly(self):
        assert _to_yahoo_interval("1H") == "1h"

    def test_unknown_lowercased(self):
        assert _to_yahoo_interval("5m") == "5m"

    def test_empty_defaults_daily(self):
        assert _to_yahoo_interval("") == "1d"


class TestIsIntradayInterval:
    """_is_intraday_interval splits minute/hour from day/week/month."""

    def test_daily_is_not_intraday(self):
        assert _is_intraday_interval("1D") is False
        assert _is_intraday_interval("1d") is False

    def test_weekly_monthly_not_intraday(self):
        assert _is_intraday_interval("1W") is False
        assert _is_intraday_interval("1M") is False
        assert _is_intraday_interval("1mo") is False

    def test_minute_and_hour_are_intraday(self):
        assert _is_intraday_interval("1H") is True
        assert _is_intraday_interval("5m") is True
        assert _is_intraday_interval("15min") is True

    def test_empty_defaults_daily(self):
        assert _is_intraday_interval("") is False


class TestDailyIndexNormalization:
    """Daily-and-coarser bars normalize to midnight; intraday keep their time.

    Regression for B1-yahoo-ts: Yahoo stamps daily bars at the US session-open
    epoch (14:30 UTC). Left unnormalized that intraday time broke fallback
    merge/join/dedup against other loaders' midnight-indexed daily bars.
    """

    def test_daily_bars_indexed_at_midnight(self):
        rows = [
            _intraday_stamped_row("2024-01-02", 10, 11, 9, 10.5, 1000),
            _intraday_stamped_row("2024-01-03", 10.5, 12, 10, 11.5, 2000),
        ]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31", "1D")
        assert len(df) == 2
        for ts in df.index:
            assert ts.hour == 0 and ts.minute == 0 and ts.second == 0
            assert ts == ts.normalize()

    def test_daily_index_matches_other_sources_date_index(self):
        rows = [
            _intraday_stamped_row("2024-01-02", 10, 11, 9, 10.5, 1000),
            _intraday_stamped_row("2024-01-03", 10.5, 12, 10, 11.5, 2000),
        ]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31", "1D")
        # A peer loader's midnight-indexed daily index for the same dates.
        expected = pd.DatetimeIndex(
            [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
            name="trade_date",
        )
        # Compare timestamps + name, not resolution units (s vs us).
        assert df.index.name == expected.name
        assert list(df.index) == list(expected)

    def test_intraday_bars_keep_their_timestamp(self):
        rows = [
            _intraday_stamped_row("2024-01-02", 10, 11, 9, 10.5, 1000),
        ]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31", "1H")
        ts = df.index[0]
        assert ts.hour == 14 and ts.minute == 30

    def test_default_interval_normalizes_to_midnight(self):
        rows = [_intraday_stamped_row("2024-01-02", 10, 11, 9, 10.5, 1000)]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31")
        assert df.index[0] == pd.Timestamp("2024-01-02")


class TestEpochSeconds:
    """_epoch_seconds derives from the calendar date, not wall-clock time."""

    def test_matches_utc_midnight(self):
        assert _epoch_seconds("2024-01-02") == _epoch("2024-01-02")

    def test_is_deterministic(self):
        assert _epoch_seconds("2024-03-15") == _epoch_seconds("2024-03-15")


class TestRowsToFrame:
    """_rows_to_frame normalizes, clips to the inclusive window, drops bad bars."""

    def test_empty_rows(self):
        assert _rows_to_frame([], "2024-01-01", "2024-01-31").empty

    def test_basic_shape_and_dtypes(self):
        rows = [
            _row("2024-01-02", 10, 11, 9, 10.5, 1000),
            _row("2024-01-03", 10.5, 12, 10, 11.5, 2000),
        ]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31")
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "trade_date"
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.tz is None
        assert all(str(df[col].dtype) == "float64" for col in df.columns)
        assert df.index.is_monotonic_increasing
        assert len(df) == 2

    def test_clips_to_inclusive_window(self):
        rows = [
            _row("2023-12-31", 1, 1, 1, 1, 1),  # before start
            _row("2024-01-05", 2, 2, 2, 2, 2),  # inside
            _row("2024-01-31", 3, 3, 3, 3, 3),  # inclusive end retained
            _row("2024-02-01", 4, 4, 4, 4, 4),  # after end
        ]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31")
        dates = [ts.strftime("%Y-%m-%d") for ts in df.index]
        assert dates == ["2024-01-05", "2024-01-31"]

    def test_drops_bars_with_null_ohlc(self):
        rows = [
            _row("2024-01-02", 10, 11, 9, 10.5, 1000),
            _row("2024-01-03", None, 12, 10, 11.5, 2000),  # null open -> dropped
        ]
        df = _rows_to_frame(rows, "2024-01-01", "2024-01-31")
        assert len(df) == 1
        assert df.index[0].strftime("%Y-%m-%d") == "2024-01-02"


class TestFetch:
    """fetch dispatches per symbol, mocks get_chart, isolates failures."""

    def test_fetch_us_symbol(self):
        rows = [
            _row("2024-01-02", 10, 11, 9, 10.5, 1000),
            _row("2024-01-03", 10.5, 12, 10, 11.5, 2000),
        ]
        with patch(
            "backtest.loaders.yahoo_loader.yahoo_client.get_chart",
            return_value=rows,
        ) as mock_chart:
            out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
        assert "AAPL.US" in out
        assert len(out["AAPL.US"]) == 2
        # Symbol passes through to the client unchanged (client maps it).
        assert mock_chart.call_args.args[0] == "AAPL.US"
        # period1/period2 derived from the dates; period2 is exclusive (+1 day).
        kwargs = mock_chart.call_args.kwargs
        assert kwargs["period1"] == _epoch("2024-01-01")
        assert kwargs["period2"] == _epoch("2024-01-31") + 86400
        assert kwargs["interval"] == "1d"

    def test_non_us_hk_symbol_skipped(self):
        with patch(
            "backtest.loaders.yahoo_loader.yahoo_client.get_chart"
        ) as mock_chart:
            out = DataLoader().fetch(["601398.SH"], "2024-01-01", "2024-01-31")
        assert out == {}
        mock_chart.assert_not_called()

    def test_one_failure_does_not_abort_batch(self):
        good_rows = [_row("2024-01-02", 10, 11, 9, 10.5, 1000)]

        def fake_chart(symbol, **_kwargs):
            if symbol == "BAD.US":
                raise ValueError("yahoo chart error")
            return good_rows

        with patch(
            "backtest.loaders.yahoo_loader.yahoo_client.get_chart",
            side_effect=fake_chart,
        ):
            out = DataLoader().fetch(
                ["BAD.US", "GOOD.US"], "2024-01-01", "2024-01-31"
            )
        assert "BAD.US" not in out
        assert "GOOD.US" in out

    def test_empty_codes_short_circuits(self):
        with patch(
            "backtest.loaders.yahoo_loader.yahoo_client.get_chart"
        ) as mock_chart:
            assert DataLoader().fetch([], "2024-01-01", "2024-01-31") == {}
        mock_chart.assert_not_called()

    def test_no_data_symbol_omitted(self):
        with patch(
            "backtest.loaders.yahoo_loader.yahoo_client.get_chart",
            return_value=[],
        ):
            out = DataLoader().fetch(["AAPL.US"], "2024-01-01", "2024-01-31")
        assert out == {}


class TestLoaderMetadata:
    """Static loader attributes match the registry contract."""

    def test_name_and_markets(self):
        loader = DataLoader()
        assert loader.name == "yahoo"
        assert loader.markets == {"us_equity", "hk_equity"}
        assert loader.requires_auth is False
        assert loader.is_available() is True
