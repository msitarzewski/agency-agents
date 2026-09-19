#!/usr/bin/env bash
#
# check-divisions.sh — enforce a single source of truth for the division set.
#
# divisions.json (repo root) is canonical. This script fails if any of the
# following disagree with it:
#   1. The actual top-level agent directories on disk
#   2. AGENT_DIRS in scripts/convert.sh
#   3. AGENT_DIRS in scripts/lint-agents.sh
#   4. The path filters in .github/workflows/lint-agents.yml
#   5. Every divisions.json entry has label, icon, and color
#
# Add a division: create its directory, add an entry to divisions.json, then
# this script tells you every other place that must be updated. No deps beyond
# bash 3.2 + coreutils (no jq) so it runs the same on macOS and CI.
#
# Usage: ./scripts/check-divisions.sh

set -euo pipefail

cd "$(dirname "$0")/.."

JSON="divisions.json"

# Top-level directories that are NOT divisions. Everything else at the repo
# root that is a directory is treated as a division (so a new division dir is
# caught even if nobody remembered to register it).
# integrations/ is convert.sh's OUTPUT tree (per-tool conversions written back
# into the repo), not a source-agent category. strategy/ holds playbooks and
# runbooks (no agent frontmatter), not agents. Neither is a division — they must
# never be scanned as source-agent categories.
NON_DIVISION_DIRS=(examples scripts integrations strategy)

errors=0
fail() { echo "ERROR $*"; errors=$((errors + 1)); }

# --- sorted, newline-delimited helpers -------------------------------------

# Canonical set: object-valued keys inside the "divisions" object. Scoping to
# lines after the `"divisions": {` opener excludes both the wrapper key itself
# and the string-valued "_note" key.
canonical() {
  awk '/"divisions"[[:space:]]*:[[:space:]]*\{/{f=1; next} f' "$JSON" \
    | grep -oE '"[a-z0-9-]+"[[:space:]]*:[[:space:]]*\{' \
    | sed -E 's/"([a-z0-9-]+)".*/\1/' | sort -u
}

# Actual division directories: top-level dirs that contain at least one
# git-TRACKED file, minus the excludes and anything dot-prefixed. Using
# `git ls-files` (not a filesystem glob) keeps this in lockstep with what CI's
# clean checkout sees, so a local gitignored scratch dir (e.g. notes/) can't
# produce a false failure.
actual_dirs() {
  local base
  git ls-files | awk -F/ 'NF>1{print $1}' | sort -u | while IFS= read -r base; do
    [[ "$base" == .* ]] && continue
    case " ${NON_DIVISION_DIRS[*]} " in *" $base "*) continue ;; esac
    echo "$base"
  done
}

# Contents of a bash AGENT_DIRS=( ... ) array in the given file, one per line.
agent_dirs_array() {
  awk '/AGENT_DIRS=\(/{f=1; next} f && /^\)/{exit} f{print}' "$1" \
    | tr ' \t' '\n\n' | grep -E '^[a-z0-9-]+$' | sort -u
}

# Compare canonical vs a candidate set; report both directions.
compare() {
  local label="$1" candidate="$2" canon
  canon="$(canonical)"
  local missing extra
  missing="$(comm -23 <(echo "$canon") <(echo "$candidate"))"
  extra="$(comm -13 <(echo "$canon") <(echo "$candidate"))"
  if [[ -n "$missing" ]]; then
    fail "$label is missing division(s) present in $JSON: $(echo "$missing" | tr '\n' ' ')"
  fi
  if [[ -n "$extra" ]]; then
    fail "$label has division(s) not in $JSON: $(echo "$extra" | tr '\n' ' ')"
  fi
}

# --- checks ----------------------------------------------------------------

[[ -f "$JSON" ]] || { echo "ERROR $JSON not found at repo root"; exit 1; }

compare "the agent directories on disk" "$(actual_dirs)"
compare "scripts/convert.sh AGENT_DIRS" "$(agent_dirs_array scripts/convert.sh)"
compare "scripts/lint-agents.sh AGENT_DIRS" "$(agent_dirs_array scripts/lint-agents.sh)"

# Workflow path filters: every canonical division must appear as `<div>/` in
# the lint workflow, or new divisions silently skip CI.
WF=".github/workflows/lint-agents.yml"
if [[ -f "$WF" ]]; then
  while IFS= read -r div; do
    grep -qE "\b${div}/" "$WF" || fail "$WF has no path filter for division '$div'"
  done < <(canonical)
else
  fail "$WF not found"
fi

# Every entry must have label, icon, and color.
while IFS= read -r div; do
  block="$(awk -v d="\"$div\"" '$0 ~ d"[[:space:]]*:[[:space:]]*\\{" {print; found=1; next} found && /\}/ {print; exit} found {print}' "$JSON")"
  for field in label icon color; do
    echo "$block" | grep -qE "\"$field\"[[:space:]]*:" \
      || fail "division '$div' in $JSON is missing \"$field\""
  done
done < <(canonical)

# Every division must contain at least one agent file: a .md whose first line is
# '---' frontmatter. This is the content-derived backstop that keeps a docs or
# playbook directory (e.g. strategy/, all of whose files are frontmatter-less)
# from being registered as an empty agent division.
has_agent_file() {
  local f first
  while IFS= read -r f; do
    first="$(head -1 "$f" | tr -d '\r')"
    [[ "$first" == "---" ]] && return 0
  done < <(find "$1" -name '*.md' -type f 2>/dev/null)
  return 1
}
while IFS= read -r div; do
  if [[ ! -d "$div" ]]; then
    fail "division '$div' has no directory on disk"
  elif ! has_agent_file "$div"; then
    fail "division '$div' has no agent files (.md with '---' frontmatter) — not a real division"
  fi
done < <(canonical)

# --- result ----------------------------------------------------------------

count="$(canonical | wc -l | tr -d ' ')"
if [[ $errors -gt 0 ]]; then
  echo ""
  echo "FAILED: $errors divisions consistency error(s). $JSON is the source of truth."
  exit 1
fi
echo "PASSED: $count divisions consistent across $JSON, directories, scripts, and CI."
