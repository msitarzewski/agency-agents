"""Security tests for the web reader tool."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.tools import web_reader_tool


@pytest.mark.parametrize(
    "url",
    [
        "",
        "file:///etc/passwd",
        "ftp://example.com/report",
        "https:///missing-host",
        "https://user:pass@example.com/private",
        "http://localhost:8899/health",
        "http://api.localhost/health",
        "http://service.local/status",
        "http://127.0.0.1:8899/health",
        "http://0.0.0.0:8899/health",
        "http://10.0.0.5/metadata",
        "http://172.16.0.5/metadata",
        "http://192.168.1.5/metadata",
        "http://169.254.169.254/latest/meta-data",
        "http://224.0.0.1/",
        "http://[::1]/",
        "http://[fc00::1]/",
        "http://[fe80::1]/",
    ],
)
def test_read_url_rejects_non_public_targets_without_network(
    monkeypatch: pytest.MonkeyPatch, url: str,
) -> None:
    def fail_get(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("requests.get should not be called for blocked URLs")

    monkeypatch.setattr(web_reader_tool.requests, "get", fail_get)

    result = json.loads(web_reader_tool.read_url(url))

    assert result["status"] == "error"
    assert "target URL is not allowed" in result["error"]


def test_read_url_allows_public_http_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_get(url: str, **kwargs: object) -> SimpleNamespace:
        calls.append({"url": url, **kwargs})
        return SimpleNamespace(
            status_code=200,
            text="Title: Example\n\n# Example\n\nPublic content",
        )

    monkeypatch.setattr(web_reader_tool.requests, "get", fake_get)

    result = json.loads(web_reader_tool.read_url("https://example.com/docs?x=1"))

    assert result["status"] == "ok"
    assert result["title"] == "Example"
    assert result["url"] == "https://example.com/docs?x=1"
    assert calls == [
        {
            "url": "https://r.jina.ai/https://example.com/docs?x=1",
            "headers": {"Accept": "text/markdown"},
            "timeout": 30,
        }
    ]
