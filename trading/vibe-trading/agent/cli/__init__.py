"""Vibe-Trading CLI package.

The legacy single-file CLI has been preserved verbatim as
``cli/_legacy.py`` and is the source of truth for non-interactive
subcommands (``serve``, ``run``, ``mcp``, ``sessions``, ``swarm`` ...).
The front door (:mod:`cli.main`) shows the banner, runs the
onboarding wizard when needed, then drives the interactive loop
built on :mod:`cli.input`, :mod:`cli.completer`, and
:mod:`cli.commands.*`. Non-interactive entries still pass through to
``_legacy.main``.

The console-script entry in ``pyproject.toml``
(``vibe-trading = "cli:main"``) points at the ``main`` callable exported
here.

Compatibility note: tests and downstream callers historically reached
into ``cli._INIT_ENV_PATH`` / ``cli.cmd_memory_list`` / ``cli.Confirm``
etc. To preserve that surface we re-export every public name from
``_legacy`` at package import time. New code should import the same
helpers from ``cli._legacy`` directly.
"""

from __future__ import annotations

from cli import _legacy as _legacy
from cli.main import main

# Re-export the legacy module's public surface (anything not prefixed
# with two underscores). This lets ``cli.cmd_memory_list`` /
# ``cli._INIT_ENV_PATH`` / ``cli.Prompt`` etc. keep working without us
# having to enumerate every name by hand.
for _name in dir(_legacy):
    if _name.startswith("__"):
        continue
    globals().setdefault(_name, getattr(_legacy, _name))
del _name


# Symbols tests may monkeypatch on the ``cli`` package that legacy
# callables still read from their own module globals. Keep this list
# explicit so accidental package-level attributes don't bleed into
# ``_legacy``.
_LEGACY_SYNCED_GLOBALS: tuple[str, ...] = (
    "_INIT_ENV_PATH",
    "AGENT_DIR",
    "RUNS_DIR",
    "SWARM_DIR",
    "SESSIONS_DIR",
    "UPLOADS_DIR",
    "_PROVIDER_CHOICES",
)


def _sync_legacy_test_overrides() -> None:
    """Mirror package-level monkeypatches onto ``_legacy``'s module globals.

    Tests reach into ``cli.<NAME>`` to override constants, but legacy
    callables read ``<NAME>`` from their own module namespace. This hook
    copies any patched value back to ``_legacy`` for the allowlist below.
    """
    pkg_globals = globals()
    for name in _LEGACY_SYNCED_GLOBALS:
        if name not in pkg_globals:
            continue
        new_value = pkg_globals[name]
        if getattr(_legacy, name, None) is not new_value:
            setattr(_legacy, name, new_value)


def cmd_init() -> int:
    """Compatibility wrapper for callers patching ``cli._INIT_ENV_PATH``."""
    _sync_legacy_test_overrides()
    return _legacy.cmd_init()


# Wrap every ``cmd_*`` callable re-exported from ``_legacy`` so a package-level
# monkeypatch of any symbol in ``_LEGACY_SYNCED_GLOBALS`` is propagated to
# ``_legacy`` before the call. Without this, ``patch.object(cli, "RUNS_DIR",
# tmp); cli.cmd_list()`` would silently read the unpatched ``_legacy.RUNS_DIR``.
import functools as _functools  # noqa: E402

def _make_synced_legacy_wrapper(legacy_fn):  # noqa: ANN001
    """Wrap ``legacy_fn`` so the package-level monkeypatch sync fires first."""

    @_functools.wraps(legacy_fn)
    def _wrapper(*args, **kwargs):
        _sync_legacy_test_overrides()
        # Re-read the (possibly just-synced) attribute from ``_legacy`` in
        # case the test also patched the function itself.
        return getattr(_legacy, legacy_fn.__name__)(*args, **kwargs)

    _wrapper.__wrapped__ = legacy_fn
    return _wrapper


for _cmd_name in [n for n in globals() if n.startswith("cmd_") and n != "cmd_init"]:
    _cmd_obj = globals()[_cmd_name]
    if callable(_cmd_obj) and getattr(_cmd_obj, "__module__", "") == "cli._legacy":
        globals()[_cmd_name] = _make_synced_legacy_wrapper(_cmd_obj)
del _cmd_name, _cmd_obj


__all__ = ["main", *sorted(
    name for name in globals()
    if not name.startswith("_") and name != "main"
)]
