#!/usr/bin/env bash
#
# test-convert-openagent.sh — convert_openagent maps agent frontmatter onto the
# OpenAgent persona fields, and every generated file parses as YAML.
#
# Two fixtures in a throwaway repo: one with vibe, emoji, color and a
# Communication Style section (apostrophes in both a label and an example, the
# one quoting rule yaml_quote has to get right), and one with none of those, so
# the fallbacks are pinned too: behavior falls back to the description, the
# face to a default emoji, the voice to the behavior line.
#
# Usage: ./scripts/test-convert-openagent.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/agency-openagent.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT

mkdir -p "$scratch/repo/scripts" "$scratch/repo/engineering"
cp "$SCRIPT_DIR/convert.sh" "$SCRIPT_DIR/lib.sh" "$scratch/repo/scripts/"

cat > "$scratch/repo/divisions.json" <<'JSON'
{
  "divisions": {
    "engineering": {"label": "Engineering", "icon": "Code", "color": "#3B82F6"}
  }
}
JSON

cat > "$scratch/repo/engineering/engineering-full-fixture.md" <<'MD'
---
name: Full Fixture
description: Reviews a pull request before anyone else's eyes are on it
color: cyan
emoji: 🔍
vibe: Reads the diff twice, says what it found once.
---
## 🧠 Your Identity
identity text

## 💭 Your Communication Style

- **Be specific**: "Line 12 drops the error; the caller never sees it"
- **Don't hedge**: "This breaks the build — here's the failing test"

## 🔄 Learning & Memory
memory text
MD

cat > "$scratch/repo/engineering/engineering-bare-fixture.md" <<'MD'
---
name: Bare Fixture
description: An agent with no vibe, no emoji and no style section
color: blue
---
## Core Mission
mission text
MD

cd "$scratch/repo"
bash scripts/convert.sh --tool openagent --out "$scratch/out" > "$scratch/convert.log" 2>&1 || {
  cat "$scratch/convert.log" >&2; echo "FAIL: convert.sh --tool openagent exited non-zero" >&2; exit 1; }

python3 - "$scratch/out/openagent" <<'PY'
import os, sys, yaml
d = sys.argv[1]
fails = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

files = sorted(os.listdir(d))
check(files == ["bare-fixture.persona.yaml", "full-fixture.persona.yaml"], f"one persona per agent, named <slug>.persona.yaml: {files}")

full = yaml.safe_load(open(os.path.join(d, "full-fixture.persona.yaml"), encoding="utf-8"))
check(full["openagent"] == "0.2", "spec version is the string '0.2'")
check(full["id"] == "full-fixture", "id is the slug")
check(full["name"] == "Full Fixture", "name is the frontmatter name")
check(full["role"] == "Reviews a pull request before anyone else's eyes are on it", "role is the description, apostrophe intact")
check(full["behavior"] == "Reads the diff twice, says what it found once.", "behavior is the vibe")
check(full["face"]["ref"] == "🔍", "face.ref is the emoji")
check(full["face"]["anchor"] == "the 🔍 emoji on a cyan background", "face.anchor names the emoji and color")
check(full["voice"]["written"]["rules"] == ["Be specific", "Don't hedge"], "voice rules are the Communication Style labels")
check(full["voice"]["written"]["sample"] == "Line 12 drops the error; the caller never sees it", "voice sample is the first example, unquoted")
check(full["ext"]["agency-agents"]["source"] == "engineering/engineering-full-fixture.md", "ext.agency-agents.source is the repo-relative source")

bare = yaml.safe_load(open(os.path.join(d, "bare-fixture.persona.yaml"), encoding="utf-8"))
desc = "An agent with no vibe, no emoji and no style section"
check(bare["behavior"] == desc, "no vibe: behavior falls back to the description")
check(bare["face"]["ref"] == "🤖", "no emoji: face.ref falls back to 🤖")
check(bare["voice"]["written"] == {"rules": [desc], "sample": desc}, "no style section: voice falls back to the behavior line")

for f in files:
    p = yaml.safe_load(open(os.path.join(d, f), encoding="utf-8"))
    missing = [k for k in ("id", "name", "role", "face", "voice", "behavior") if not p.get(k)]
    check(not missing, f"{f}: every field the OpenAgent schema requires is present {missing or ''}")

if fails:
    print(f"\n{len(fails)} check(s) failed"); sys.exit(1)
print("\nPASSED: convert_openagent maps frontmatter onto the persona fields")
PY
