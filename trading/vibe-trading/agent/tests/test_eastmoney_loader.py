"""Tests for the Eastmoney OHLCV loader.

These never touch the network: the cross-market path mocks the shared client
(:mod:`backtest.loaders.eastmoney_client`), and the end-to-end path mocks the
HTTP boundary (``throttled_get_json``) so the real client parsing runs while no
request leaves the process.
"""

from __future__ import annotations

from typing import List
from unittest.mock import patch

import pandas as pd
import pytest

from backtest.loaders import eastmoney_client
from backtest.loaders.eastmoney_loader import DataLoader, _to_compact_date


def _client_rows() -> List[dict]:
    """Two ascending bars in eastmoney_client.fetch_kline output shape."""
    return [
        {
            "trade_date": "2024-01-02",
            "open": 1700.0,
            "close": 1710.0,
            "high": 1720.0,
            "low": 1690.0,
            "volume": 100000.0,
            "amount": 1.7e8,
        },
        {
            "trade_date": "2024-01-03",
            "open": 1711.0,
            "close": 1705.0,
            "high": 1725.0,
            "low": 1700.0,
            "volume": 120000.0,
            "amount": 2.0e8,
        },
    ]


# ---------------------------------------------------------------------------
# Loader contract
# ---------------------------------------------------------------------------


class TestLoaderContract:
    def test_class_attributes(self) -> None:
        loader = DataLoader()
        assert loader.name == "eastmoney"
        assert loader.markets == {"a_share", "hk_equity", "us_equity"}
        assert loader.requires_auth is False

    def test_is_available_true(self) -> None:
        assert DataLoader().is_available() is True


class TestToCompactDate:
    def test_dashed_date_compacts(self) -> None:
        assert _to_compact_date("2024-01-02") == "20240102"

    def test_invalid_date_raises(self) -> None:
        with pytest.raises(ValueError):
            _to_compact_date("not-a-date")


# ---------------------------------------------------------------------------
# fetch() — client mocked
# ---------------------------------------------------------------------------


class TestFetchWithMockedClient:
    def test_a_share_builds_canonical_frame(self) -> None:
        loader = DataLoader()
        with patch.object(
            eastmoney_client, "resolve_secid", return_value="1.600519"
        ) as resolve, patch.object(
            eastmoney_client, "fetch_kline", return_value=_client_rows()
        ) as fetch_kline:
            out = loader.fetch(
                ["600519.SH"], "2024-01-01", "2024-01-31", interval="1D"
            )

        resolve.assert_called_once_with("600519.SH")
        # 1D -> klt 101, compact dates passed through.
        _, kwargs = fetch_kline.call_args
        assert kwargs["klt"] == eastmoney_client.KLT_BY_INTERVAL["1D"]
        assert kwargs["beg"] == "20240101"
        assert kwargs["end"] == "20240131"

        assert set(out) == {"600519.SH"}
        df = out["600519.SH"]
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "trade_date"
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.is_monotonic_increasing
        assert len(df) == 2
        assert df.iloc[0]["close"] == pytest.approx(1710.0)
        assert all(str(df[c].dtype) == "float64" for c in df.columns)

    def test_unsupported_interval_yields_no_frame(self) -> None:
        loader = DataLoader()
        with patch.object(eastmoney_client, "resolve_secid") as resolve, patch.object(
            eastmoney_client, "fetch_kline"
        ) as fetch_kline:
            out = loader.fetch(["600519.SH"], "2024-01-01", "2024-01-31", interval="3m")

        assert out == {}
        resolve.assert_not_called()
        fetch_kline.assert_not_called()

    def test_unresolvable_symbol_omitted(self) -> None:
        loader = DataLoader()
        with patch.object(
            eastmoney_client, "resolve_secid", return_value=None
        ), patch.object(eastmoney_client, "fetch_kline") as fetch_kline:
            out = loader.fetch(["WAT.XYZ"], "2024-01-01", "2024-01-31")

        assert out == {}
        fetch_kline.assert_not_called()

    def test_one_bad_symbol_does_not_abort_batch(self) -> None:
        loader = DataLoader()

        def _resolve(symbol: str) -> str | None:
            return "1.600519" if symbol == "600519.SH" else "0.000001"

        def _fetch_kline(secid: str, **_kwargs: object) -> List[dict]:
            if secid == "0.000001":
                raise RuntimeError("eastmoney boom")
            return _client_rows()

        with patch.object(eastmoney_client, "resolve_secid", side_effect=_resolve), patch.object(
            eastmoney_client, "fetch_kline", side_effect=_fetch_kline
        ):
            out = loader.fetch(
                ["000001.SZ", "600519.SH"], "2024-01-01", "2024-01-31"
            )

        # The boom symbol is dropped; the healthy one survives.
        assert set(out) == {"600519.SH"}

    def test_empty_klines_omitted(self) -> None:
        loader = DataLoader()
        with patch.object(
            eastmoney_client, "resolve_secid", return_value="116.00700"
        ), patch.object(eastmoney_client, "fetch_kline", return_value=[]):
            out = loader.fetch(["00700.HK"], "2024-01-01", "2024-01-31")

        assert out == {}

    def test_invalid_date_range_raises(self) -> None:
        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.fetch(["600519.SH"], "2024-02-01", "2024-01-01")


# ---------------------------------------------------------------------------
# End-to-end — only the HTTP boundary mocked, real client parsing runs.
# ---------------------------------------------------------------------------


class TestFetchEndToEndHttpMocked:
    def test_a_share_through_real_client(self) -> None:
        # push2his kline rows: "date,open,close,high,low,volume,amount".
        payload = {
            "data": {
                "klines": [
                    "2024-01-02,1700.00,1710.00,1720.00,1690.00,100000,1.7e8",
                    "2024-01-03,1711.00,1705.00,1725.00,1700.00,120000,2.0e8",
                ]
            }
        }
        loader = DataLoader()
        with patch.object(
            eastmoney_client, "throttled_get_json", return_value=payload
        ) as http:
            out = loader.fetch(["600519.SH"], "2024-01-01", "2024-01-31")

        http.assert_called_once()
        _, kwargs = http.call_args
        assert kwargs["params"]["secid"] == "1.600519"
        assert kwargs["host_key"] == "eastmoney"

        df = out["600519.SH"]
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 2
        assert df.iloc[1]["close"] == pytest.approx(1705.0)
