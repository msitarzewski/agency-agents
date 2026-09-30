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

echo "PASS: unclosed frontmatter is rejected and a valid agent still passes"
