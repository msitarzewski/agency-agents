"""Single source of truth for the CLI version string.

Reads ``vibe-trading-ai``'s installed package metadata when available
(``pip install -e .`` is enough). For an un-installed checkout (e.g. running
straight from a clone with ``PYTHONPATH=agent``) it falls back to reading the
version straight out of ``pyproject.toml`` — so ``pyproject.toml`` is the one
and only place the version is ever written. There is deliberately no hardcoded
version constant to drift out of sync on release (issue #156).
"""

from __future__ import annotations

from typing import Final


def _version_from_pyproject() -> str:
    """Read ``[project] version`` from the repo's ``pyproject.toml``.

    Returns:
        The declared version, or ``"unknown"`` if the file cannot be located
        or parsed (only reachable for an un-installed checkout whose tree has
        been moved away from its ``pyproject.toml``).
    """
    import tomllib
    from pathlib import Path

    # agent/cli/_version.py -> parents[2] is the repo root holding pyproject.toml.
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"


try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    try:
        __version__: Final[str] = _pkg_version("vibe-trading-ai")
    except PackageNotFoundError:
        __version__ = _version_from_pyproject()
except ImportError:  # pragma: no cover — importlib.metadata is stdlib on 3.8+
    __version__ = _version_from_pyproject()


__all__ = ["__version__"]
