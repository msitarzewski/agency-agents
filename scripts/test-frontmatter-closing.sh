#!/usr/bin/env bash
# An unclosed source frontmatter must not become a deployable empty persona.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/agency-frontmatter-closing.XXXXXX")"
trap 'rm -rf "$FIXTURE"' EXIT

cat > "$FIXTURE/unclosed.md" <<'EOF'
---
name: Broken Agent
description: This agent is missing its closing frontmatter fence
color: blue
# Identity
# Core Mission
# Critical Rules
EOF

if bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/unclosed.md" > "$FIXTURE/invalid.log" 2>&1; then
  echo "linter accepted an agent with no closing frontmatter fence" >&2
  exit 1
fi
grep -Fq 'missing frontmatter closing ---' "$FIXTURE/invalid.log"

cat > "$FIXTURE/valid.md" <<'EOF'
---
name: Valid Agent
description: This agent has a closing frontmatter fence
color: blue
---
## Identity
## Core Mission
## Critical Rules
EOF
bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/valid.md" > "$FIXTURE/valid.log" 2>&1

# Metadata after a scalar ending in --- must not enter the originality body.
# Distinct long vibe fields must not hide two identical agent bodies.
repo="$FIXTURE/originality"
mkdir -p "$repo/scripts" "$repo/engineering"
cp "$SCRIPT_DIR/check-agent-originality.sh" "$repo/scripts/"
printf '%s\n' '{"divisions":{"engineering":{}}}' > "$repo/divisions.json"
for variant in first second; do
  {
    printf '%s\n' '---' "name: $variant Agent" 'description: Explains ---' 'color: blue'
    printf 'vibe:'
    for ((i=0; i<100; i++)); do printf ' %s%d' "$variant" "$i"; done
    printf '\n%s\n' '---' '## Identity' '## Core Mission' '## Critical Rules'
    printf '%s\n' 'This specialist analyzes customer requirements and provides detailed implementation recommendations with evidence from repeatable experiments while preserving existing behavior and documenting each important decision with clear expectations realistic measurements reliable checks and complete operational guidance for maintainers and reviewers.'
  } > "$repo/engineering/$variant.md"
done
if bash "$repo/scripts/check-agent-originality.sh" "$repo/engineering/second.md" > "$FIXTURE/originality.log" 2>&1; then
  echo 'FAIL: metadata suffix hid an identical agent body from the originality check' >&2
  exit 1
fi
grep -Fq 'substantially duplicate' "$FIXTURE/originality.log"

echo "PASS: unclosed frontmatter is rejected and a valid agent still passes"
