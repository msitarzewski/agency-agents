#!/usr/bin/env bash
# grep -q must not make an early selected slug fail under pipefail/SIGPIPE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/agency-selection.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

# Exercise the installer's actual slug predicate with a list beyond the pipe
# buffer. An early grep -q match can close its input before printf finishes.
eval "$(sed -n '/^slug_allowed() {/,/^}/p' "$SCRIPT_DIR/install.sh")"
SELECTION_ACTIVE=true
_ALLOWED_SLUGS="$(awk 'BEGIN { print "first"; for (i = 0; i < 20000; i++) print "other-" i }')"
if ! slug_allowed first; then
  echo 'FAIL: an allowed early slug was rejected after grep closed the pipe' >&2
  exit 1
fi
slug_allowed other-19999 || {
  echo 'FAIL: an allowed final slug was rejected' >&2
  exit 1
}
echo 'PASS: early and final slugs remain selectable in a large roster'

# Confirm the real division install copies every source agent, not a variable
# subset that happens to survive the pipeline race.
source "$SCRIPT_DIR/lib.sh"
expected=0
while IFS= read -r -d '' file; do
  is_agent_file "$file" && expected=$((expected + 1))
done < <(find "$REPO_ROOT/engineering" -name '*.md' -type f -print0)
HOME="$tmp/home" bash "$SCRIPT_DIR/install.sh" --no-interactive --tool claude-code \
  --division engineering --path "$tmp/agents" > "$tmp/output" 2>&1
actual="$(find "$tmp/agents" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' ')"
if [[ "$actual" != "$expected" ]]; then
  printf 'FAIL: engineering install copied %s of %s source agents\n' "$actual" "$expected" >&2
  exit 1
fi
echo "PASS: engineering install copies all $expected selected agents"
