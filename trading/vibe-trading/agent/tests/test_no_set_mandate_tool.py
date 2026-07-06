"""Structural guarantee: nothing the agent can reach writes the mandate store.

Mirrors the BROKERS.md method-name-regex gate. Two checks:

1. **Name-regex AST scan** over ``src/live/`` (and ``src/tools/``): no function
   or method matches the forbidden self-authorization regex. The single
   legitimate writer (the consent commit path, ``src/live/mandate/commit.py``,
   owned by a different parcel) is named ``commit_mandate`` — deliberately NOT
   matching ``^(_)?(set|write|update|grant|authorize|enable|widen)_...`` — and
   is exempted by name + by not being importable as a tool.
2. **No agent-reachable write path** opens ``mandate.json`` for write. We AST-
   scan the modules the agent loop *can* import (``src/live/order_guard.py``,
   ``src/live/enforcement.py``, ``src/live/extractors/``) for any ``open(...)``
   in a write mode targeting the mandate file, and assert the mandate store
   module exposes no ``save``/``set`` symbol.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import src.live.mandate.store as store

AGENT_DIR = Path(__file__).resolve().parent.parent
LIVE_DIR = AGENT_DIR / "src" / "live"
TRADING_DIR = AGENT_DIR / "src" / "trading"

_FORBIDDEN_NAME = re.compile(
    r"^(_)?(set|write|update|grant|authorize|enable|widen)_(mandate|limit|live|authorization)([_a-z]*)?$"
)

#: Known-legitimate functions whose names collide with the broad regex but do
#: NOT write the mandate store. ``write_live_action`` (P5) appends to the
#: append-only AUDIT ledger — it has no mandate write path. Exempting by exact
#: name keeps the security regex strict (it still catches any real
#: ``write_mandate`` / ``enable_live`` etc.) without a false positive.
_NAME_ALLOWLIST = {"write_live_action"}


def _py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def test_no_self_authorization_named_function_in_live() -> None:
    offenders: list[str] = []
    for path in _py_files(LIVE_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in _NAME_ALLOWLIST:
                    continue
                if _FORBIDDEN_NAME.match(node.name):
                    offenders.append(f"{path.name}:{node.name}")
    assert not offenders, f"forbidden mandate-write function names: {offenders}"


def test_store_exposes_no_write_symbol() -> None:
    public = [name for name in dir(store) if not name.startswith("_")]
    for forbidden in ("save_mandate", "set_mandate", "write_mandate", "update_mandate"):
        assert forbidden not in public, f"{forbidden} must not exist in the store module"
    # The only public callable is the read-only loader.
    assert "load_mandate" in public


def test_agent_reachable_modules_never_open_mandate_for_write() -> None:
    """No agent-importable live module opens the mandate file in a write mode."""
    reachable = [
        LIVE_DIR / "order_guard.py",
        LIVE_DIR / "enforcement.py",
        LIVE_DIR / "extractors" / "__init__.py",
        TRADING_DIR / "connectors" / "robinhood" / "extractor.py",
        LIVE_DIR / "mandate" / "store.py",
    ]
    write_modes = {"w", "wb", "a", "ab", "w+", "r+", "x"}
    offenders: list[str] = []
    for path in reachable:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_open = (isinstance(func, ast.Name) and func.id == "open") or (
                isinstance(func, ast.Attribute) and func.attr == "open"
            )
            if not is_open:
                continue
            # mode may be positional[1] or keyword 'mode'
            mode = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if isinstance(mode, str) and mode in write_modes:
                # Allowed: trade_counter.json writes in order_guard (NOT the mandate).
                src_seg = ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
                offenders.append(f"{path.name}: open(..., {mode!r}) [{src_seg[:60]}]")
    # order_guard writes trade_counter.json via Path.write_text/replace, not open();
    # the only open() write any reachable module performs would be a violation.
    assert not offenders, f"agent-reachable write opens found: {offenders}"


def test_registry_has_no_mandate_write_tool() -> None:
    """The assembled tool registry exposes no tool that can write a mandate."""
    from src.tools import build_registry

    registry = build_registry()
    names = list(getattr(registry, "_tools", {}).keys())
    for name in names:
        assert not _FORBIDDEN_NAME.match(name), f"tool {name!r} matches forbidden write regex"
        assert "set_mandate" not in name and "commit_mandate" not in name
