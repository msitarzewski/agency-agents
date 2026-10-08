#!/usr/bin/env bash
#
# check-eol.sh — enforce LF line endings across the repository.
#
# `git ls-files --eol` is used as the source of truth.
#
# Usage: ./scripts/check-eol.sh

set -euo pipefail
cd "$(dirname "$0")/.."

errors=0

# --- no CRLF/mixed endings anywhere -------------------------------------------
# git ls-files --eol reports:
#   column 1 = index EOL
#   column 2 = working-tree EOL
#   column 3+ = resolved attributes
# Reject only CRLF/mixed EOL (binary files reported as -text are valid)
eol_info=$(git ls-files --eol)

if bad=$(printf '%s\n' "$eol_info" | awk '
  $1 ~ /^i\/(crlf|mixed)$/ || $2 ~ /^w\/(crlf|mixed)$/ { print }
'); then
  if [[ -n "$bad" ]]; then
    printf 'ERROR: CRLF/mixed line endings found (index/worktree):\n%s\n' "$bad" >&2
    errors=$((errors + 1))
  fi
fi

# --- result -------------------------------------------------------------------
if [[ "$errors" -eq 0 ]]; then
  echo 'OK: tracked text files are LF-clean'
  exit 0
fi

echo "FAILED: $errors check(s) failed" >&2
exit 1
