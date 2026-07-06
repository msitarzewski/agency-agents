"""Tests for the mootdx A-share OHLCV loader."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from backtest.loaders.mootdx_loader import DataLoader, _is_a_share, _is_bj


# ---------------------------------------------------------------------------
# Symbol detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, expected",
    [
        ("000001.SZ", True),
        ("600519.SH", True),
        ("835174.BJ", True),
        ("000001", True),
        ("600519", True),
        ("AAPL.US", False),
        ("00700.HK", False),
        ("BTC-USDT", False),
        ("12345", False),  # 5-digit
        ("000001A", False),  # contains letter
    ],
)
def test_is_a_share(code: str, expected: bool) -> None:
    assert _is_a_share(code) is expected


# ---------------------------------------------------------------------------
# Fake mootdx client (no network, no TCP)
# ---------------------------------------------------------------------------


class _FakeStdQuotes:
    """Drop-in for ``mootdx.quotes.StdQuotes`` covering the two methods we call."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def get_k_data(self, code: str, start_date: str, end_date: str):
        self.calls.append(("get_k_data", code, start_date, end_date))
        idx = pd.DatetimeIndex(["2025-01-02", "2025-01-03", "2025-01-06"], name="date")
        return pd.DataFrame(
            {
                "open":   [11.73, 11.44, 11.38],
                "close":  [11.43, 11.38, 11.44],
                "high":   [11.77, 11.54, 11.48],
                "low":    [11.40, 11.32, 11.31],
                "vol":    [1_000_000, 800_000, 950_000],
                "amount": [1.1e7, 9.1e6, 1.08e7],
                "date":   ["2025-01-02", "2025-01-03", "2025-01-06"],
                "code":   [code, code, code],
            },
            index=idx,
        )

    def bars(self, symbol: str, frequency: int, start: int = 0, offset: int = 800):
        self.calls.append(("bars", symbol, frequency, start, offset))
        # First page (start=0): four 15-min bars on 2025-01-02. Subsequent
        # pages return empty so the paginator stops promptly.
        if start > 0:
            return pd.DataFrame(columns=["open", "close", "high", "low", "vol",
                                          "amount", "datetime", "volume"])
        timestamps = pd.date_range("2025-01-02 09:30", periods=4, freq="15min")
        return pd.DataFrame(
            {
                "open":     [11.73, 11.74, 11.75, 11.76],
                "close":    [11.74, 11.75, 11.76, 11.77],
                "high":     [11.78, 11.79, 11.80, 11.81],
                "low":      [11.70, 11.71, 11.72, 11.73],
                "vol":      [100, 200, 300, 400],
                "amount":   [1100, 2200, 3300, 4400],
                "datetime": [t.strftime("%Y-%m-%d %H:%M") for t in timestamps],
                "volume":   [100, 200, 300, 400],
            },
            index=pd.DatetimeIndex(timestamps, name="datetime"),
        )


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> _FakeStdQuotes:
    """Install a fake StdQuotes so DataLoader doesn't hit the TDX network."""
    fake = _FakeStdQuotes()
    fake_module = SimpleNamespace(Quotes=SimpleNamespace(factory=lambda market: fake))
    import sys
    monkeypatch.setitem(sys.modules, "mootdx", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "mootdx.quotes", fake_module)
    return fake


# ---------------------------------------------------------------------------
# Loader behavior
# ---------------------------------------------------------------------------


def test_fetch_daily_uses_get_k_data(fake_client: _FakeStdQuotes) -> None:
    loader = DataLoader()
    out = loader.fetch(["000001.SZ"], "2025-01-01", "2025-01-10", interval="1D")

    assert "000001.SZ" in out
    df = out["000001.SZ"]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.name == "trade_date"
    assert len(df) == 3
    # Symbol stripping: SDK called with bare 6-digit code.
    assert any(call[0] == "get_k_data" and call[1] == "000001" for call in fake_client.calls)


def test_fetch_intraday_uses_bars_and_clips_window(
    fake_client: _FakeStdQuotes,
) -> None:
    loader = DataLoader()
    out = loader.fetch(["600519"], "2025-01-02", "2025-01-02", interval="15m")

    assert "600519" in out
    df = out["600519"]
    assert len(df) == 4  # all four 15-min bars on 2025-01-02 are in window
    # frequency=1 corresponds to KLINE_15MIN in mootdx.consts.
    assert any(call[0] == "bars" and call[2] == 1 for call in fake_client.calls)
    # Paginator stopped after the first non-empty page returned older bars.
    assert sum(1 for c in fake_client.calls if c[0] == "bars") >= 1


def test_fetch_intraday_empty_window_returns_no_entry(
    fake_client: _FakeStdQuotes,
) -> None:
    loader = DataLoader()
    out = loader.fetch(["600519"], "2030-01-01", "2030-01-02", interval="5m")
    assert out == {}


def test_fetch_skips_non_a_share_symbols(fake_client: _FakeStdQuotes) -> None:
    loader = DataLoader()
    out = loader.fetch(["AAPL.US", "00700.HK", "BTC-USDT"], "2025-01-01", "2025-01-10")
    assert out == {}
    assert fake_client.calls == []


def test_fetch_skips_bj_symbols_with_warning(
    fake_client: _FakeStdQuotes, caplog: pytest.LogCaptureFixture,
) -> None:
    """Mootdx upstream has no BJ data; loader must skip + warn, not crash."""
    import logging
    caplog.set_level(logging.WARNING)
    loader = DataLoader()
    out = loader.fetch(["835174.BJ", "832000", "000001.SZ"], "2025-01-01", "2025-01-10")
    assert "835174.BJ" not in out
    assert "832000" not in out
    assert "000001.SZ" in out
    assert fake_client.calls and fake_client.calls[0][1] == "000001"
    warnings = [r for r in caplog.records if "北交所" in r.message]
    assert len(warnings) == 2


@pytest.mark.parametrize(
    "code, expected",
    [("835174.BJ", True), ("832000", True), ("488888", True),
     ("000001.SZ", False), ("600519", False), ("300750", False)],
)
def test_is_bj(code: str, expected: bool) -> None:
    assert _is_bj(code) is expected


def test_fetch_rejects_unknown_interval(fake_client: _FakeStdQuotes) -> None:
    loader = DataLoader()
    with pytest.raises(ValueError, match="Unsupported interval"):
        loader.fetch(["000001.SZ"], "2025-01-01", "2025-01-10", interval="3D")


def test_is_available_false_when_mootdx_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    real_import = builtins.__import__

    def blocking_import(name, *args, **kwargs):
        if name == "mootdx" or name.startswith("mootdx."):
            raise ImportError("mootdx not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocking_import)
    assert DataLoader().is_available() is False


def test_is_available_true_when_mootdx_present(fake_client: _FakeStdQuotes) -> None:
    assert DataLoader().is_available() is True


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


def test_registry_lists_mootdx_in_a_share_chain() -> None:
    from backtest.loaders.registry import FALLBACK_CHAINS, _ensure_registered, LOADER_REGISTRY

    _ensure_registered()
    assert "mootdx" in LOADER_REGISTRY
    chain = FALLBACK_CHAINS["a_share"]
    assert "mootdx" in chain
    # Order is by IP-ban risk: throttle-tolerant public/no-auth sources lead,
    # key-gated REST trails. So mootdx (TCP, no auth) > akshare (HTTP scrape) >
    # tushare (key-gated REST, placed last).
    assert chain.index("mootdx") < chain.index("akshare")
    assert chain.index("akshare") < chain.index("tushare")
