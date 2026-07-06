"""Web reader tool: fetch a URL as Markdown text via the Jina Reader API."""

from __future__ import annotations

import ipaddress
import json
import logging
from urllib.parse import urlsplit

import requests

from src.agent.progress import emit_progress
from src.agent.tools import BaseTool
from src.security.scanner import with_security_warnings

logger = logging.getLogger(__name__)

_JINA_PREFIX = "https://r.jina.ai/"
_TIMEOUT = 30
_MAX_LENGTH = 8000
_CACHED_MARKER = "Warning: This is a cached snapshot"


def _url_allowed(url: str) -> tuple[bool, str]:
    """Return whether a URL is safe to forward to the remote reader service."""
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return False, "target URL is not allowed"

    if parsed.scheme.lower() not in {"http", "https"}:
        return False, "target URL is not allowed"
    if not parsed.hostname:
        return False, "target URL is not allowed"
    if parsed.username or parsed.password:
        return False, "target URL is not allowed"

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        return False, "target URL is not allowed"

    ip_host = host.split("%", 1)[0]
    try:
        ip = ipaddress.ip_address(ip_host)
    except ValueError:
        return True, ""

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or not ip.is_global
    ):
        return False, "target URL is not allowed"
    return True, ""


def read_url(url: str, no_cache: bool = False) -> str:
    """Fetch web page content via the Jina Reader API.

    The full URL (including query string) is sent to the third-party Jina
    Reader service (r.jina.ai); never pass credentials/tokens or private
    addresses. Results may be a cached snapshot.

    Args:
        url: Target URL.
        no_cache: When true, ask the reader for a fresh (uncached) fetch.

    Returns:
        JSON result with title, content, url; ``cached: true`` is added
        when the reader served a stale snapshot.
    """
    target_url = url.strip()
    allowed, error = _url_allowed(target_url)
    if not allowed:
        return json.dumps({"status": "error", "error": error}, ensure_ascii=False)

    try:
        headers = {"Accept": "text/markdown"}
        if no_cache:
            headers["x-no-cache"] = "true"
        emit_progress(
            "fetching",
            message=f"GET {target_url[:60]}{'…' if len(target_url) > 60 else ''}",
        )
        resp = requests.get(
            f"{_JINA_PREFIX}{target_url}",
            headers=headers,
            timeout=_TIMEOUT,
        )
        emit_progress("parsing", message="extracting markdown")
        if resp.status_code != 200:
            logger.warning("read_url upstream HTTP %s: %s", resp.status_code, resp.text[:500])
            return json.dumps({
                "status": "error",
                "error": f"remote reader returned HTTP {resp.status_code}: {resp.text[:500]}",
            }, ensure_ascii=False)

        text = resp.text
        title = ""
        for line in text.split("\n"):
            if line.startswith("Title:"):
                title = line[6:].strip()
                break

        if len(text) > _MAX_LENGTH:
            text = text[:_MAX_LENGTH] + f"\n\n... (truncated, total {len(resp.text)} chars)"

        result = {
            "status": "ok",
            "title": title,
            "url": target_url,
            "content": text,
            "length": len(resp.text),
        }
        if _CACHED_MARKER in resp.text:
            result["cached"] = True
        result = with_security_warnings(result, fields=("content",))
        return json.dumps(result, ensure_ascii=False)

    except requests.Timeout:
        return json.dumps({"status": "error", "error": f"Request timed out ({_TIMEOUT}s)"}, ensure_ascii=False)
    except Exception as exc:
        logger.warning("read_url request failed: %s", exc)
        return json.dumps(
            {"status": "error", "error": f"remote reader request failed: {exc}"},
            ensure_ascii=False,
        )


class WebReaderTool(BaseTool):
    """Web reader tool."""

    name = "read_url"
    description = "Fetch web page content: provide a URL and receive the page as Markdown text. Useful for reading docs, articles, API references, etc."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the web page to read"},
            "no_cache": {"type": "boolean", "description": "Request a fresh (uncached) fetch", "default": False},
        },
        "required": ["url"],
    }
    repeatable = True

    def execute(self, **kwargs) -> str:
        """Fetch web page."""
        return read_url(kwargs["url"], no_cache=bool(kwargs.get("no_cache", False)))
