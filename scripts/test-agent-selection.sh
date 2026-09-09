#!/usr/bin/env bash
# Regression coverage for install.sh agent-selection validation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/install.sh"
AGENTS_FILE="$(mktemp "${TMPDIR:-/tmp}/agency-agent-selection.XXXXXX")"
trap 'rm -f "$AGENTS_FILE"' EXIT

set +e
output="$($INSTALLER --tool claude-code --agent definitely-not-an-agent --dry-run 2>&1)"
status=$?
set -e
[[ "$status" -ne 0 ]] || {
  printf 'Unknown --agent selection unexpectedly succeeded:\n%s\n' "$output" >&2
  exit 1
}
[[ "$output" == *"Unknown agent"* ]] || {
  printf 'Unknown --agent selection did not explain the error:\n%s\n' "$output" >&2
  exit 1
}

printf '%s\n' 'definitely-not-an-agent' > "$AGENTS_FILE"
set +e
output="$($INSTALLER --tool claude-code --agents-file "$AGENTS_FILE" --dry-run 2>&1)"
status=$?
set -e
[[ "$status" -ne 0 ]] || {
  printf 'Unknown agents-file entry unexpectedly succeeded:\n%s\n' "$output" >&2
  exit 1
}
[[ "$output" == *"in agents-file"* ]] || {
  printf 'Unknown agents-file entry did not identify its source:\n%s\n' "$output" >&2
  exit 1
}

output="$($INSTALLER --tool claude-code --agent 'Developer Tooling Engineer' --dry-run 2>&1)"
[[ "$output" == *"Agents:  1"* ]] || {
  printf 'Valid display-name selection did not resolve to one agent:\n%s\n' "$output" >&2
  exit 1
}

echo "PASS: install.sh rejects unknown agent selections and accepts display names"
