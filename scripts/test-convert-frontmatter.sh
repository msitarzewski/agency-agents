#!/usr/bin/env bash
# Regression coverage for YAML frontmatter emitted by convert.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-frontmatter.XXXXXX")"
trap 'rm -rf "$OUTPUT_DIR"' EXIT

# Body separators are Markdown content, not additional frontmatter fences.
# get_body feeds the bodies used by the integration converters below.
. "$SCRIPT_DIR/lib.sh"
cat > "$OUTPUT_DIR/body-with-separator.md" <<'EOF'
---
name: Example
---

# Example

---

Important body text.
EOF
separator_count="$(get_body "$OUTPUT_DIR/body-with-separator.md" | grep -cx -- '---' || true)"
[[ "$separator_count" == 1 ]] || {
  printf 'Expected Markdown separator in agent body, got %s\n' "$separator_count" >&2
  exit 1
}

for tool in gemini-cli opencode qwen; do
  "$SCRIPT_DIR/convert.sh" --tool "$tool" --out "$OUTPUT_DIR" >/dev/null
done

assert_quoted() {
  local file="$1" field="$2" line prefix
  line="$(awk -v key="$field" '$0 ~ "^" key ":" { print; exit }' "$file")"
  prefix="$field: '"
  [[ "$line" == "$prefix"*"'" ]] || {
    printf 'Expected %s in %s to be a single-quoted YAML scalar, got: %s\n' \
      "$field" "$file" "$line" >&2
    return 1
  }
}

assert_quoted \
  "$OUTPUT_DIR/gemini-cli/agents/developer-tooling-engineer.md" \
  description
assert_quoted \
  "$OUTPUT_DIR/opencode/agents/developer-tooling-engineer.md" \
  name
assert_quoted \
  "$OUTPUT_DIR/opencode/agents/developer-tooling-engineer.md" \
  description
assert_quoted \
  "$OUTPUT_DIR/qwen/agents/programmatic-display-buyer.md" \
  tools

# A present but empty required field is unusable discovery metadata. Check the
# source linter directly, including YAML's quoted empty-string form.
cat > "$OUTPUT_DIR/agent.md" <<'EOF'
---
name: Example Agent
description: Builds useful examples
color: red
---

## Identity

## Core Mission

## Critical Rules

EOF
for field in name description color; do
  sed "s/^${field}:.*/${field}: \"\"/" "$OUTPUT_DIR/agent.md" > "$OUTPUT_DIR/empty-$field.md"
  if "$SCRIPT_DIR/lint-agents.sh" "$OUTPUT_DIR/empty-$field.md" > /dev/null; then
    printf 'Expected linter to reject empty %s metadata\n' "$field" >&2
    exit 1
  fi
done

echo "PASS: converted YAML frontmatter stays quoted and required source metadata is nonempty"
