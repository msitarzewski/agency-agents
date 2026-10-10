#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$SCRIPT_DIR/check-agent-originality.sh" <<'PY'
from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile
checker = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="agency-originality-paths-") as temp:
    root = Path(temp).resolve() / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "engineering").mkdir()
    shutil.copyfile(checker, root / "scripts/check-agent-originality.sh")
    (root / "divisions.json").write_text(json.dumps({"divisions": {"engineering": {}}}))
    body = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima"
    target = root / "engineering/original.md"
    target.write_text(f"---\nname: Original\n---\n{body}\n")
    alias = root.parent / "alias"
    alias.symlink_to(root, target_is_directory=True)
    file_alias = root.parent / "agent.md"
    file_alias.symlink_to(target)
    def run(script, argument):
        return subprocess.run(["bash", str(script), str(argument)], cwd=root, capture_output=True, text=True, env={**os.environ, "ORIGINALITY_FAIL": "40", "ORIGINALITY_WARN": "20"})
    for label, script, argument in [
        ("directory alias", root / "scripts/check-agent-originality.sh", alias / "engineering/original.md"),
        ("file alias", root / "scripts/check-agent-originality.sh", file_alias),
        ("checker invoked through alias", alias / "scripts/check-agent-originality.sh", target),
    ]:
        result = run(script, argument)
        assert result.returncode == 0, (label, result.stdout, result.stderr)
        print(f"PASS {label} excludes candidate's own corpus record")
    duplicate = root / "engineering/duplicate.md"
    duplicate.write_text(f"---\nname: Duplicate\n---\n{body}\n")
    result = run(root / "scripts/check-agent-originality.sh", file_alias)
    assert result.returncode == 1 and "duplicate.md" in result.stdout, (result.stdout, result.stderr)
    print("PASS a separate identical file is still rejected")
PY
