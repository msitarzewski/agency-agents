"""Tests for startup preflight checks."""

from __future__ import annotations

import sys

from src import preflight


def test_akshare_check_uses_spec_without_import(monkeypatch) -> None:
    """AKShare's package import is heavy; preflight should only check discovery."""
    monkeypatch.delitem(sys.modules, "akshare", raising=False)
    monkeypatch.setattr(preflight, "find_spec", lambda name: object() if name == "akshare" else None)

    result = preflight._check_akshare()

    assert result.status == "ready"
    assert result.message == "installed"
    assert "akshare" not in sys.modules


def test_akshare_check_skips_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(preflight, "find_spec", lambda name: None)

    result = preflight._check_akshare()

    assert result.status == "skipped"
    assert result.message == "package not installed"


def test_content_filter_threshold_check(monkeypatch) -> None:
    """Content Filter Threshold row must appear in preflight output."""
    monkeypatch.setenv("CONTENT_FILTER_WARNING_THRESHOLD", "0.10")

    result = preflight._check_content_filter_threshold()

    assert result.name == "Content Filter Threshold"
    assert result.status == "ready"
    assert "10%" in result.message
    assert "CONTENT_FILTER_WARNING_THRESHOLD" in result.message


def test_content_filter_threshold_default(monkeypatch) -> None:
    """Default threshold is 5% when env var is unset."""
    monkeypatch.delenv("CONTENT_FILTER_WARNING_THRESHOLD", raising=False)

    result = preflight._check_content_filter_threshold()

    assert result.name == "Content Filter Threshold"
    assert result.status == "ready"
    assert "5%" in result.message
