#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/agency-frontmatter-keys.XXXXXX")"
trap 'rm -rf "$FIXTURE"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
cat > "$FIXTURE/valid.md" <<'AGENT'
---
name: "Key Fixture: Not a second key"
description: Reviews unique metadata keys
  and includes the word name as ordinary continuation text
color: blue
vibe: Preserve a single metadata meaning
---
## Identity
A fixture for checking that duplicate metadata is rejected before different
integrations interpret different field values. The body deliberately repeats
name: without making it part of the frontmatter mapping.
## Core Mission
Verify metadata validation with explicit controlled documents and meaningful
positive and negative cases rather than checking the implementation text.
## Critical Rules
Keep field identity separate from colons inside scalar values and body content.
AGENT
for key in name description color vibe; do
  awk -v key="$key" 'NR==2 {print key ": Replacement"} {print}' "$FIXTURE/valid.md" > "$FIXTURE/duplicate.md"
  if bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/duplicate.md" > "$FIXTURE/error.log" 2>&1; then
    fail "linter accepted duplicate ${key} metadata"
  fi
  grep -Fq "duplicate frontmatter field '${key}'" "$FIXTURE/error.log" \
    || { cat "$FIXTURE/error.log" >&2; fail "missing duplicate-key diagnostic"; }
done
bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/valid.md" > "$FIXTURE/valid.log" 2>&1 \
  || { cat "$FIXTURE/valid.log" >&2; fail "linter rejected colons in scalar/body text"; }
echo 'PASS: repeated required/optional keys rejected; quoted scalar/body colons accepted'
