#!/usr/bin/env bash
#
# test-cursor-pack.sh — high-signal regression tests for Cursor convert+install.
#
# Covers:
#   1. cursor_guard_source / enrich / classify helpers (unit)
#   2. staged pack invariants via check-cursor-pack.sh
#   3. install --tool cursor --division engineering --dry-run (agents + router)
#   4. install --tool claude-code --dry-run smoke (unchanged path)
#
# Usage: ./scripts/test-cursor-pack.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_ROOT="$(pwd)"
errors=0
passed=0

fail() { echo "FAIL: $*"; errors=$((errors + 1)); }
pass() { echo "PASS: $*"; passed=$((passed + 1)); }

# ---------------------------------------------------------------------------
# 1. Unit: extract cursor helpers from convert.sh (avoid running main)
# ---------------------------------------------------------------------------
error() { printf '%s\n' "$*" >&2; }

eval "$(sed -n \
  -e '/^cursor_classify_header()/,/^}$/p' \
  -e '/^cursor_enrich_description()/,/^}$/p' \
  -e '/^cursor_guard_source()/,/^}$/p' \
  "$REPO_ROOT/scripts/convert.sh")"

# Guard: reject .mdc
if cursor_guard_source "/tmp/fake-persona.mdc" 2>/dev/null; then
  fail "cursor_guard_source should reject .mdc input"
else
  pass "cursor_guard_source rejects .mdc"
fi

# Guard: reject integrations/cursor paths
if cursor_guard_source "$REPO_ROOT/integrations/cursor/rules/agency-router.mdc" 2>/dev/null; then
  fail "cursor_guard_source should reject integrations/cursor paths"
else
  pass "cursor_guard_source rejects integrations/cursor paths"
fi

# Guard: allow division Claude .md
if cursor_guard_source "$REPO_ROOT/engineering/engineering-frontend-developer.md"; then
  pass "cursor_guard_source allows division Claude *.md"
else
  fail "cursor_guard_source should allow division Claude *.md"
fi

# Enrich: append Use when… when missing
enriched="$(cursor_enrich_description "Frontend specialist." "Frontend Developer")"
case "$enriched" in
  *"Use when"*"Frontend Developer"*) pass "cursor_enrich_description appends Use when…" ;;
  *) fail "cursor_enrich_description missing Use when… (got: $enriched)" ;;
esac

# Enrich: leave existing Use when alone
already="Does X. Use when shipping UI."
enriched2="$(cursor_enrich_description "$already" "Frontend Developer")"
if [[ "$enriched2" == "$already" ]]; then
  pass "cursor_enrich_description keeps existing Use when"
else
  fail "cursor_enrich_description should not rewrite existing Use when"
fi

# Classify: a few deterministic buckets
[[ "$(cursor_classify_header '## Identity')" == "identity" ]] \
  && pass "cursor_classify_header identity" \
  || fail "cursor_classify_header identity expected"
[[ "$(cursor_classify_header '## Learning Goals')" == "cut" ]] \
  && pass "cursor_classify_header cut/learning" \
  || fail "cursor_classify_header cut/learning expected"
[[ "$(cursor_classify_header '## Core Mission')" == "mission" ]] \
  && pass "cursor_classify_header mission" \
  || fail "cursor_classify_header mission expected"

# ---------------------------------------------------------------------------
# 2. Pack invariants (committed or post-convert integrations/cursor)
# ---------------------------------------------------------------------------
if "$REPO_ROOT/scripts/check-cursor-pack.sh"; then
  pass "check-cursor-pack.sh invariants"
else
  fail "check-cursor-pack.sh invariants"
fi

# ---------------------------------------------------------------------------
# 3. Cursor install dry-run mentions agents + router
# ---------------------------------------------------------------------------
cursor_out="$(NO_COLOR=1 "$REPO_ROOT/scripts/install.sh" \
  --tool cursor --division engineering --dry-run 2>&1 || true)"

