"""AST-based purity gate over ``agent/src/factors/zoo/**/*.py``.

Enforces the Alpha-Zoo pure-function contract (see
``docs/alpha-zoo/spec.md`` §"Alpha 纯函数契约"):

* Allowed imports (whitelist): ``pandas``, ``numpy``, ``scipy[.*]``,
  ``src.factors.base``, ``__future__``, ``typing``, ``math``, ``dataclasses``.
* Forbidden names (anywhere in the module — load, attribute access, string
  argument of ``getattr``): ``os``, ``sys``, ``subprocess``, ``socket``,
  ``urllib``, ``requests``, ``httpx``, ``aiohttp``, ``pathlib``, ``Path``,
  ``open``, ``eval``, ``exec``, ``compile``, ``__import__``, plus any
  ``getattr(obj, "__...")`` string-arg dunder access.
* Module-level statements: only ``import`` / ``from ... import`` / function
  definitions / ``ALPHA_ID = "..."`` or ``__alpha_meta__ = {...}`` / module
  docstring. No top-level classes, ``if``, calls, or other statements.

Each ``.py`` file becomes its own parametrized case so violations are
isolated and reported one-by-one. When the zoo is empty (current state of
the repo), the suite emits a single ``pytest.skip``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


# ---------------------------------------------------------------- constants


ZOO_ROOT = Path(__file__).resolve().parents[2] / "src" / "factors" / "zoo"

_ALLOWED_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "pandas",
        "numpy",
        "scipy",
        "__future__",
        "typing",
        "math",
        "dataclasses",
    }
)
# ``src.factors.base`` is the only operator import accepted from this repo.
_ALLOWED_REPO_IMPORT = "src.factors.base"

_FORBIDDEN_NAMES: frozenset[str] = frozenset(
    {
        # I/O & system surface
        "os",
        "sys",
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "httpx",
        "aiohttp",
        "pathlib",
        "Path",
        "open",
        # Code evaluation / import escape hatches
        "eval",
        "exec",
        "compile",
        "__import__",
        "breakpoint",
        "input",
        "help",
        "memoryview",
        # Reflection-based introspection ladders that can reach
        # ``os`` / ``__import__`` via ``().__class__.__base__.__subclasses__()``.
        "globals",
        "locals",
        "vars",
        # Dunder ladders themselves (matched as attribute access too).
        "__class__",
        "__base__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__globals__",
        "__builtins__",
    }
)


# ---------------------------------------------------------------- helpers


def _discover_alpha_files() -> list[Path]:
    """Return every ``zoo/**/<alpha>.py`` candidate (skips ``__init__`` and ``_*``)."""
    if not ZOO_ROOT.is_dir():
        return []
    out: list[Path] = []
    for path in sorted(ZOO_ROOT.rglob("*.py")):
        if path.name == "__init__.py" or path.name.startswith("_"):
            continue
        # Skip anything inside a __pycache__ tree just in case.
        if "__pycache__" in path.parts:
            continue
        out.append(path)
    return out


def _is_allowed_import(module: str) -> bool:
    """Decide whether an import statement target is on the whitelist."""
    if not module:
        return False
    if module == _ALLOWED_REPO_IMPORT:
        return True
    head = module.split(".", 1)[0]
    return head in _ALLOWED_IMPORT_ROOTS


def _format_violations(path: Path, violations: list[str]) -> str:
    rel = path.relative_to(ZOO_ROOT.parent.parent.parent)
    body = "\n  - ".join(violations)
    return f"{rel}:\n  - {body}"


# ---------------------------------------------------------------- visitor


class _PurityVisitor(ast.NodeVisitor):
    """Collect every purity violation in a zoo alpha module."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    # ---- imports ---------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            if not _is_allowed_import(alias.name):
                self.violations.append(
                    f"L{node.lineno}: disallowed import {alias.name!r}"
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.level and node.level > 0:
            self.violations.append(
                f"L{node.lineno}: relative imports are forbidden in zoo modules"
            )
            return
        module = node.module or ""
        if not _is_allowed_import(module):
            self.violations.append(
                f"L{node.lineno}: disallowed import-from {module!r}"
            )

    # ---- name references ------------------------------------------

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if node.id in _FORBIDDEN_NAMES:
            self.violations.append(
                f"L{node.lineno}: forbidden name reference {node.id!r}"
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        # Catch ``os.path``, ``pathlib.Path``, ``__class__.__bases__`` etc.
        if node.attr in _FORBIDDEN_NAMES:
            self.violations.append(
                f"L{node.lineno}: forbidden attribute access .{node.attr!r}"
            )
        self.generic_visit(node)

    # ---- getattr(x, "...") trapdoor -------------------------------

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        func = node.func
        if isinstance(func, ast.Name) and func.id == "getattr":
            # Second arg MUST be an ``ast.Constant`` — any computed string
            # (``"__cl" + "ass__"``, f-strings, name lookups, ``chr(95)`` calls)
            # is rejected because it would let an attacker assemble a dunder
            # name past the literal check.
            if len(node.args) >= 2:
                second = node.args[1]
                if not isinstance(second, ast.Constant):
                    self.violations.append(
                        f"L{node.lineno}: getattr(..., <{type(second).__name__}>) "
                        f"— second arg must be a string literal (no BinOp / "
                        f"Name / f-string evasion)"
                    )
                else:
                    value = second.value
                    if isinstance(value, str) and value.startswith("__"):
                        self.violations.append(
                            f"L{node.lineno}: getattr(..., {value!r}) "
                            f"— dunder string args are forbidden"
                        )
        self.generic_visit(node)


# ---------------------------------------------------------------- module-level


def _check_module_body(tree: ast.Module) -> list[str]:
    """Module top-level statements must match a tight whitelist.

    Defense-in-depth: even though :func:`registry.load_alpha_meta_from_py`
    uses ``ast.literal_eval`` (which already rejects non-literal RHS), we
    enforce the RHS shape here too so violations surface in CI before
    they reach the registry:

      * ``ALPHA_ID = <Constant str>`` only.
      * ``__alpha_meta__ = <Dict literal>`` only.
    """
    allowed_assign_targets = {"ALPHA_ID", "__alpha_meta__"}
    violations: list[str] = []

    for stmt in tree.body:
        # Module docstring (first ``ast.Expr`` of a string constant).
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        ):
            continue
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target_id = stmt.targets[0].id
                if target_id == "ALPHA_ID":
                    if not (
                        isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)
                    ):
                        violations.append(
                            f"L{stmt.lineno}: ALPHA_ID RHS must be a string "
                            f"literal (got {type(stmt.value).__name__})"
                        )
                    continue
                if target_id == "__alpha_meta__":
                    if not isinstance(stmt.value, ast.Dict):
                        violations.append(
                            f"L{stmt.lineno}: __alpha_meta__ RHS must be a "
                            f"dict literal (got {type(stmt.value).__name__})"
                        )
                    continue
                if target_id in allowed_assign_targets:
                    continue
            violations.append(
                f"L{stmt.lineno}: only `ALPHA_ID = ...` / `__alpha_meta__ = ...` "
                f"assignments allowed at module level"
            )
            continue
        violations.append(
            f"L{stmt.lineno}: disallowed top-level statement "
            f"{type(stmt).__name__}"
        )
    return violations


# ---------------------------------------------------------------- pytest


_ALPHA_FILES = _discover_alpha_files()


@pytest.mark.skipif(not _ALPHA_FILES, reason="no zoo modules registered yet")
@pytest.mark.parametrize("alpha_path", _ALPHA_FILES, ids=lambda p: p.relative_to(ZOO_ROOT).as_posix())
def test_alpha_module_is_pure(alpha_path: Path) -> None:
    """Each zoo alpha must satisfy the AST purity contract."""
    source = alpha_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(alpha_path))

    violations = _check_module_body(tree)
    visitor = _PurityVisitor()
    visitor.visit(tree)
    violations.extend(visitor.violations)

    assert not violations, _format_violations(alpha_path, violations)
