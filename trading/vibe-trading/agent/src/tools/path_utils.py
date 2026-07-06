"""Path safety helpers used by file-access tools.

Three helpers, three threat models:

* `safe_path(p, workdir)` — tool-controlled sandbox. Resolves `p` under
  `workdir` and rejects any escape. Used by `read_file` / `write_file` /
  `edit_file` where the LLM must stay inside the current run dir.

* `safe_user_path(p)` — user-supplied broker files. Accepts files only under
  explicit import roots, not the whole home directory or project tree.

* `safe_document_path(p)` — document-reader inputs. Uses the same import-root
  boundary as `safe_user_path()`.

All helpers raise ``ValueError`` on rejection — callers already expect this.
"""

from __future__ import annotations

import os
from pathlib import Path

_ALLOWED_FILE_ROOTS_ENV = "VIBE_TRADING_ALLOWED_FILE_ROOTS"
_ALLOWED_RUN_ROOTS_ENV = "VIBE_TRADING_ALLOWED_RUN_ROOTS"


def _rejects_unc(p: str) -> None:
    """Raise ValueError if `p` starts with a UNC share prefix."""
    if p.startswith("\\\\") or p.startswith("//"):
        raise ValueError(f"UNC paths are not allowed: {p!r}")


def safe_path(p: str, workdir: Path) -> Path:
    """Resolve `p` under `workdir` and ensure it stays inside.

    Args:
        p: User-supplied path (relative or absolute).  ``~`` expansion is
            supported so callers can pass home-relative paths.
        workdir: Workspace root. `p` must resolve to a location inside.

    Returns:
        Absolute resolved path inside `workdir`.

    Raises:
        ValueError: If `p` uses a UNC share, or its resolved form escapes
            `workdir`. Callers surface this back to the LLM as a tool error.
    """
    _rejects_unc(p)
    base = Path(workdir).resolve()
    # Expand ~ so home-relative paths (e.g. ~/.vibe-trading/scripts/foo.py)
    # resolve correctly instead of being treated as literal directory names.
    expanded = Path(p).expanduser()
    if expanded.is_absolute():
        resolved = expanded.resolve()
    else:
        resolved = (base / p).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path {p!r} escapes the workspace root") from exc
    return resolved


def _agent_root() -> Path:
    """Return the agent package root."""
    return Path(__file__).resolve().parents[2]


def _configured_file_roots() -> list[Path]:
    """Return file roots configured through the environment."""
    raw = os.getenv(_ALLOWED_FILE_ROOTS_ENV, "")
    roots: list[Path] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        _rejects_unc(item)
        roots.append(Path(item).expanduser().resolve())
    return roots


def _default_file_roots() -> list[Path]:
    """Return default roots for uploaded/imported user files."""
    cwd = Path.cwd().resolve()
    home = Path.home().resolve()
    agent_root = _agent_root()
    return [
        agent_root / "uploads",
        agent_root / "runs",
        cwd / "uploads",
        cwd / "data",
        home / ".vibe-trading" / "uploads",
        home / ".vibe-trading" / "imports",
    ]


def _default_run_roots() -> list[Path]:
    """Return default roots for generated backtest/tool run directories."""
    from src.swarm.store import swarm_runs_root

    cwd = Path.cwd().resolve()
    home = Path.home().resolve()
    agent_root = _agent_root()
    return [
        agent_root / "runs",
        swarm_runs_root(),
        cwd / "runs",
        home / ".vibe-trading" / "shadow_runs",
        home / ".vibe-trading" / "runs",
    ]


def allowed_file_roots() -> list[Path]:
    """Return all roots allowed for document and broker-file reads."""
    roots: list[Path] = []
    for root in [*_default_file_roots(), *_configured_file_roots()]:
        resolved = root.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return roots


_ALLOWED_WRITE_ROOTS_ENV = "VIBE_TRADING_ALLOWED_WRITE_ROOTS"


def allowed_write_roots() -> list[Path]:
    """Return all roots allowed for file writes and edits."""
    raw = os.getenv(_ALLOWED_WRITE_ROOTS_ENV, "")
    configured: list[Path] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        _rejects_unc(item)
        configured.append(Path(item).expanduser().resolve())

    cwd = Path.cwd().resolve()
    home = Path.home().resolve()
    agent_root = _agent_root()
    defaults = [
        agent_root / "uploads",
        agent_root / "runs",
        cwd / "uploads",
        home / ".vibe-trading" / "uploads",
        home / ".vibe-trading" / "runs",
    ]

    roots: list[Path] = []
    for root in [*defaults, *configured]:
        resolved = root.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return roots


