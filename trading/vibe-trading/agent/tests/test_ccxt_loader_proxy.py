"""Regression tests for CCXT proxy environment handling."""

from __future__ import annotations

import ccxt

from backtest.loaders.ccxt_loader import DataLoader


class _FakeExchange:
    def __init__(self, config):
        self.config = config


def _clear_proxy_env(monkeypatch):
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        monkeypatch.delenv(name, raising=False)


def test_get_exchange_passes_all_proxy_to_ccxt(monkeypatch):
    _clear_proxy_env(monkeypatch)
    monkeypatch.setenv("CCXT_EXCHANGE", "binance")
    monkeypatch.setenv("ALL_PROXY", "socks5h://127.0.0.1:1088")
    monkeypatch.setattr(ccxt, "binance", _FakeExchange)

    exchange = DataLoader()._get_exchange()

    assert exchange.config["proxies"] == {
        "http": "socks5h://127.0.0.1:1088",
        "https": "socks5h://127.0.0.1:1088",
    }


def test_get_exchange_prefers_explicit_http_and_https_proxy_over_all_proxy(monkeypatch):
    _clear_proxy_env(monkeypatch)
    monkeypatch.setenv("CCXT_EXCHANGE", "binance")
    monkeypatch.setenv("ALL_PROXY", "socks5h://127.0.0.1:1088")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:8443")
    monkeypatch.setattr(ccxt, "binance", _FakeExchange)

    exchange = DataLoader()._get_exchange()

    assert exchange.config["proxies"] == {
        "http": "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8443",
    }


def test_get_exchange_omits_proxy_config_when_env_absent(monkeypatch):
    _clear_proxy_env(monkeypatch)
    monkeypatch.setenv("CCXT_EXCHANGE", "binance")
    monkeypatch.setattr(ccxt, "binance", _FakeExchange)

    exchange = DataLoader()._get_exchange()

    assert "proxies" not in exchange.config
