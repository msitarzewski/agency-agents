#!/usr/bin/env python3
"""Validate the generated Hermes router plugin against Hermes' tool contract."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts" / "build-hermes-plugin.py"

EXPECTED_TOOLS = {
    "agency_agents_search",
    "agency_agents_inspect",
    "agency_agents_load",
    "agency_agents_delegate",
}


def load_module(name: str, path: Path):
    """Load a Python module directly from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingContext:
    """Minimal Hermes context used to record registered tools."""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def register_tool(self, **kwargs: Any) -> None:
        name = kwargs.get("name")

        if not name:
            raise ValueError("Tool registration is missing a name")

        self.tools[name] = kwargs


def validate_tool_schema(name: str, registration: dict[str, Any]) -> None:
    """Validate the schema for a registered Hermes tool."""
    schema = registration.get("schema")

    assert isinstance(schema, dict), f"{name}: schema is missing"
    assert schema.get("name") == name, f"{name}: schema name is missing"
    assert schema.get("description"), f"{name}: schema description is missing"

    parameters = schema.get("parameters")
    assert isinstance(parameters, dict), (
        f"{name}: schema.parameters is missing"
    )
    assert parameters.get("type") == "object", (
        f"{name}: parameters must be an object"
    )
    assert isinstance(parameters.get("properties"), dict), (
        f"{name}: properties are missing"
    )
    assert isinstance(parameters.get("required"), list), (
        f"{name}: required must be a list"
    )


def call_tool(
    tools: dict[str, dict[str, Any]],
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Call a registered tool and decode its JSON response."""
    handler = tools[name].get("handler")

    assert callable(handler), f"{name}: handler is missing"

    response = handler(arguments)

    assert isinstance(response, str), (
        f"{name}: handler must return a JSON string"
    )

    result = json.loads(response)
    assert isinstance(result, dict), (
        f"{name}: handler response must be a JSON object"
    )

    return result


def validate_plugin(builder: Any, plugin: Any) -> None:
    """Validate tool registration, schemas, and basic routing behavior."""
    context = RecordingContext()
    plugin.register(context)

    assert set(context.tools) == EXPECTED_TOOLS, (
        f"Unexpected tools registered: {set(context.tools)}"
    )

    for name, registration in context.tools.items():
        validate_tool_schema(name, registration)

    search = call_tool(
        context.tools,
        "agency_agents_search",
        {"query": "backend architecture"},
    )

    assert search.get("success") is True, "search should succeed"

    results = search.get("results")
    assert isinstance(results, list) and results, (
        "search should return at least one specialist"
    )

    slug = results[0].get("slug")
    assert slug, "search result is missing a slug"

    inspected = call_tool(
        context.tools,
        "agency_agents_inspect",
        {"slug": slug},
    )

    assert inspected.get("success") is True, "inspect should succeed"

    agent = inspected.get("agent")
    assert isinstance(agent, dict), "inspect response is missing agent"
    assert agent.get("slug") == slug, (
        "inspect should return the requested specialist"
    )


def main() -> int:
    """Build the plugin and validate the generated implementation."""
    builder = load_module(
        "agency_agents_hermes_builder",
        BUILDER_PATH,
    )

    with tempfile.TemporaryDirectory(prefix="hermes-router-") as tmp:
        output_dir = Path(tmp) / "hermes"

        builder.build(REPO_ROOT, output_dir)

        plugin_path = (
            output_dir
            / builder.PLUGIN_NAME
            / "__init__.py"
        )

        plugin = load_module(
            "agency_agents_router_check",
            plugin_path,
        )

        validate_plugin(builder, plugin)

    print(
        "PASSED: generated Hermes plugin schemas "
        "and routing behavior are valid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
