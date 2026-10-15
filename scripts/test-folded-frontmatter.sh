#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
for indicator in '>' '>-' '>+' '>2' '>2-' '>-2' '>+2' '>2+ # comment'; do
  printf '%s\n' '---' 'name: Example Agent' "description: $indicator" '  First line' '  Second line' 'color: blue' '---' '## Identity' '## Core Mission' '## Critical Rules' > "$scratch/agent.md"
  if bash "$SCRIPT_DIR/lint-agents.sh" "$scratch/agent.md" > "$scratch/result.log" 2>&1; then
    echo "FAIL: linter accepted folded frontmatter $indicator" >&2; exit 1
  fi
  grep -q 'folded YAML frontmatter is unsupported' "$scratch/result.log"
done
for indicator in '|' '|-' '|+' '|2' '|2-' '|-2' '|+2' '|2+ # comment'; do
  printf '%s\n' '---' 'name: Example Agent' "description: $indicator" '  First line' '  Second line' 'color: blue' '---' '## Identity' '## Core Mission' '## Critical Rules' > "$scratch/agent.md"
  if bash "$SCRIPT_DIR/lint-agents.sh" "$scratch/agent.md" > "$scratch/result.log" 2>&1; then
    echo "FAIL: linter accepted literal frontmatter $indicator" >&2; exit 1
  fi
  grep -q 'literal YAML frontmatter is unsupported' "$scratch/result.log"
done
for description in '"A > B"' "'A > B'" '"A | B"' "'A | B'" 'Ordinary description'; do
  printf '%s\n' '---' 'name: Example Agent' "description: $description" 'color: blue' '---' '## Identity' '## Core Mission' '## Critical Rules' '> Body quotation' > "$scratch/agent.md"
  bash "$SCRIPT_DIR/lint-agents.sh" "$scratch/agent.md" > "$scratch/result.log" 2>&1
done
echo 'PASS: folded and literal frontmatter are rejected while quoted scalars and body quotations pass'
