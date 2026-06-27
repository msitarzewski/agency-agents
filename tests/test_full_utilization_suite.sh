#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

run_expect_success() {
  local cmd="$1"
  if ! bash -lc "$cmd" >/tmp/agency_test.out 2>/tmp/agency_test.err; then
    echo "STDOUT:" >&2
    sed -n '1,120p' /tmp/agency_test.out >&2 || true
    echo "STDERR:" >&2
    sed -n '1,120p' /tmp/agency_test.err >&2 || true
    fail "command failed: $cmd"
  fi
}

run_expect_success "./scripts/lint-agents.sh"
run_expect_success "./scripts/lint-strategy.sh"
run_expect_success "./scripts/lint-integrations.sh"
run_expect_success "./scripts/lint-all.sh"

test -f docs/full-utilization-guide.md || fail "missing docs/full-utilization-guide.md"
rg -n "lint-all\.sh|full-utilization-guide\.md" README.md >/tmp/agency_test.grep 2>/tmp/agency_test.grep.err \
  || fail "README.md does not reference lint-all.sh and full-utilization-guide.md"

echo "PASS: full utilization suite"
