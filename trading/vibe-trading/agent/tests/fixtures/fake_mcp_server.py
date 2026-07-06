"""Minimal fake MCP server for integration tests.

Launched as a stdio subprocess by test_mcp_stdio_integration.py.
Exposes two tools:
  - echo(message: str) -> str   — returns "echo: <message>"
  - add(a: int, b: int) -> int  — returns a + b

Usage (called by pytest, not directly):
    python agent/tests/fixtures/fake_mcp_server.py
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("fake-mcp-server")


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back with a prefix.

    Args:
        message: The message to echo.

    Returns:
        The message prefixed with "echo: ".
    """
    return f"echo: {message}"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        The sum a + b.
    """
    return a + b


if __name__ == "__main__":
    mcp.run(transport="stdio")
