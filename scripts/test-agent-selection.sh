#!/usr/bin/env bash
# Regression coverage for install.sh agent-selection validation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$SCRIPT_DIR/install.sh"
CONVERTER="$SCRIPT_DIR/convert.sh"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agency-agent-selection.XXXXXX")"
AGENTS_FILE="$WORK_DIR/agents.txt"
trap 'rm -rf "$WORK_DIR"' EXIT

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

# Pi integration: generate isolated fixtures, then exercise every destination
# and data-protection branch without touching the user's real Pi directories.
PI_INTEGRATIONS="$WORK_DIR/integrations"
"$CONVERTER" --tool pi --out "$PI_INTEGRATIONS" >/dev/null
PI_SOURCE="$PI_INTEGRATIONS/pi/agents/engineering-code-reviewer.md"
test -f "$PI_SOURCE"
mkdir -p "$WORK_DIR/home" "$WORK_DIR/global" "$WORK_DIR/project" \
  "$WORK_DIR/custom-root" "$WORK_DIR/backup" "$WORK_DIR/symlink" "$WORK_DIR/non-file"

PI_ENV=(HOME="$WORK_DIR/home" AGENCY_INTEGRATIONS_DIR="$PI_INTEGRATIONS")
env "${PI_ENV[@]}" "$INSTALLER" --tool pi --agent 'Code Reviewer' --no-convert >/dev/null
test -f "$WORK_DIR/home/.pi/agent/agents/engineering-code-reviewer.md"
cmp "$PI_SOURCE" "$WORK_DIR/home/.pi/agent/agents/engineering-code-reviewer.md"

env "${PI_ENV[@]}" PI_CODING_AGENT_DIR="$WORK_DIR/custom-root" \
  "$INSTALLER" --tool pi --agent 'Code Reviewer' --no-convert >/dev/null
test -f "$WORK_DIR/custom-root/agents/engineering-code-reviewer.md"

env "${PI_ENV[@]}" "$INSTALLER" --tool pi --agent 'Code Reviewer' \
  --path "$WORK_DIR/project" --no-convert >/dev/null
test -f "$WORK_DIR/project/engineering-code-reviewer.md"

printf 'USER CUSTOM\n' > "$WORK_DIR/backup/engineering-code-reviewer.md"
env "${PI_ENV[@]}" "$INSTALLER" --tool pi --agent 'Code Reviewer' \
  --path "$WORK_DIR/backup" --no-convert >/dev/null
backup_file="$(find "$WORK_DIR/backup/.agency-agents-backups" -type f -name 'engineering-code-reviewer.md' | head -1)"
test -n "$backup_file"
grep -q '^USER CUSTOM$' "$backup_file"
cmp "$PI_SOURCE" "$WORK_DIR/backup/engineering-code-reviewer.md"

printf 'SYMLINK SOURCE\n' > "$WORK_DIR/external.md"
ln -s "$WORK_DIR/external.md" "$WORK_DIR/symlink/engineering-code-reviewer.md"
env "${PI_ENV[@]}" "$INSTALLER" --tool pi --agent 'Code Reviewer' \
  --path "$WORK_DIR/symlink" --no-convert >/dev/null
test -L "$WORK_DIR/symlink/engineering-code-reviewer.md"
grep -q '^SYMLINK SOURCE$' "$WORK_DIR/external.md"

mkdir "$WORK_DIR/non-file/engineering-code-reviewer.md"
env "${PI_ENV[@]}" "$INSTALLER" --tool pi --agent 'Code Reviewer' \
  --path "$WORK_DIR/non-file" --no-convert >/dev/null
test -d "$WORK_DIR/non-file/engineering-code-reviewer.md"

mkdir -p "$WORK_DIR/detected"
output="$(env HOME="$WORK_DIR/home" AGENCY_INTEGRATIONS_DIR="$PI_INTEGRATIONS" \
  PI_AGENTS_DIR="$WORK_DIR/detected" PATH="/usr/bin:/bin" \
  "$INSTALLER" --no-interactive --dry-run --no-convert 2>&1)"
[[ "$output" == *"Tools:   pi"* ]] || {
  printf 'PI_AGENTS_DIR was not detected:\n%s\n' "$output" >&2
  exit 1
}

echo "PASS: install.sh selection and Pi install safety"
