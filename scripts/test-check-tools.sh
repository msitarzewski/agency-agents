#!/usr/bin/env bash
# check-tools.sh must notice a tool that convert.sh accepts with --tool but
# leaves out of the lists a plain `convert.sh` or `convert.sh --parallel` runs.
#
# Before: only valid_tools was compared with tools.json. Removing a tool from
# tools_to_run (the default "all" run), from parallel_tools, or from the
# sequential aider/windsurf tail still printed PASSED, and the default commands
# in the README then generated nothing for that tool.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/agency-check-tools.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

fail() { echo "FAIL: $*" >&2; sed 's/^/    /' "$tmp/output" >&2; exit 1; }

# A minimal copy of what check-tools.sh reads, so each case can edit convert.sh.
fresh_repo() {
  rm -rf "$tmp/repo"
  mkdir -p "$tmp/repo/scripts"
  cp "$REPO_ROOT/tools.json" "$tmp/repo/"
  cp "$REPO_ROOT/scripts/check-tools.sh" "$REPO_ROOT/scripts/install.sh" \
     "$REPO_ROOT/scripts/convert.sh" "$tmp/repo/scripts/"
}

# The real tree passes.
fresh_repo
bash "$tmp/repo/scripts/check-tools.sh" > "$tmp/output" 2>&1 \
  || fail "check-tools.sh rejected the unmodified tree"

# expect_reject <label> <sed program applied to convert.sh> <expected message>
expect_reject() {
  fresh_repo
  sed -E "$2" "$tmp/repo/scripts/convert.sh" > "$tmp/convert.sh"
  cmp -s "$tmp/convert.sh" "$tmp/repo/scripts/convert.sh" \
    && { echo "FAIL: $1: the edit did not change convert.sh" >&2; exit 1; }
  mv "$tmp/convert.sh" "$tmp/repo/scripts/convert.sh"
  if bash "$tmp/repo/scripts/check-tools.sh" > "$tmp/output" 2>&1; then
    fail "$1: check-tools.sh passed"
  fi
  grep -qF "$3" "$tmp/output" || fail "$1: expected '$3'"
}

expect_reject "dsh missing from the default run" \
  '/tools_to_run=\("antigravity"/s/ "dsh"//' \
  'tools_to_run (plain convert.sh) skips: dsh'
expect_reject "dsh missing from the parallel run" \
  '/parallel_tools=\(antigravity/s/ dsh//' \
  'convert.sh --parallel skips: dsh'
expect_reject "windsurf missing from the parallel tail" \
  's/for t in aider windsurf; do/for t in aider; do/' \
  'convert.sh --parallel skips: windsurf'

echo "PASSED: check-tools.sh catches tools missing from convert.sh's default and parallel runs."
