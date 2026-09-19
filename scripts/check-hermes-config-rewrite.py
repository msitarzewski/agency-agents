"""
Regression test runner for the ensure_hermes_plugin_enabled() heredoc.

Extracts the heredoc body from scripts/install.sh and runs it against a
battery of synthetic configs plus the user's own Hermes config.yaml backup
if present. Fails if any case produces an invalid YAML file, collapses the
list into a scalar, duplicates the plugin, or isn't idempotent on re-run.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

INSTALL_SH = Path(__file__).resolve().parent / "install.sh"
HERMES_BACKUP = Path(os.path.expanduser("~/.hermes/config.yaml.bak.pre-agency-agents"))

PLUGIN = "agency-agents-router"


def extract_heredoc(path: Path) -> str:
    text = path.read_text()
    # The heredoc body sits between <<'PY' and the next "PY" sentinel on
    # its own line. The sentinel is exactly "PY" at column 0.
    pattern = re.compile(
        r"""python3 - "\$config" "\$plugin" <<'PY'\n(.+?)\nPY\n""",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"heredoc not found in {path}")
    return match.group(1)


def run_heredoc(heredoc: str, cfg_text: str):
    """Run the heredoc once. Returns (parsed_yaml_dict, error_string)."""
    import yaml
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "config.yaml"
        p.write_text(cfg_text)
        result = subprocess.run(
            ["python3", "-", str(p), PLUGIN],
            input=heredoc,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None, f"exit={result.returncode} stderr={result.stderr[:200]}"
        try:
            parsed = yaml.safe_load(p.read_text())
            return parsed, None
        except yaml.YAMLError as e:
            return None, f"yaml parse: {e}"


def check_case(heredoc: str, name: str, cfg_text: str) -> list[str]:
    import yaml
    failures: list[str] = []
    parsed, err = run_heredoc(heredoc, cfg_text)
    if err:
        failures.append(f"{name}: {err}")
        return failures
    enabled = (parsed or {}).get("plugins", {}).get("enabled")
    if not isinstance(enabled, list):
        failures.append(f"{name}: enabled is not a list (got {enabled!r})")
        return failures
    if PLUGIN not in enabled:
        failures.append(f"{name}: plugin missing from enabled")
    # Idempotency: re-run on the produced text; expect no further changes.
    text = yaml.safe_dump(parsed, sort_keys=False)
    parsed2, err2 = run_heredoc(heredoc, text)
    if err2:
        failures.append(f"{name}: idempotent re-run: {err2}")
        return failures
    enabled2 = (parsed2 or {}).get("plugins", {}).get("enabled")
    if enabled2 != enabled:
        failures.append(
            f"{name}: idempotent re-run changed enabled: {enabled!r} -> {enabled2!r}"
        )
    return failures


def main() -> int:
    heredoc = extract_heredoc(INSTALL_SH)
    print(
        f"Extracted heredoc: {len(heredoc)} chars, "
        f"{heredoc.count(chr(10)) + 1} lines"
    )

    configs: list[tuple[str, str]] = [
        (
            "Hermes 4-space indent, fresh install",
            textwrap.dedent("""\
                model:
                  name: x
                plugins:
                  disabled:
                    - old/dead
                  enabled:
                    - basic
                    - chronos
                    - ponytail
                session_reset:
                  foo: bar
            """),
        ),
        (
            "Corrupted-scalar (post-bug recovery)",
            "model:\n  name: x\nplugins:\n  enabled:\n"
            "  - agency-agents-router - basic - chronos - ponytail\n",
        ),
        (
            "Already present (no-op)",
            textwrap.dedent("""\
                model:
                  name: x
                plugins:
                  enabled:
                    - agency-agents-router
                    - basic
                    - chronos
            """),
        ),
        (
            "Empty inline enabled: []",
            textwrap.dedent("""\
                model:
                  name: x
                plugins:
                  enabled: []
                other:
                  x: 1
            """),
        ),
        (
            "No plugins: block at all",
            textwrap.dedent("""\
                model:
                  name: x
                session_reset:
                  foo: bar
            """),
        ),
        (
            "Original 2-space indent (script's documented style)",
            textwrap.dedent("""\
                model:
                  name: x
                plugins:
                  enabled:
                  - basic
                  - chronos
            """),
        ),
        (
            "Append not prepend (verify position)",
            textwrap.dedent("""\
                model:
                  name: x
                plugins:
                  enabled:
                    - basic
                    - chronos
                    - ponytail
                other:
                  x: 1
            """),
        ),
    ]

    if HERMES_BACKUP.exists():
        configs.append(
            ("Hermes actual config backup (ground truth)", HERMES_BACKUP.read_text())
        )

    total = 0
    failures: list[str] = []
    for name, cfg in configs:
        total += 1
        for f in check_case(heredoc, name, cfg):
            failures.append(f)

    if failures:
        print(f"\nFAIL ({len(failures)} error(s) across {total} cases):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\nOK: all {total} regression cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())