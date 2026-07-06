"""iWenCai (问财) natural-language A-share research search tool.

iWenCai is a Chinese-market natural-language stock screener: a research caller
phrases a question in plain language ("low-PE banks with rising net profit") and
the service returns the matching A-share securities with the metric columns its
parser extracted from the question. This tool wraps that semantic-search
endpoint read-only.

The endpoint is rate-limited per source IP and requires a caller-supplied access
key, so every request routes through :mod:`backtest.loaders._http` for per-host
throttling and session reuse, and carries a ``Bearer`` authorization header built
from ``VIBE_TRADING_IWENCAI_KEY``. The tool is silently excluded from the registry
when that key is absent, so a key-less install never advertises a search it cannot
perform.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from backtest.loaders._http import resolve_min_interval, throttled_get_json
from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Endpoint + throttle bucket. All iWenCai calls share one host key so the shared
# HTTP layer spaces and pools them independently of other providers.
_SEARCH_URL = "https://www.iwencai.com/customized/chart/get-robot-data"
_HOST_KEY = "iwencai"
_MIN_INTERVAL_ENV = "VIBE_TRADING_IWENCAI_MIN_INTERVAL"
_DEFAULT_MIN_INTERVAL = 1.5

# Access key env var. Absent -> tool excluded by check_available().
_KEY_ENV = "VIBE_TRADING_IWENCAI_KEY"

# Result caps so a broad query never returns an unbounded payload.
_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100
# Hard ceiling on per-row columns retained, keeping the envelope compact even
# when the service tags a row with dozens of derived metrics.
_MAX_COLUMNS = 40


def _min_interval() -> float:
    """Resolve the per-call minimum iWenCai request spacing in seconds."""
    return resolve_min_interval(_MIN_INTERVAL_ENV, _DEFAULT_MIN_INTERVAL)


def _coerce_limit(value: Any) -> int:
    """Clamp a requested row limit into the supported range.

    Args:
        value: Raw ``limit`` argument (may be missing, a string, or a number).

    Returns:
        An int in ``[1, _MAX_LIMIT]``, defaulting to ``_DEFAULT_LIMIT`` when the
        value is missing or not parseable.
    """
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    if limit < 1:
        return _DEFAULT_LIMIT
    return min(limit, _MAX_LIMIT)


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    """Pull the answer rows out of the iWenCai robot-data response.

    The service nests the structured result several levels deep under
    ``data.answer[].txt[].content.components[].data.datas``; any level may be
    absent on an empty or unparseable answer, so each hop is defensive and a
    missing branch yields an empty list rather than raising.

    Args:
        payload: Decoded JSON response body.

    Returns:
        The list of per-security row dicts, possibly empty.
    """
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    for answer in data.get("answer", []) if isinstance(data.get("answer"), list) else []:
        if not isinstance(answer, dict):
            continue
        for txt in answer.get("txt", []) if isinstance(answer.get("txt"), list) else []:
            rows = _rows_from_txt(txt)
            if rows:
                return rows
    return []


def _rows_from_txt(txt: Any) -> list[dict[str, Any]]:
    """Extract the ``datas`` rows from one ``txt`` block, if present.

    Args:
        txt: One entry of an answer's ``txt`` list.

    Returns:
        The row dicts under the first component carrying ``data.datas``; empty
        when this block holds no tabular result.
    """
    if not isinstance(txt, dict):
        return []
    content = txt.get("content")
    if not isinstance(content, dict):
        return []
    components = content.get("components")
    if not isinstance(components, list):
        return []
    for component in components:
        if not isinstance(component, dict):
            continue
        comp_data = component.get("data")
        if not isinstance(comp_data, dict):
            continue
        datas = comp_data.get("datas")
        if isinstance(datas, list):
            return [row for row in datas if isinstance(row, dict)]
    return []


def _project_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Trim one raw answer row to a compact, column-capped record.

    iWenCai returns a wide, query-dependent column set keyed by Chinese metric
    names; rather than hardcode column names (they vary per question) we pass the
    columns through verbatim but cap their count so the payload stays bounded.

    Args:
        raw: One row dict from the answer's ``datas`` list.

    Returns:
        A dict with at most ``_MAX_COLUMNS`` of the row's key/value pairs.
    """
    items = list(raw.items())[:_MAX_COLUMNS]
    return {str(key): value for key, value in items}


class IWenCaiSearchTool(BaseTool):
    """Run an iWenCai (问财) natural-language A-share research query."""

    name = "iwencai_search"

    @classmethod
    def check_available(cls) -> bool:
        """Available only when an iWenCai access key is configured.

        Returns:
            ``True`` when ``VIBE_TRADING_IWENCAI_KEY`` is set to a non-empty
            value; ``False`` otherwise, which silently excludes the tool from
            the registry. Never raises.
        """
        return bool(os.getenv(_KEY_ENV))

    description = (
        "Run a natural-language A-share research query against iWenCai (问财), a "
        "Chinese-market semantic stock screener. Phrase the question in plain "
        "language (Chinese works best) and get back the matching China A-share "
        "(SH/SZ) securities with the metric columns iWenCai parsed from the "
        "question. Read-only; requires the VIBE_TRADING_IWENCAI_KEY access key. "
        'Example: {"query": "市盈率低于15的银行股", "limit": 10}.'
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Natural-language research question, e.g. "
                    "'市盈率低于15且净利润增长的银行股' or 'low-PE banks with "
                    "rising net profit'. Chinese phrasing yields the best parse."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    "Maximum securities to return. Default 20, max 100; values "
                    "outside the range are clamped."
                ),
                "default": _DEFAULT_LIMIT,
            },
        },
        "required": ["query"],
    }
    repeatable = True

    def execute(self, **kwargs: Any) -> str:
        """Execute an iWenCai semantic search and return a JSON envelope.

        Args:
            **kwargs: ``query`` (required, str) and optional ``limit`` (int).

        Returns:
            A JSON string envelope. On success:
            ``{"ok": true, "market": "a_share", "source": "iwencai",
            "data": {"query": ..., "count": int, "results": [...]}}``. On
            failure: ``{"ok": false, "error": "..."}``.
        """
        key = os.getenv(_KEY_ENV)
        if not key:
            return self._error(
                f"iWenCai access key not configured; set {_KEY_ENV} to enable this tool"
            )

        query_arg = kwargs.get("query")
        if not isinstance(query_arg, str) or not query_arg.strip():
            return self._error("missing required parameter: query")
        query = query_arg.strip()
        limit = _coerce_limit(kwargs.get("limit"))

        try:
            payload = throttled_get_json(
                _SEARCH_URL,
                host_key=_HOST_KEY,
                min_interval=_min_interval(),
                params={
                    "question": query,
                    "perpage": str(limit),
                    "page": "1",
                    "source": "Ths_iwencai_Xuangu",
                },
                headers={"Authorization": f"Bearer {key}"},
            )
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure as an envelope
            logger.warning("iwencai search failed for %r: %s", query, exc)
            return self._error(f"iwencai search failed: {exc}")

        rows = _extract_rows(payload)
        results = [_project_row(row) for row in rows[:limit]]
        data = {"query": query, "count": len(results), "results": results}
        return json.dumps(
            {"ok": True, "market": "a_share", "source": "iwencai", "data": data},
            ensure_ascii=False,
        )

    @staticmethod
    def _error(message: str) -> str:
        """Render a failure envelope as a JSON string.

        Args:
            message: Human-readable error text.

        Returns:
            ``{"ok": false, "error": message}`` as a JSON string.
        """
        return json.dumps({"ok": False, "error": message}, ensure_ascii=False)
