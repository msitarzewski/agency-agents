"""Provider abstraction for reliable public web search.

The provider is intentionally HTTP/JSON based. Browser-page scraping belongs
only in the legacy fallback module and is not the primary research path.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import List, Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


@dataclass
class ProviderResult:
    title: str
    url: str
    snippet: str = ""
    provider: str = "unknown"


def _configured_provider() -> tuple[str, str, str]:
    """Return provider, endpoint, and API key from environment."""
    provider = os.getenv("SEARCH_PROVIDER", "tavily").strip().lower()
    if provider == "tavily":
        return (
            provider,
            os.getenv("SEARCH_API_URL", "https://api.tavily.com/search"),
            os.getenv("SEARCH_API_KEY", ""),
        )
    if provider == "serper":
        return (
            provider,
            os.getenv("SEARCH_API_URL", "https://google.serper.dev/search"),
            os.getenv("SEARCH_API_KEY", ""),
        )
    raise ValueError(f"unsupported SEARCH_PROVIDER={provider!r}")


def _request_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def search_api(query: str, max_results: int = 5, timeout: int = 20) -> List[ProviderResult]:
    """Search using a configured JSON search API.

    Supports Tavily and Serper-compatible response formats. No result is
    treated as evidence until its title/URL/snippet passes identity filtering
    in the caller.
    """
    provider, endpoint, api_key = _configured_provider()
    if not api_key:
        raise RuntimeError(
            f"{provider} search is configured but SEARCH_API_KEY is missing"
        )

    if provider == "tavily":
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }
        data = _request_json(
            endpoint,
            payload,
            {"Content-Type": "application/json", "User-Agent": "ClientAcquisitionOS/0.3"},
            timeout,
        )
        raw_results = data.get("results", [])
        return [
            ProviderResult(
                title=str(item.get("title", "")).strip(),
                url=str(item.get("url", "")).strip(),
                snippet=str(item.get("content", "")).strip(),
                provider=provider,
            )
            for item in raw_results
            if item.get("title") and item.get("url")
        ]

    data = _request_json(
        endpoint,
        {"q": query, "num": max_results},
        {
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
            "User-Agent": "ClientAcquisitionOS/0.3",
        },
        timeout,
    )
    raw_results = data.get("organic", [])
    return [
        ProviderResult(
            title=str(item.get("title", "")).strip(),
            url=str(item.get("link", "")).strip(),
            snippet=str(item.get("snippet", "")).strip(),
            provider=provider,
        )
        for item in raw_results
        if item.get("title") and item.get("link")
    ]
