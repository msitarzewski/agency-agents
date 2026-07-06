"""M5 — SWARM external MCP tools: trust-model regression tests.

Covers requirements R-06 and tests T-16, T-17, T-18 in
``docs/2026-05-25_swarm_mcp_tools_tdd.md``. M5 pins the contract that an
external MCP caller of ``run_swarm`` cannot influence which remote MCP
servers a worker reaches, no matter what they put in ``variables`` or
the preset YAML:

  * T-16 — the ``run_swarm`` FastMCP tool's input schema MUST NOT expose
    any field that would let a caller inject MCP server URLs, commands,
    env vars, or allowlist overrides (``mcp_servers``, ``mcp_url``,
    ``mcp_command``, ``mcp_env``, ``agent_config``, ``extra_tools``).

  * T-17 — keys in the ``variables`` dict that *look like* config keys
    (``mcp_url``, ``mcp_command``, ``agent_config`` …) are forwarded
    verbatim as template values. The worker uses them only as text
    substitutions; they are never re-read as configuration. The single
    source of MCP config is the boot-time loader
    (:func:`load_swarm_agent_config`).

  * T-18 — a preset that whitelists an ``mcp_*`` tool whose server is
    not in the boot allowlist logs an operator-facing drop warning and
    the worker still reaches a terminal state. The unknown tool is NEVER
    fetched via a caller-supplied lookup path.

The trust boundary being defended is the one called out in the roadmap
SSRF section: the operator owns ``agent_config`` (via env var or static
file on disk); the MCP caller only owns ``preset_name`` + ``variables``
which carry no config authority.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

import mcp_server
from src.config.schema import AgentConfig
from src.providers.chat import LLMResponse
from src.swarm.models import RunStatus, SwarmAgentSpec, SwarmRun, SwarmTask
from src.swarm.worker import run_worker


# --------------------------------------------------------------------------- #
# T-16 — FastMCP schema introspection (R-06)
# --------------------------------------------------------------------------- #


# Field names whose presence in ``run_swarm``'s input schema would let an
# external MCP caller inject MCP server connection details directly. They
# must never appear on the wire schema. Mirrors the SSRF guard called out
# in ``docs/2026-05-25_swarm_mcp_tools_roadmap.md``.
_FORBIDDEN_RUN_SWARM_PARAMETERS = frozenset(
    {
        "mcp_servers",
        "mcp_url",
        "mcp_command",
        "mcp_env",
        "agent_config",
        "extra_tools",
    }
)

# The exact set of parameters ``run_swarm`` is allowed to expose. ``ctx``
# is the FastMCP-supplied progress channel — it is bound by the runtime,
# never by the caller, but it does appear in the JSON-Schema signature on
# some FastMCP versions, so we allow it as a known-safe inclusion.
_ALLOWED_RUN_SWARM_PARAMETERS = frozenset(
    {"preset_name", "variables", "wait_seconds", "start_only", "ctx"}
)


def _get_run_swarm_tool_schema() -> dict[str, Any]:
    """Return the JSON-Schema for ``run_swarm`` via FastMCP introspection.

    Uses the public ``FastMCP.get_tool`` API so the test exercises the
    schema *as an external client would observe it* — same code path
    that produces the ``tools/list`` payload over the wire.
    """
    tool = asyncio.run(mcp_server.mcp.get_tool("run_swarm"))
    return tool.parameters


def test_run_swarm_schema_excludes_mcp_config_injection_fields() -> None:
    """The wire schema for ``run_swarm`` must not name any config fields.

    A future refactor that adds e.g. ``mcp_url`` as a parameter would
    silently turn the swarm entry point into an SSRF primitive — every
    MCP caller could redirect a worker to a server of their choosing.
    The boot-time loader is the only authority for that config, by
    design, and this test pins that design at the schema level.
    """
    schema = _get_run_swarm_tool_schema()
    properties = schema.get("properties", {})

    leaks = sorted(_FORBIDDEN_RUN_SWARM_PARAMETERS & set(properties.keys()))
    assert not leaks, (
        f"run_swarm exposes forbidden config-injection field(s): {leaks}. "
        "These let a caller override MCP server config — boot-time loader "
        "must remain the only authority. See docs/2026-05-25_swarm_mcp_tools_roadmap.md."
    )


def test_run_swarm_schema_only_exposes_known_safe_parameters() -> None:
    """Defense-in-depth: flag any *new* parameter for explicit review.

    The forbidden-list test above catches the names we know to fear.
    This test catches the names we *haven't* thought to fear yet — any
    new parameter that doesn't appear on the allowlist forces a code
    review of whether it expands the trust surface.
    """
    schema = _get_run_swarm_tool_schema()
    properties = set(schema.get("properties", {}).keys())

    unexpected = sorted(properties - _ALLOWED_RUN_SWARM_PARAMETERS)
    assert not unexpected, (
        f"run_swarm gained unexpected parameter(s): {unexpected}. "
        "Review whether they expand the trust surface before adding them "
        "to _ALLOWED_RUN_SWARM_PARAMETERS in this test."
    )


# --------------------------------------------------------------------------- #
# T-17 — variables are template data; never re-read as config (S-04 / R-06)
# --------------------------------------------------------------------------- #


def test_run_swarm_variables_are_template_data_only_never_config(
    monkeypatch, tmp_path: Path
) -> None:
    """A caller that stuffs ``variables`` with config-shaped keys cannot
    influence which MCP server the worker reaches.

    The check is two-sided:

      1. ``SwarmRuntime`` is constructed with the ``agent_config`` returned
         by the boot-time loader — not anything derived from the caller's
         ``variables``. We pin this by patching the loader to return a
         distinct sentinel object and asserting the runtime saw exactly
         that object.

      2. ``runtime.start_run`` receives the caller's ``variables`` dict
         verbatim, with all the attack-shaped keys preserved. They flow
         into ``SwarmRun.user_vars`` and from there into the prompt
         template — they are *data*, not config. The worker has no path
         by which ``variables["mcp_url"]`` becomes a server URL.
    """
    # Step 1 — pin the boot-time config source as a sentinel.
    boot_cfg = AgentConfig.model_validate({"mcpServers": {}})

    def _loader_returns_sentinel() -> AgentConfig:
        return boot_cfg

    monkeypatch.setattr(
        "src.config.load_swarm_agent_config", _loader_returns_sentinel
    )

    # Step 2 — pin the SwarmStore base dir to a tmp path so the test
    # never touches the repo-level ``.swarm/runs`` directory.
    monkeypatch.setattr(
        "src.swarm.store.swarm_runs_root", lambda: tmp_path / "swarm_runs"
    )

    captured: dict[str, Any] = {}

    class _SpyRuntime:
        """Record construction + start_run args; return a stub SwarmRun."""

        def __init__(
            self,
            *,
            store: Any,
            agent_config: AgentConfig | None = None,
            max_workers: int = 4,
        ) -> None:
            captured["construct_agent_config"] = agent_config
            captured["construct_store"] = store

        def start_run(
            self,
            preset_name: str,
            user_vars: dict[str, str],
            include_shell_tools: bool = False,
        ) -> SwarmRun:
            captured["start_preset"] = preset_name
            captured["start_user_vars"] = dict(user_vars)
            captured["start_include_shell_tools"] = include_shell_tools
            return SwarmRun(
                id="swarm-test-trustcheck",
                preset_name=preset_name,
                status=RunStatus.pending,
                user_vars=user_vars,
                agents=[],
                tasks=[],
                created_at="2026-05-25T00:00:00+00:00",
            )

    monkeypatch.setattr("src.swarm.runtime.SwarmRuntime", _SpyRuntime)

    # ``_build_run_payload`` calls store.load_run(run_id) which won't know
    # about our stub run — short-circuit it so the test focuses on the
    # trust-side captures (construction + start_run forwarding).
    monkeypatch.setattr(
        mcp_server,
        "_build_run_payload",
        lambda store, run_id, preset_name, *, timed_out: {
            "status": "pending",
            "run_id": run_id,
            "preset": preset_name,
        },
    )

    # An ``variables`` payload crafted to look like a config-injection
    # attempt. The attacker hopes the runtime treats ``mcp_url`` /
    # ``mcp_command`` as MCP server config; the worker must instead
    # treat every key as a plain template variable.
    attack_vars = {
        "mcp_url": "http://attacker.example/evil",
        "mcp_command": "rm -rf /",
        "mcp_servers": '{"evil": {"command": "bash"}}',
        "mcp_env": "EVIL_API_KEY=stolen",
        "agent_config": '{"mcpServers": {"evil": "..."}}',
        "extra_tools": "mcp_evil_anything",
        # A legitimate template variable so the preset *could* render.
        "target": "AAPL.US",
    }

    asyncio.run(
        mcp_server.run_swarm(
            preset_name="any_preset_name",
            variables=attack_vars,
            start_only=True,
        )
    )

    # Trust check #1: the boot-time loader was the source of agent_config.
    # The runtime saw the exact sentinel object — no copy, no derivation
    # from the caller's variables.
    assert "construct_agent_config" in captured, (
        "run_swarm did not construct SwarmRuntime; trust path likely broken."
    )
    assert captured["construct_agent_config"] is boot_cfg, (
        "SwarmRuntime was constructed with a different AgentConfig than the "
        "boot-time loader returned. The caller's variables must NEVER reach "
        "this argument."
    )

    # Trust check #2: variables were forwarded verbatim as template data.
    # Every attack-shaped key is preserved as a plain string — they will
    # end up in ``SwarmRun.user_vars`` and be rendered into the prompt as
    # text, never consulted as configuration.
    assert captured["start_user_vars"] == attack_vars, (
        "variables were mutated, filtered, or otherwise touched on the "
        "way to start_run. They must arrive verbatim — the trust model "
        "depends on the worker treating them as opaque text."
    )

    # Trust check #3: the preset name was the literal user-supplied
    # string. The caller picks the preset; that's expected and bounded
    # by the on-disk preset catalogue.
    assert captured["start_preset"] == "any_preset_name"


# --------------------------------------------------------------------------- #
# T-18 — preset-referenced ``mcp_*`` tool whose server is not in the boot
#         allowlist drops with a warning; worker still reaches a terminal
#         state; caller-supplied attack-shaped variables are NOT consulted
#         as a fallback config source.
# --------------------------------------------------------------------------- #


class _StubChatLLM:
    """Minimal scripted replacement for :class:`ChatLLM`.

    The worker only needs the LLM to produce a final response for this
    test — we never want the LLM to *use* the dropped tool. Captures
    the ``tools=`` argument so we can verify the dropped MCP tool was
    not handed to the LLM either.
    """

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self.tool_defs_seen: list[list[dict] | None] = []

    def __call__(self, *args, **kwargs):  # ChatLLM(model_name=...) constructor shim
        return self

    def stream_chat(self, messages, tools=None, on_text_chunk=None, timeout=None):
        self.tool_defs_seen.append(tools)
        if not self._responses:
            return LLMResponse(content="(stub exhausted)", finish_reason="stop")
        return self._responses.pop(0)

    def chat(self, messages, tools=None, timeout=None):  # pragma: no cover
        return self.stream_chat(messages, tools=tools)


def _stub_llm_factory(responses: list[LLMResponse]):
    stub = _StubChatLLM(responses)

    def _factory(model_name=None):
        return stub

    _factory.stub = stub  # type: ignore[attr-defined]
    return _factory


def _llm_tool_names(tool_defs: list[dict] | None) -> set[str]:
    """Extract tool names from an OpenAI-format tool-definitions list."""
    if not tool_defs:
        return set()
    names: set[str] = set()
    for entry in tool_defs:
        fn = entry.get("function") if isinstance(entry, dict) else None
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.add(fn["name"])
    return names


def test_unknown_mcp_server_tool_drops_cleanly_with_attack_shaped_variables(
    tmp_path: Path,
    caplog,
) -> None:
    """A preset that names an ``mcp_*`` tool whose server is absent from
    the boot allowlist must drop the tool with an operator-facing warning,
    NOT silently look it up from the caller's ``variables`` dict.

    Setup mirrors what an attacker would attempt:

      * Boot ``agent_config`` lists *no* MCP servers — the operator has
        not approved anything.
      * The agent's whitelist names ``mcp_attacker_evil_tool`` (perhaps
        injected via a preset PR the operator did not review carefully).
      * ``user_vars`` contains attacker-shaped keys
        (``mcp_attacker_url``, ``mcp_attacker_command``, …) that a
        broken implementation might treat as a fallback lookup source.

    The worker must:

      * Drop ``mcp_attacker_evil_tool`` with a warning (M2 contract,
        re-pinned here at the worker integration layer).
      * NOT hand ``mcp_attacker_evil_tool`` to the LLM (no leaked
        capability surface).
      * Reach a terminal state without crashing — variables are opaque
        text, not config.
      * NEVER trigger MCP wrapper construction for an attacker-named
        server — the only authority for which servers exist is the
        boot ``agent_config``.
    """
    # Boot allowlist is empty: operator has approved zero MCP servers.
    boot_cfg = AgentConfig.model_validate({"mcpServers": {}})

    # The LLM stub returns a final response immediately — we don't want
    # it to call the dropped tool (it shouldn't be able to: dropped tools
    # are absent from ``tools=``).
    llm_factory = _stub_llm_factory(
        [LLMResponse(content="No remote tool available; analysis skipped.", finish_reason="stop")]
    )

    # Spy on the MCP wrapper builder. With an empty boot allowlist the
    # worker must NEVER call this — no server to wrap. If the test sees
    # any call, the trust boundary has been crossed.
    wrapper_calls: list[tuple] = []

    def _spy_build_mcp_tool_wrappers(*args, **kwargs):  # pragma: no cover — should not run
        wrapper_calls.append((args, kwargs))
        return []

    attack_vars = {
        "mcp_attacker_url": "http://attacker.example",
        "mcp_attacker_command": "rm -rf /",
        "agent_config": '{"mcpServers": {"attacker": ...}}',
        "target": "AAPL.US",
    }

    with (
        patch("src.tools.mcp.build_mcp_tool_wrappers", side_effect=_spy_build_mcp_tool_wrappers),
        patch("src.swarm.worker.ChatLLM", llm_factory),
        caplog.at_level(logging.WARNING),
    ):
        result = run_worker(
            agent_spec=SwarmAgentSpec(
                id="kb_analyst",
                role="Analyst",
                system_prompt="Analyse markets.",
                tools=["mcp_attacker_evil_tool", "write_file"],
                skills=[],
                max_iterations=3,
                timeout_seconds=30,
            ),
            task=SwarmTask(
                id="t1",
                agent_id="kb_analyst",
                prompt_template="Analyse {target}.",
            ),
            upstream_summaries={},
            user_vars=attack_vars,
            run_dir=tmp_path,
            agent_config=boot_cfg,
        )

    # The worker reached a terminal state — variables didn't crash the
    # pipeline by being misinterpreted as config.
    assert result.status in {"completed", "incomplete"}, (
        f"Worker did not reach a clean terminal state: status={result.status}, "
        f"error={getattr(result, 'error', None)!r}"
    )

    # Operator-facing drop warning fired for the unknown MCP tool —
    # standard M2 contract, re-checked here from the worker entry point.
    drop_warnings = [
        rec for rec in caplog.records
        if "mcp_attacker_evil_tool" in rec.message and "unavailable" in rec.message
    ]
    assert drop_warnings, (
        "Expected an 'unavailable' drop warning for mcp_attacker_evil_tool. "
        f"Got log records: {[(r.levelname, r.message) for r in caplog.records]}"
    )

    # The LLM was never handed the dropped tool — capability isolation
    # holds at the layer that actually matters (what the model can see).
    first_seen = llm_factory.stub.tool_defs_seen[0]  # type: ignore[attr-defined]
    seen_names = _llm_tool_names(first_seen)
    assert "mcp_attacker_evil_tool" not in seen_names, (
        f"Dropped MCP tool leaked into LLM tools= argument: {sorted(seen_names)}"
    )
    # Local tool that the preset legitimately requested *was* exposed.
    assert "write_file" in seen_names, (
        f"Local write_file should remain available; LLM saw: {sorted(seen_names)}"
    )

    # Trust check: even though the caller stuffed attacker-shaped keys
    # into variables, no MCP wrapper was ever built for an attacker
    # server. The only authority for "which servers exist" is the boot
    # ``agent_config`` — which is empty in this test.
    assert wrapper_calls == [], (
        f"build_mcp_tool_wrappers was called {len(wrapper_calls)} time(s) "
        "despite boot allowlist being empty; trust boundary breached: "
        f"{wrapper_calls!r}"
    )
