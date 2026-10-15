#!/usr/bin/env python3
"""Validate tools.json against schema/tools.schema.json.

Pure-stdlib JSON Schema validator for the subset the tool catalog uses
(type, required, properties, additionalProperties, enum, pattern, minLength,
minProperties, items, one-level $ref). No external deps — matches the repo's
"no deps beyond coreutils" stance, and runs identically on CI and local.

Usage: python3 scripts/check-tools-schema.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = REPO_ROOT / "tools.json"
SCHEMA = REPO_ROOT / "schema" / "tools.schema.json"


class SchemaError(Exception):
    pass


def _resolve(node: Any, root: dict[str, Any]) -> dict[str, Any]:
    """Resolve a one-level $ref (only refs into #/definitions are used)."""
    if isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/definitions/"):
            raise SchemaError(f"unsupported $ref: {ref}")
        name = ref[len("#/definitions/"):]
        target = root.get("definitions", {}).get(name)
        if target is None:
            raise SchemaError(f"unknown $ref target: {name}")
        return target
    return node


def _validate_type(value: Any, expected: str | list[str]) -> bool:
    types = [expected] if isinstance(expected, str) else expected
    for t in types:
        if t == "string" and isinstance(value, str):
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "object" and isinstance(value, dict):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "null" and value is None:
            return True
    return False


def validate(value: Any, node: Any, root: dict[str, Any], path: str, errors: list[str]) -> None:
    node = _resolve(node, root)

    if "type" in node and not _validate_type(value, node["type"]):
        errors.append(f"{path}: expected type {node['type']}, got {type(value).__name__}")
        return

    if isinstance(value, dict):
        for field in node.get("required", []):
            if field not in value:
                errors.append(f"{path}: missing required field '{field}'")
        if "minProperties" in node and len(value) < node["minProperties"]:
            errors.append(f"{path}: expected >= {node['minProperties']} properties")
        props = node.get("properties", {})
        addl = node.get("additionalProperties", True)
        for key, sub in value.items():
            subpath = f"{path}.{key}" if path else key
            if key in props:
                validate(sub, props[key], root, subpath, errors)
            elif addl is True:
                continue
            elif isinstance(addl, dict):
                validate(sub, addl, root, subpath, errors)
            else:
                errors.append(f"{subpath}: unexpected property '{key}'")

    if isinstance(value, list) and "items" in node:
        for i, item in enumerate(value):
            validate(item, node["items"], root, f"{path}[{i}]", errors)

    if "enum" in node and value not in node["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {node['enum']}")

    if "pattern" in node and isinstance(value, str):
        if not re.search(node["pattern"], value):
            errors.append(f"{path}: {value!r} does not match pattern {node['pattern']}")

    if "minLength" in node and isinstance(value, str) and len(value) < node["minLength"]:
        errors.append(f"{path}: length {len(value)} < minLength {node['minLength']}")


def main() -> int:
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {e}")
        return 1

    errors: list[str] = []
    validate(catalog, schema, schema, "", errors)

    if errors:
        print(f"FAILED: {len(errors)} schema violation(s).")
        for e in errors:
            print(f"  - {e}")
        return 1

    n = len(catalog.get("tools", {}))
    print(f"PASSED: tools.json ({n} tools) conforms to schema/tools.schema.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
