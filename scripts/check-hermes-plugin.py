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


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingContext:
    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def register_tool(self, **kwargs: Any) -> None:
        self.tools[kwargs["name"]] = kwargs


def main() -> int:
    builder = load_module("agency_agents_hermes_builder", BUILDER_PATH)

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "hermes"
        builder.build(REPO_ROOT, out_dir)
        plugin = load_module(
            "agency_agents_router_check",
            out_dir / builder.PLUGIN_NAME / "__init__.py",
        )

        ctx = RecordingContext()
        plugin.register(ctx)

        expected_tools = {
            "agency_agents_search",
            "agency_agents_inspect",
            "agency_agents_load",
            "agency_agents_delegate",
        }
        assert set(ctx.tools) == expected_tools

        for name, registration in ctx.tools.items():
            schema = registration["schema"]
            assert schema["name"] == name, f"{name}: schema name is missing"
            assert schema.get("description"), f"{name}: schema description is missing"
            parameters = schema.get("parameters")
            assert isinstance(parameters, dict), f"{name}: schema.parameters is missing"
            assert parameters.get("type") == "object", f"{name}: parameters must be an object"
            assert isinstance(parameters.get("properties"), dict), f"{name}: properties are missing"
            assert isinstance(parameters.get("required"), list), f"{name}: required must be a list"

        search = json.loads(
            ctx.tools["agency_agents_search"]["handler"]({"query": "backend architecture"})
        )
        assert search["success"] is True
        assert search["results"], "search should return at least one specialist"

        slug = search["results"][0]["slug"]
        inspected = json.loads(
            ctx.tools["agency_agents_inspect"]["handler"]({"slug": slug})
        )
        assert inspected["success"] is True
        assert inspected["agent"]["slug"] == slug

    print("PASSED: generated Hermes plugin schemas and routing behavior are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