def resolve_safe_path(
    file_path: str,
    run_dir: str | None,
    allowed_roots: list[Path],
    *,
    purpose: str = "workspace",
) -> Path:
    """Resolve a file path under run_dir with fallback to allowed roots.

    Args:
        file_path: Relative or absolute path (supports tilde expansion).
        run_dir: Optional run directory to resolve against.
        allowed_roots: List of fallback allowed root directories.
        purpose: Context name for error messages.

    Returns:
        Absolute resolved Path.

    Raises:
        ValueError: If path cannot be resolved or escapes boundaries.
    """
    _rejects_unc(file_path)

    # Try resolving against run_dir if provided
    if run_dir:
        try:
            run_root = safe_run_dir(run_dir)
        except ValueError as exc:
            # If safe_run_dir fails, check if the path is in allowed_roots first
            candidate = Path(file_path).expanduser().resolve()
            for root in allowed_roots:
                if candidate.is_relative_to(root):
                    return candidate
            raise exc

        try:
            return safe_path(file_path, run_root)
        except ValueError as exc:
            # Fallback to allowed roots if safe_path containment fails
            candidate = Path(file_path).expanduser().resolve()
            for root in allowed_roots:
                if candidate.is_relative_to(root):
                    return candidate
            raise ValueError(
                f"Path {file_path!r} escapes run_dir {run_dir!r} and is not in allowed {purpose} roots."
            ) from exc

    # If no run_dir, path must resolve inside one of the allowed roots
    candidate = Path(file_path).expanduser().resolve()
    for root in allowed_roots:
        if candidate.is_relative_to(root):
            return candidate

    raise ValueError(
        f"run_dir is required to write/edit {file_path!r}, or the path must resolve inside allowed {purpose} roots."
    )


def _allowed_run_roots() -> list[Path]:
    """Return all roots allowed for run_dir-based tools."""
    raw = os.getenv(_ALLOWED_RUN_ROOTS_ENV, "")
    configured: list[Path] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        _rejects_unc(item)
        configured.append(Path(item).expanduser().resolve())

    roots: list[Path] = []
    for root in [*_default_run_roots(), *configured]:
        resolved = root.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return roots


def _import_candidate(p: str) -> Path:
    """Return the filesystem candidate for an import path.

    Browser uploads are exposed as ``uploads/<name>`` so the UI never needs
    a local absolute path. Resolve that handle back to the agent upload root
    before enforcing the allowlist.
    """
    candidate = Path(p).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()

    parts = candidate.parts
    if parts and parts[0] == "uploads":
        return (_agent_root() / candidate).resolve()
    if len(parts) >= 2 and parts[0] == "agent" and parts[1] == "uploads":
        return (_agent_root() / Path(*parts[1:])).resolve()
    return (Path.cwd() / candidate).resolve()


def _safe_import_path(p: str, *, purpose: str) -> Path:
    """Validate a user-supplied path against explicit import roots.

    Args:
        p: User-supplied path. `~` expansion is supported.
        purpose: Human-readable purpose for error messages.

    Returns:
        Absolute resolved path inside an allowed import root.

    Raises:
        ValueError: If `p` is a UNC share or resolves outside all allowed
            import roots.
    """
    _rejects_unc(p)
    resolved = _import_candidate(p)

    for root in allowed_file_roots():
        if resolved.is_relative_to(root):
            return resolved

    raise ValueError(
        f"Path {p!r} is outside allowed {purpose} roots. "
        f"Set {_ALLOWED_FILE_ROOTS_ENV} to add an import directory."
    )


def safe_user_path(p: str) -> Path:
    """Validate a user-supplied broker/export file path.

    Args:
        p: User-supplied path. `~` expansion is supported.

    Returns:
        Absolute resolved path inside an allowed import root.

    Raises:
        ValueError: If `p` is a UNC share or resolves outside all allowed
            import roots.
    """
    return _safe_import_path(p, purpose="user-file")


def safe_document_path(p: str) -> Path:
    """Validate a document-reader file path.

    Args:
        p: User-supplied document path. `~` expansion is supported.

    Returns:
        Absolute resolved path inside an allowed import root.

    Raises:
        ValueError: If `p` is a UNC share or resolves outside all allowed
            import roots.
    """
    return _safe_import_path(p, purpose="document")


def safe_run_dir(p: str) -> Path:
    """Validate a run directory used by generated-code tools.

    Args:
        p: User/LLM-supplied run directory. `~` expansion is supported.

    Returns:
        Absolute resolved path inside an allowed run root.

    Raises:
        ValueError: If `p` is a UNC share or resolves outside all allowed run
            roots.
    """
    _rejects_unc(p)
    resolved = Path(p).expanduser().resolve()

    for root in _allowed_run_roots():
        if resolved.is_relative_to(root):
            return resolved

    raise ValueError(
        f"run_dir {p!r} is outside allowed run roots. "
        f"Set {_ALLOWED_RUN_ROOTS_ENV} to add a run directory."
    )


def safe_run_id(run_id: str) -> Path:
    """Resolve a bare run id to an existing allowed run directory.

    Args:
        run_id: Bare run directory name, not a path.

    Returns:
        Existing run directory under one of the allowed run roots.

    Raises:
        ValueError: If the run id is empty, path-shaped, or not found.
    """
    _rejects_unc(run_id)
    candidate = Path(run_id)
    if (
        not run_id.strip()
        or candidate.is_absolute()
        or len(candidate.parts) != 1
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise ValueError(f"run_id {run_id!r} must be a bare run directory name")

    for root in _allowed_run_roots():
        resolved = (root / candidate.name).resolve()
        if resolved.is_relative_to(root) and resolved.is_dir():
            return resolved

    raise ValueError(f"run_id {run_id!r} was not found under allowed run roots")
