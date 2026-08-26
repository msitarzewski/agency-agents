#!/usr/bin/env bash
#
# check-cursor-pack.sh — lint integrations/cursor after convert --tool cursor.
#
# Fails if:
#   - any rules/*.mdc other than agency-router.mdc
#   - agency-router.mdc missing or alwaysApply not true
#   - any agent missing name/description frontmatter
#   - any agent body > 200 lines
#
# Usage: ./scripts/check-cursor-pack.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

ROOT="integrations/cursor"
errors=0
fail() { echo "ERROR $*"; errors=$((errors + 1)); }

[[ -d "$ROOT/agents" ]] || { echo "ERROR $ROOT/agents missing — run ./scripts/convert.sh --tool cursor"; exit 1; }

# Only agency-router.mdc under rules/
if [[ -d "$ROOT/rules" ]]; then
  while IFS= read -r -d '' f; do
    base="$(basename "$f")"
    if [[ "$base" != "agency-router.mdc" ]]; then
      fail "unexpected persona/rule file: $f (only agency-router.mdc allowed)"
    fi
  done < <(find "$ROOT/rules" -type f -name '*.mdc' -print0)
fi

router="$ROOT/rules/agency-router.mdc"
[[ -f "$router" ]] || fail "missing $router"
if [[ -f "$router" ]]; then
  grep -qE '^alwaysApply:[[:space:]]*true[[:space:]]*$' "$router" \
    || fail "$router must set alwaysApply: true"
  lines="$(wc -l < "$router" | tr -d ' ')"
  [[ "$lines" -le 60 ]] || fail "$router is $lines lines (prefer ≤60)"
fi

agent_count=0
while IFS= read -r -d '' f; do
  agent_count=$((agent_count + 1))
  name="$(awk '/^---$/{fm++; next} fm==1 && /^name: /{sub(/^name: /,""); print; exit}' "$f")"
  desc="$(awk '/^---$/{fm++; next} fm==1 && /^description:/{print; exit}' "$f")"
  [[ -n "$name" ]] || fail "$f missing name frontmatter"
  [[ -n "$desc" ]] || fail "$f missing description frontmatter"
  body_lines="$(awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{n++} END{print n+0}' "$f")"
  [[ "$body_lines" -le 200 ]] || fail "$f body is $body_lines lines (max 200)"
done < <(find "$ROOT/agents" -type f -name '*.md' -print0)

[[ "$agent_count" -gt 0 ]] || fail "no agent files under $ROOT/agents"

if [[ -f "$ROOT/catalog/roster.json" ]]; then
  # Rough entry count: "slug" fields
  roster_n="$(grep -o '"slug"' "$ROOT/catalog/roster.json" | wc -l | tr -d ' ')"
  if [[ "$roster_n" -ne "$agent_count" ]]; then
    fail "roster.json slug count ($roster_n) != agent file count ($agent_count)"
  fi
else
  fail "missing $ROOT/catalog/roster.json"
fi

if [[ $errors -gt 0 ]]; then
  echo ""
  echo "FAILED: $errors cursor pack lint error(s)."
  exit 1
fi
echo "PASSED: cursor pack OK ($agent_count agents, router-only rules)."
