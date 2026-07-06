"""Shared helpers for HTTP-based MCP integration tests."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

import requests

_PYTHON = sys.executable


def make_single_server_agent_json(
    tmp_path: Path,
    server_name: str,
    *,
    transport_type: str,
    url: str,
    **server_kwargs: Any,
) -> Path:
    """Write a minimal agent.json with one remote MCP server."""
    config: dict[str, Any] = {
        "mcpServers": {
            server_name: {
                "type": transport_type,
                "url": url,
                **server_kwargs,
            }
        }
    }
    cfg_path = tmp_path / "agent.json"
    cfg_path.write_text(json.dumps(config))
    return cfg_path


@contextmanager
def reserved_local_port() -> Iterator[int]:
    """Reserve a loopback port for the lifetime of the context."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        yield int(sock.getsockname()[1])


def stop_http_mcp_server(proc: subprocess.Popen[str]) -> None:
    """Terminate an HTTP MCP subprocess and wait for clean exit."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _collect_process_output(proc: subprocess.Popen[str]) -> str:
    """Return subprocess stdout after ensuring the process has exited."""
    if proc.poll() is None:
        stop_http_mcp_server(proc)
    return proc.stdout.read() if proc.stdout is not None else ""


def start_http_mcp_server(
    fixture_server: Path,
    *,
    ready_url: str,
    service_name: str,
    extra_args: list[str],
    ready_statuses: set[int] | None = None,
    ready_request_kwargs: dict[str, Any] | None = None,
) -> subprocess.Popen[str]:
    """Start an HTTP MCP subprocess and wait until the endpoint is reachable."""
    proc = subprocess.Popen(
        [_PYTHON, str(fixture_server), *extra_args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    request_kwargs = dict(ready_request_kwargs or {})
    accepted_statuses = set(ready_statuses or {200})

    for _ in range(40):
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout is not None else ""
            raise RuntimeError(f"{service_name} failed to start with exit code {proc.returncode}: {output}")
        try:
            response = requests.get(ready_url, timeout=0.5, **request_kwargs)
            if response.status_code in accepted_statuses:
                response.close()
                return proc
            response.close()
        except requests.RequestException:
            time.sleep(0.2)

    stop_http_mcp_server(proc)
    output = proc.stdout.read() if proc.stdout is not None else ""
    raise RuntimeError(f"{service_name} did not become ready within 8 seconds: {output}")


def start_http_mcp_server_on_random_port(
    fixture_server: Path,
    *,
    service_name: str,
    ready_url_builder: Callable[[int], str],
    extra_args_builder: Callable[[int], list[str]],
    ready_statuses: set[int] | None = None,
    ready_request_kwargs: dict[str, Any] | None = None,
    max_attempts: int = 5,
) -> tuple[subprocess.Popen[str], int]:
    """Start an HTTP MCP subprocess on an OS-assigned port."""
    last_error: RuntimeError | None = None

    for _ in range(max_attempts):
        with tempfile.TemporaryDirectory(prefix="mcp-port-") as temp_dir:
            port_file = Path(temp_dir) / "port.txt"
            proc = subprocess.Popen(
                [_PYTHON, str(fixture_server), *extra_args_builder(0), "--port-file", str(port_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                port = _wait_for_server_port(proc, port_file, service_name=service_name)
                _wait_for_http_ready(
                    proc,
                    ready_url=ready_url_builder(port),
                    service_name=service_name,
                    ready_statuses=ready_statuses,
                    ready_request_kwargs=ready_request_kwargs,
                )
                return proc, port
            except RuntimeError as exc:
                last_error = exc
                stop_http_mcp_server(proc)

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"{service_name} could not obtain an available port")


def _wait_for_server_port(
    proc: subprocess.Popen[str],
    port_file: Path,
    *,
    service_name: str,
    timeout_seconds: float = 8.0,
) -> int:
    """Wait until the fixture writes back its bound port."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if proc.poll() is not None:
            output = _collect_process_output(proc)
            raise RuntimeError(f"{service_name} failed to start with exit code {proc.returncode}: {output}")
        if port_file.exists():
            try:
                return int(port_file.read_text(encoding="utf-8").strip())
            except ValueError:
                pass
        time.sleep(0.05)

    output = _collect_process_output(proc)
    raise RuntimeError(f"{service_name} did not write its listening port within 8 seconds: {output}")


def _wait_for_http_ready(
    proc: subprocess.Popen[str],
    *,
    ready_url: str,
    service_name: str,
    ready_statuses: set[int] | None = None,
    ready_request_kwargs: dict[str, Any] | None = None,
    timeout_seconds: float = 8.0,
) -> None:
    """Poll the fixture endpoint until it is reachable."""
    request_kwargs = dict(ready_request_kwargs or {})
    accepted_statuses = set(ready_statuses or {200})
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        if proc.poll() is not None:
            output = _collect_process_output(proc)
            raise RuntimeError(f"{service_name} failed to start with exit code {proc.returncode}: {output}")
        try:
            response = requests.get(ready_url, timeout=0.5, **request_kwargs)
            if response.status_code in accepted_statuses:
                response.close()
                return
            response.close()
        except requests.RequestException:
            time.sleep(0.2)

    output = _collect_process_output(proc)
    raise RuntimeError(f"{service_name} did not become ready within 8 seconds: {output}")


@contextmanager
def running_http_mcp_server(
    fixture_server: Path,
    *,
    ready_url: str,
    service_name: str,
    extra_args: list[str],
    ready_statuses: set[int] | None = None,
    ready_request_kwargs: dict[str, Any] | None = None,
) -> Iterator[subprocess.Popen[str]]:
    """Context manager that runs a FastMCP HTTP server for one test."""
    proc = start_http_mcp_server(
        fixture_server,
        ready_url=ready_url,
        service_name=service_name,
        extra_args=extra_args,
        ready_statuses=ready_statuses,
        ready_request_kwargs=ready_request_kwargs,
    )
    try:
        yield proc
    finally:
        stop_http_mcp_server(proc)


@contextmanager
def running_http_mcp_server_on_random_port(
    fixture_server: Path,
    *,
    service_name: str,
    ready_url_builder: Callable[[int], str],
    extra_args_builder: Callable[[int], list[str]],
    ready_statuses: set[int] | None = None,
    ready_request_kwargs: dict[str, Any] | None = None,
    max_attempts: int = 5,
) -> Iterator[tuple[subprocess.Popen[str], int]]:
    """Context manager that runs a FastMCP HTTP server on a retryable free port."""
    proc, port = start_http_mcp_server_on_random_port(
        fixture_server,
        service_name=service_name,
        ready_url_builder=ready_url_builder,
        extra_args_builder=extra_args_builder,
        ready_statuses=ready_statuses,
        ready_request_kwargs=ready_request_kwargs,
        max_attempts=max_attempts,
    )
    try:
        yield proc, port
    finally:
        stop_http_mcp_server(proc)