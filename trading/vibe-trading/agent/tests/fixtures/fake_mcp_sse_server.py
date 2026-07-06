"""Minimal FastMCP SSE server for integration tests.

Launched as an HTTP subprocess by test_mcp_sse_integration.py.
Exposes two tools:
    - echo(message: str) -> str  — returns "echo: <message>"
    - add(a: int, b: int) -> int — returns a + b

Usage (called by pytest, not directly):
    python agent/tests/fixtures/fake_mcp_sse_server.py --port 0 --port-file /tmp/fake-mcp-sse.port
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from fastmcp import FastMCP
import uvicorn

mcp = FastMCP("fake-mcp-sse-server")


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back with a prefix."""
    return f"echo: {message}"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal FastMCP SSE test server")
    parser.add_argument("--port", type=int, default=18900, help="SSE port")
    parser.add_argument("--path", default="/sse", help="SSE path")
    parser.add_argument("--port-file", default="", help="Optional file to write the bound port")
    args = parser.parse_args()

    app = mcp.http_app(path=args.path, transport="sse")
    config = uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning")
    server = uvicorn.Server(config)
    sock = config.bind_socket()
    if args.port_file:
        Path(args.port_file).write_text(str(sock.getsockname()[1]), encoding="utf-8")
    asyncio.run(server.serve(sockets=[sock]))


if __name__ == "__main__":
    main()
