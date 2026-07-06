"""Regression tests for the SPA deep-link middleware in ``api_server``.

The middleware intercepts browser navigation (``Accept: text/html``) to
SPA pages that share a path with an API endpoint, serving the SPA shell
instead. It must NOT intercept API-only paths even when called with a
text/html accept header — the matcher is intentionally narrow so things
like ``/runs/{id}/code`` and ``/runs/{id}/pine`` keep returning the
correct API response.
"""

from __future__ import annotations

import pytest


class TestSpaHtmlRouteMatcher:
    """Pin the matcher used by ``_spa_html_deep_link_fallback`` middleware."""

    @pytest.mark.parametrize(
        "path",
        [
            "/correlation",        # Correlation page
            "/runs/abc",           # RunDetail (no trailing slash)
            "/runs/abc-123",       # RunDetail with dashes
            "/runs/abc/",          # RunDetail (trailing slash)
        ],
    )
    def test_spa_pages_match(self, path: str) -> None:
        from api_server import _is_spa_html_route

        assert _is_spa_html_route(path) is True, path

    @pytest.mark.parametrize(
        "path",
        [
            "/runs",                # collection endpoint (API only)
            "/runs/abc/code",       # API-only — must NOT be hijacked
            "/runs/abc/pine",       # API-only — must NOT be hijacked
            "/runs/abc/code/",
            "/runs/abc/foo/bar",    # deeper nested — defensive
            "/sessions/xyz",        # different namespace
            "/api",
            "/skills",
            "/correlation/extra",   # only the bare /correlation page exists
        ],
    )
    def test_api_only_paths_do_not_match(self, path: str) -> None:
        from api_server import _is_spa_html_route

        assert _is_spa_html_route(path) is False, path
