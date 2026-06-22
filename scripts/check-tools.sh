#!/usr/bin/env bash
#
# check-tools.sh — enforce a single source of truth for the supported tool set.
#
# tools.json (repo root) is canonical. This script fails if any of the following
# disagree with it:
#   1. ALL_TOOLS in scripts/install.sh        (exact set — every installable tool)
#   2. valid_tools in scripts/convert.sh      (every converter tool must exist in tools.json)
#   3. Every tools.json entry has id, label, kebab, format, and dest
#
# Add a tool: add an entry to tools.json, a convert_<tool> (or reuse a `format`)
# in convert.sh, and an install_<tool> in install.sh, then run this script — it
# tells you every place that must agree. No deps beyond bash 3.2 + coreutils
# (no jq) so it runs the same on macOS and CI. Mirrors scripts/check-divisions.sh.
#
# Usage: ./scripts/check-tools.sh

set -euo pipefail
cd "$(dirname "$0")/.."

JSON="tools.json"
errors=0
fail() { echo "ERROR $*"; errors=$((errors + 1)); }

# --- helpers ---------------------------------------------------------------

# Canonical tool keys (kebab) from tools.json: the keys at 4-space indent inside
# the "tools" object. One tool per line keeps the nested "scope"/"detect"/…
# objects off the line start, so only tool keys match.
canonical() {
  awk '/"tools"[[:space:]]*:[[:space:]]*\{/{f=1; next} f' "$JSON" \
    | grep -oE '^    "[a-z0-9-]+"' \
    | sed -E 's/.*"([a-z0-9-]+)".*/\1/' | sort -u
}

# Entries of a single-line bash array  NAME=( ... )  (quoted or bare), one per line.
bash_array() {
  grep -oE "$2=\([^)]*\)" "$1" | head -1 | sed -E "s/^$2=\(//; s/\)\$//" \
    | tr -d '"' | tr ' \t' '\n\n' | grep -E '^[a-z0-9-]+$' | sort -u
}

# --- checks ----------------------------------------------------------------

[[ -f "$JSON" ]] || { echo "ERROR $JSON not found at repo root"; exit 1; }

canon="$(canonical)"

# 1. tools.json keys == ALL_TOOLS in install.sh (exact, both directions).
all_tools="$(bash_array scripts/install.sh ALL_TOOLS)"
missing="$(comm -23 <(echo "$canon") <(echo "$all_tools"))"
extra="$(comm -13 <(echo "$canon") <(echo "$all_tools"))"
[[ -n "$missing" ]] && fail "scripts/install.sh ALL_TOOLS is missing tool(s) in $JSON: $(echo $missing)"
[[ -n "$extra"   ]] && fail "scripts/install.sh ALL_TOOLS has tool(s) not in $JSON: $(echo $extra)"

# 2. Every converter in convert.sh must exist in tools.json (subset; identity
#    tools like claude-code/copilot are install-only, so it's a subset not equal).
conv="$(bash_array scripts/convert.sh valid_tools | grep -v '^all$' || true)"
notin="$(comm -13 <(echo "$canon") <(echo "$conv"))"
[[ -n "$notin" ]] && fail "scripts/convert.sh converts tool(s) absent from $JSON: $(echo $notin)"

# 3. Required fields per entry (each tool is one line). aa converts+installs
#    every listed tool, so every entry must carry format + dest — there is no
#    "half-described" tool. (Renderer coverage is a consumer's concern, derived
#    from `format`; the catalog itself carries no such flag.)
while IFS= read -r t; do
  [[ -n "$t" ]] || continue
  line="$(grep -E "^    \"$t\"[[:space:]]*:" "$JSON")"
  for field in id label kebab format dest; do
    echo "$line" | grep -qE "\"$field\":" || fail "tool '$t' in $JSON is missing \"$field\""
  done
done < <(echo "$canon")

# --- result ----------------------------------------------------------------

count="$(echo "$canon" | grep -c .)"
if [[ $errors -gt 0 ]]; then
  echo ""
  echo "FAILED: $errors tool consistency error(s). $JSON is the source of truth."
  exit 1
fi
echo "PASSED: $count tools consistent across $JSON, install.sh, and convert.sh."
