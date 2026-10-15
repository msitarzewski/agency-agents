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

# Qwen resolves tools by its own names and silently keeps one it does not know,
# so Claude Code's Read/Write/Bash have to arrive as read_file/write_file/
# run_shell_command or the agent cannot read, create files, or run a shell.
qwen_tools_line="$(grep -m1 '^tools:' "$OUTPUT_DIR/qwen/agents/programmatic-display-buyer.md")"
[[ "$qwen_tools_line" == "tools: 'web_fetch, web_search, read_file, write_file, edit, run_shell_command'" ]] || {
  printf 'Expected Qwen tool names in programmatic-display-buyer, got: %s\n' "$qwen_tools_line" >&2
  exit 1
}

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

# A nonempty display name still needs a nonempty ASCII slug for every tool's
# output filename. The source linter and converter must agree on that rule.
sed 's/^name:.*/name: 专家/' "$OUTPUT_DIR/agent.md" > "$OUTPUT_DIR/empty-slug.md"
if "$SCRIPT_DIR/lint-agents.sh" "$OUTPUT_DIR/empty-slug.md" > /dev/null; then
  echo "Expected linter to reject an agent name with an empty install slug" >&2
  exit 1
fi

fixture_repo="$OUTPUT_DIR/fixture-repo"
mkdir -p "$fixture_repo/scripts" "$fixture_repo/engineering"
cp "$SCRIPT_DIR/convert.sh" "$SCRIPT_DIR/lib.sh" "$fixture_repo/scripts/"
cp "$OUTPUT_DIR/empty-slug.md" "$fixture_repo/engineering/empty-slug.md"
mkdir -p "$OUTPUT_DIR/empty-slug-output/codex"
printf 'keep existing output\n' > "$OUTPUT_DIR/empty-slug-output/codex/sentinel"
if "$fixture_repo/scripts/convert.sh" --tool codex --out "$OUTPUT_DIR/empty-slug-output" > "$OUTPUT_DIR/empty-slug-convert.log" 2>&1; then
  echo "Expected converter to reject an agent name with an empty install slug" >&2
  exit 1
fi
grep -q 'empty agent slug' "$OUTPUT_DIR/empty-slug-convert.log" || {
  echo "Expected converter to explain the empty slug" >&2
  exit 1
}
[[ "$(cat "$OUTPUT_DIR/empty-slug-output/codex/sentinel")" == 'keep existing output' ]] || {
  echo "Expected empty-slug rejection to preserve existing output" >&2
  exit 1
}

# Keep the Unicode display name, but provide an explicit ASCII alias rather
# than guessing a transliteration. This remains a valid installable agent.
sed 's/^name:.*/name: Expert 专家/' "$OUTPUT_DIR/agent.md" > "$fixture_repo/engineering/empty-slug.md"
"$SCRIPT_DIR/lint-agents.sh" "$fixture_repo/engineering/empty-slug.md" > /dev/null
"$fixture_repo/scripts/convert.sh" --tool codex --out "$OUTPUT_DIR/aliased-output" > /dev/null
[[ -f "$OUTPUT_DIR/aliased-output/codex/agents/expert.toml" ]] || {
  echo "Expected the aliased agent's Codex TOML output" >&2
  exit 1
}

echo "PASS: converted YAML frontmatter stays quoted and required source metadata is nonempty"
