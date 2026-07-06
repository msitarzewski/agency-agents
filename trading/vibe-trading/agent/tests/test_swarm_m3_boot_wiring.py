"""M3 — SWARM external MCP tools: boot wiring & config resolution.

Covers requirements R-09 (lazy boot discovery) and tests T-08, T-09, T-10, T-11
in ``docs/2026-05-25_swarm_mcp_tools_tdd.md``. M3 introduces the boot-time
config resolver that lets operators point a swarm-only MCP allowlist at a
distinct file from the main agent config.

The contract this file defends:

  * ``VIBE_TRADING_SWARM_AGENT_CONFIG`` env var, when set, wins absolutely —
    even if neighbouring ``swarm-agent.json`` / ``agent.json`` exist on disk.
  * Without the env var, ``~/.vibe-trading/swarm-agent.json`` (the swarm-
    specific operator file) is preferred over ``agent.json``.
  * Without either swarm-specific file, ``~/.vibe-trading/agent.json``
    (the main-agent config) is reused as a sane default — operators with a
    single-config setup don't have to duplicate it.
  * With nothing on disk and no env var, the resolver returns ``None`` so the
    runtime keeps today's local-only behaviour byte-for-byte (R-03).

Tests use ``tmp_path`` to redirect the runtime root so they never touch the
real ``~/.vibe-trading`` directory of whoever is running the suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import AgentConfig
from src.config.loader import (
    _resolve_swarm_agent_config_path,
    load_swarm_agent_config,
)


def _write_agent_json(path: Path, server_name: str) -> None:
    """Write a minimal AgentConfig JSON file pinning a single MCP server.

    The server name is used in assertions to verify *which* file the resolver
    picked up — that's how we tell ``swarm-agent.json`` apart from
    ``agent.json`` even when both exist on disk.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    server_name: {"command": "uvx", "args": [f"{server_name}-server"]}
                }
            }
        ),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# T-08 — env var wins absolutely (S-10)
# --------------------------------------------------------------------------- #


def test_resolve_swarm_agent_config_path_uses_env_var_when_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``VIBE_TRADING_SWARM_AGENT_CONFIG`` is the absolute first-priority source.

    An operator who explicitly points the env var at a custom file MUST get
    that file even if the well-known ``swarm-agent.json`` and ``agent.json``
    happen to exist alongside. The env var is the override hatch for CI /
    sandbox deployments where the runtime root is read-only.
    """
    runtime_root = tmp_path / "runtime"
    env_pointed = tmp_path / "external" / "operator-swarm.json"
    _write_agent_json(env_pointed, "env_pointed")
    _write_agent_json(runtime_root / "swarm-agent.json", "swarm_specific")
    _write_agent_json(runtime_root / "agent.json", "main_agent")
    monkeypatch.setenv("VIBE_TRADING_SWARM_AGENT_CONFIG", str(env_pointed))

    resolved = _resolve_swarm_agent_config_path(runtime_root=runtime_root)

    assert resolved == env_pointed


# --------------------------------------------------------------------------- #
# T-09 — swarm-agent.json beats agent.json when env unset (S-11)
# --------------------------------------------------------------------------- #


def test_resolve_swarm_agent_config_path_prefers_swarm_specific_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``swarm-agent.json`` shadows ``agent.json`` when both are present.

    Operators express "I want the swarm path to use a different MCP allowlist
    from the main agent" by dropping a ``swarm-agent.json`` next to the main
    config. When that file exists, the main ``agent.json`` is *ignored* for
    swarm — preventing accidental cross-pollination of allowlists.
    """
    monkeypatch.delenv("VIBE_TRADING_SWARM_AGENT_CONFIG", raising=False)
    runtime_root = tmp_path / "runtime"
    _write_agent_json(runtime_root / "swarm-agent.json", "swarm_specific")
    _write_agent_json(runtime_root / "agent.json", "main_agent")

    resolved = _resolve_swarm_agent_config_path(runtime_root=runtime_root)

    assert resolved == runtime_root / "swarm-agent.json"


# --------------------------------------------------------------------------- #
# T-10 — agent.json fallback (S-12)
# --------------------------------------------------------------------------- #


def test_resolve_swarm_agent_config_path_falls_back_to_main_agent_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``agent.json`` is reused when no swarm-specific file is provided.

    Single-config operators (the common case during early adoption) shouldn't
    have to duplicate their MCP allowlist. The resolver gracefully falls back
    to the main ``agent.json`` so the operator's existing configuration stays
    the source of truth for both code paths.
    """
    monkeypatch.delenv("VIBE_TRADING_SWARM_AGENT_CONFIG", raising=False)
    runtime_root = tmp_path / "runtime"
    _write_agent_json(runtime_root / "agent.json", "main_agent")

    resolved = _resolve_swarm_agent_config_path(runtime_root=runtime_root)

    assert resolved == runtime_root / "agent.json"


# --------------------------------------------------------------------------- #
# T-11 — nothing configured → None (S-13, R-03)
# --------------------------------------------------------------------------- #


def test_resolve_swarm_agent_config_path_returns_none_when_nothing_configured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No env var, no on-disk files → resolver returns ``None``.

    This preserves the byte-for-byte legacy behaviour from R-03: a fresh
    install with no operator config keeps the swarm strictly local-tool-only.
    A ``None`` resolution flows through to ``SwarmRuntime(agent_config=None)``
    which the M1/M2 plumbing already handles.
    """
    monkeypatch.delenv("VIBE_TRADING_SWARM_AGENT_CONFIG", raising=False)
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()

    resolved = _resolve_swarm_agent_config_path(runtime_root=runtime_root)

    assert resolved is None


# --------------------------------------------------------------------------- #
# Integration: load_swarm_agent_config returns AgentConfig at every level
# --------------------------------------------------------------------------- #


def test_load_swarm_agent_config_returns_default_when_unconfigured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Boot wiring stays safe even with no operator config on disk.

    The boot helpers in ``mcp_server.py`` / ``api_server.py`` / CLI runners
    call ``load_swarm_agent_config()`` at startup, then forward the result
    into ``SwarmRuntime(agent_config=...)``. When nothing is configured, the
    result is an empty ``AgentConfig()`` whose ``mcp_servers`` dict is empty —
    ``build_swarm_registry`` already treats that case identically to ``None``
    (verified by the M2 ``test_build_swarm_registry_with_empty_mcp_servers_is_local_only``).
    """
    monkeypatch.delenv("VIBE_TRADING_SWARM_AGENT_CONFIG", raising=False)
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()

    config = load_swarm_agent_config(runtime_root=runtime_root)

    assert isinstance(config, AgentConfig)
    assert config.mcp_servers == {}


def test_load_swarm_agent_config_loads_swarm_specific_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``swarm-agent.json`` exists, its servers are validated and loaded.

    End-to-end check that the resolver + loader integrates cleanly: the
    ``swarm_specific`` server name we pinned in the file is the one that
    surfaces on the returned ``AgentConfig.mcp_servers`` mapping.
    """
    monkeypatch.delenv("VIBE_TRADING_SWARM_AGENT_CONFIG", raising=False)
    runtime_root = tmp_path / "runtime"
    _write_agent_json(runtime_root / "swarm-agent.json", "swarm_specific")
    _write_agent_json(runtime_root / "agent.json", "main_agent")

    config = load_swarm_agent_config(runtime_root=runtime_root)

    assert "swarm_specific" in config.mcp_servers
    assert "main_agent" not in config.mcp_servers