echo "$cursor_out" | grep -qE 'Dry run' \
  && pass "cursor dry-run exits with plan header" \
  || fail "cursor dry-run missing Dry run header"

echo "$cursor_out" | grep -qE 'Cursor plan:' \
  && pass "cursor dry-run prints Cursor plan" \
  || fail "cursor dry-run missing Cursor plan"

echo "$cursor_out" | grep -qE 'agents:.*flattened' \
  && pass "cursor dry-run mentions flattened agents" \
  || fail "cursor dry-run missing agents plan line"

echo "$cursor_out" | grep -qE 'router:.*agency-router\.mdc' \
  && pass "cursor dry-run mentions agency-router.mdc" \
  || fail "cursor dry-run missing router plan line"

# ---------------------------------------------------------------------------
# 4. Claude Code dry-run smoke (install path untouched)
# ---------------------------------------------------------------------------
claude_rc=0
claude_out="$(NO_COLOR=1 "$REPO_ROOT/scripts/install.sh" \
  --tool claude-code --dry-run 2>&1)" || claude_rc=$?

if [[ "$claude_rc" -eq 0 ]]; then
  pass "claude-code dry-run exits 0"
else
  fail "claude-code dry-run exited $claude_rc"
fi

echo "$claude_out" | grep -qE 'Dry run' \
  && pass "claude-code dry-run prints plan" \
  || fail "claude-code dry-run missing Dry run header"

echo "$claude_out" | grep -qE 'Tools:[[:space:]]+claude-code' \
  && pass "claude-code dry-run selects claude-code" \
  || fail "claude-code dry-run did not select claude-code"

# Claude Code plan must not grow a Cursor-only router block
if echo "$claude_out" | grep -qE 'Cursor plan:|agency-router\.mdc'; then
  fail "claude-code dry-run unexpectedly mentions Cursor router plan"
else
  pass "claude-code dry-run has no Cursor router plan"
fi

# ---------------------------------------------------------------------------
# 5. Real install to tempdir (flatten + router-only rules)
# ---------------------------------------------------------------------------
if [[ ! -d "$REPO_ROOT/integrations/cursor/agents" ]]; then
  fail "integrations/cursor/agents missing — run ./scripts/convert.sh --tool cursor first"
else
  tmp="$(mktemp -d)"
  install_rc=0
  (
    cd "$tmp"
    NO_COLOR=1 "$REPO_ROOT/scripts/install.sh" \
      --tool cursor --division engineering --no-interactive --no-convert
  ) >/dev/null 2>&1 || install_rc=$?

  if [[ "$install_rc" -ne 0 ]]; then
    fail "cursor temp install exited $install_rc"
  else
    pass "cursor temp install exits 0"
  fi

  agent_n="$(find "$tmp/.cursor/agents" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${agent_n:-0}" -gt 0 ]]; then
    pass "cursor temp install flattened agents ($agent_n)"
  else
    fail "cursor temp install produced no .cursor/agents/*.md"
  fi

  # No nested division dirs under installed agents/
  if find "$tmp/.cursor/agents" -mindepth 1 -type d 2>/dev/null | grep -q .; then
    fail "cursor temp install left nested agent directories (expected flatten)"
  else
    pass "cursor temp install agents are flattened"
  fi

  rule_n="$(find "$tmp/.cursor/rules" -type f -name '*.mdc' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "$rule_n" -eq 1 ]] && [[ -f "$tmp/.cursor/rules/agency-router.mdc" ]]; then
    pass "cursor temp install rules are router-only"
  else
    fail "cursor temp install expected sole agency-router.mdc (got $rule_n mdc files)"
  fi

  rm -rf "$tmp"
fi

# ---------------------------------------------------------------------------
echo ""
if [[ "$errors" -gt 0 ]]; then
  echo "FAILED: $errors test(s); $passed passed."
  exit 1
fi
echo "OK: $passed cursor pack/install tests passed."
exit 0
