"""Smoke test for the MCP server entry point.

Regression test for PR #85 (deadlock fix). Spawns ``vibe-trading-mcp`` as a
subprocess and walks through the full JSON-RPC happy path:

1. ``initialize`` handshake.
2. ``tools/list`` returns the registered tool catalogue.
3. ``tools/call`` for ``analyze_options`` (a network-free Black-Scholes
   calculation) returns a sane numeric result.

The combined run cost is one cold spawn (~3-5s) plus sub-second per request.
The most important assertion is that ``tools/call`` does not hang: without
the registry pre-warm in ``mcp_server.main()``, the lazy registry build runs
inside FastMCP's worker thread on the first ``tools/call`` and deadlocks.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "agent"

# Generous bound — covers cold imports of fastmcp + tool registry build on
# slow CI runners. The patched server typically finishes initialize in 3-9s.
INIT_TIMEOUT = 30.0

# tools/call analyze_options is a pure CPU calculation. With the fix in place
# it returns in well under a second; without it, it never returns. 15s is a
# safe lower bound that still flags the deadlock quickly.
CALL_TIMEOUT = 15.0

# Tools we rely on as a baseline. The repo currently ships 35 tools; we
# assert ``>= 30`` so unrelated tool additions / removals don't break the
# test, but a regression that drops half the catalogue still fires.
EXPECTED_MIN_TOOL_COUNT = 30
REQUIRED_TOOL_NAMES = {
    "analyze_options",
    "get_market_data",
    "list_skills",
    "start_research_goal",
    "get_research_goal",
    "add_goal_evidence",
    "update_research_goal_status",
    "trading_connections",
    "trading_select_connection",
    "trading_check",
    "trading_account",
    "trading_positions",
    "trading_orders",
    "trading_quote",
    "trading_history",
}


def _reader(stream, q: Queue) -> None:
    """Pump every line from *stream* into *q*; signal EOF with ``None``."""
    try:
        for line in iter(stream.readline, b""):
            q.put(line)
    finally:
        q.put(None)


def _send(proc: subprocess.Popen, obj: dict) -> None:
    payload = (json.dumps(obj) + "\n").encode("utf-8")
    proc.stdin.write(payload)
    proc.stdin.flush()


def _wait_for_id(q: Queue, want_id: int, timeout: float):
    """Drain *q* until a JSON-RPC response with matching ``id`` arrives.

    Returns ``(response_dict, elapsed_seconds)`` on success, or
    ``(None, "TIMEOUT" | "EOF")`` on failure.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            line = q.get(timeout=0.5)
        except Empty:
            continue
        if line is None:
            return None, "EOF"
        try:
            obj = json.loads(line.decode("utf-8", errors="replace"))
        except Exception:
            # Server may emit non-JSON-RPC log lines on stdout in some envs;
            # skip and keep scanning for the response we care about.
            continue
        if obj.get("id") == want_id:
            return obj, time.time() - start
    return None, "TIMEOUT"


def _extract_tool_result(resp: dict) -> dict:
    """Pull the structured payload out of a ``tools/call`` JSON-RPC response.

    FastMCP wraps tool return values as ``result.content[0].text`` (a JSON
    string). Some tools in this repo additionally wrap their dict return as
    ``{"result": "<json string>"}``; we unwrap that second layer when
    present so callers see the real fields.
    """
    result = resp.get("result", {})
    content = result.get("content") or []
    assert content, f"tools/call response has no content: {resp}"
    text = content[0].get("text", "")
    data = json.loads(text)
    if (
        isinstance(data, dict)
        and set(data.keys()) == {"result"}
        and isinstance(data["result"], str)
    ):
        try:
            data = json.loads(data["result"])
        except (json.JSONDecodeError, ValueError):
            # Leave the raw envelope alone if it isn't actually nested JSON.
            pass
    return data


@pytest.mark.integration
def test_mcp_server_happy_path() -> None:
    """End-to-end smoke check for ``vibe-trading-mcp``.

    Verifies (1) the JSON-RPC handshake completes, (2) the tool catalogue
    is registered, and (3) ``tools/call analyze_options`` returns a sane
    numeric result without hanging. The hang case is the regression fixed
    by PR #85; without the registry pre-warm, ``tools/call`` deadlocks
    inside FastMCP's worker thread.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(AGENT_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    # Force unbuffered stdio in the child so its responses reach our reader
    # without being held in libc/Python buffers.
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-c", "from mcp_server import main; main()"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
        env=env,
        cwd=str(AGENT_DIR),
    )
    q: Queue = Queue()
    reader = threading.Thread(target=_reader, args=(proc.stdout, q), daemon=True)
    reader.start()

    try:
        # 1. initialize — first call, includes cold imports + registry build.
        _send(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smoke-test", "version": "1"},
            },
        })
        resp, info = _wait_for_id(q, 1, INIT_TIMEOUT)
        assert resp is not None, (
            f"initialize did not respond within {INIT_TIMEOUT}s (status={info})"
        )
        assert "result" in resp, f"initialize returned an error response: {resp}"

        # Required handshake step before any further request.
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 2. tools/list — verify the catalogue is wired up. A regression that
        # drops package data or breaks tool registration shows up here.
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        resp, info = _wait_for_id(q, 2, INIT_TIMEOUT)
        assert resp is not None, (
            f"tools/list did not respond within {INIT_TIMEOUT}s (status={info})"
        )
        tools = resp.get("result", {}).get("tools") or []
        assert len(tools) >= EXPECTED_MIN_TOOL_COUNT, (
            f"expected at least {EXPECTED_MIN_TOOL_COUNT} tools, got {len(tools)}"
        )
        tool_names = {t["name"] for t in tools}
        missing = REQUIRED_TOOL_NAMES - tool_names
        assert not missing, f"required tools missing from catalogue: {sorted(missing)}"

        # 3. tools/call analyze_options — pure CPU Black-Scholes; no network.
        # If this hangs, the cause is the registry build deadlock, not a
        # flaky data source.
        _send(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "analyze_options",
                "arguments": {"spot": 100.0, "strike": 105.0, "expiry_days": 30},
            },
        })
        resp, info = _wait_for_id(q, 3, CALL_TIMEOUT)
        assert resp is not None, (
            f"tools/call analyze_options did not respond within {CALL_TIMEOUT}s "
            f"(status={info}). This is the symptom fixed by PR #85 — check "
            f"that mcp_server.main() still calls _get_registry() before mcp.run()."
        )
        assert "result" in resp, f"tools/call returned an error response: {resp}"

        # Validate the numerical answer is at least in the right shape.
        # 5% OTM call, 30 days, default vol/rate — price should be a small
        # positive number, delta should sit between 0 and 1.
        data = _extract_tool_result(resp)
        price = data.get("price")
        delta = data.get("delta")
        assert isinstance(price, (int, float)) and price > 0, (
            f"expected positive price, got {price!r} from {data!r}"
        )
        assert isinstance(delta, (int, float)) and 0.0 <= delta <= 1.0, (
            f"expected call delta in [0, 1], got {delta!r} from {data!r}"
        )
    finally:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
