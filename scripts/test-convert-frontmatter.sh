#!/usr/bin/env bash
# Regression coverage for YAML frontmatter emitted by convert.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-frontmatter.XXXXXX")"
trap 'rm -rf "$OUTPUT_DIR"' EXIT

for tool in gemini-cli opencode qwen pi; do
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
assert_quoted \
  "$OUTPUT_DIR/pi/agents/engineering-developer-tooling-engineer.md" \
  description
PI_AGENT="$OUTPUT_DIR/pi/agents/engineering-code-reviewer.md"
for line in "color: 'purple'" "emoji: '👁️'" "vibe: 'Reviews code like a mentor, not a gatekeeper. Every comment teaches something.'"; do
  grep -Fqx "$line" "$PI_AGENT" || { echo "Pi output dropped metadata: $line" >&2; exit 1; }
done
PI_TOOLS_AGENT="$OUTPUT_DIR/pi/agents/product-manager.md"
grep -Fqx "x-agency-claude-tools: 'WebFetch, WebSearch, Read, Write, Edit'" "$PI_TOOLS_AGENT"
grep -Fqx 'tools: read, write, edit' "$PI_TOOLS_AGENT"
grep -Fqx 'extensions: false' "$PI_TOOLS_AGENT"
grep -Fqx "x-agency-unmapped-tools: 'WebFetch, WebSearch'" "$PI_TOOLS_AGENT"
if [[ "$(grep -c '^---$' "$OUTPUT_DIR/pi/agents/design-ux-architect.md")" -ne 4 ]]; then
  echo "Pi output dropped persona body separators" >&2
  exit 1
fi

echo "PASS: converted YAML frontmatter keeps scalar values safely quoted"
