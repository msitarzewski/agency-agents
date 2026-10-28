#!/usr/bin/env bash
# A failed parallel converter must expose its buffered error and clean up.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-failure.XXXXXX")"
trap 'rm -rf "$FIXTURE"' EXIT

# An empty roster makes this fast. Hermes intentionally lacks its builder.
mkdir -p "$FIXTURE/repo/scripts"
cp "$SCRIPT_DIR/convert.sh" "$SCRIPT_DIR/lib.sh" "$FIXTURE/repo/scripts/"

status=0
TMPDIR="$FIXTURE" "$FIXTURE/repo/scripts/convert.sh" \
  --tool all --parallel --jobs 2 --out "$FIXTURE/output" \
  > "$FIXTURE/run.log" 2>&1 || status=$?

[[ "$status" -ne 0 ]] || { echo "parallel conversion unexpectedly succeeded" >&2; exit 1; }
grep -Fq 'build-hermes-plugin.py' "$FIXTURE/run.log" || {
  echo "parallel converter error was hidden in its buffered output" >&2
  exit 1
}
if find "$FIXTURE" -mindepth 1 -maxdepth 1 -type d -name 'agency-convert-parallel.*' | grep -q .; then
  echo "parallel conversion left its buffered output directory behind" >&2
  exit 1
fi

# The same empty-roster fixture succeeds once its one missing converter exists.
printf 'import sys\n' > "$FIXTURE/repo/scripts/build-hermes-plugin.py"
TMPDIR="$FIXTURE" "$FIXTURE/repo/scripts/convert.sh" \
  --tool all --parallel --jobs 2 --out "$FIXTURE/output" \
  > "$FIXTURE/success.log" 2>&1
# Identity targets copy source files; every other registered target is rendered.
# Read the independent catalog instead of pinning the current converter count.
expected_tools="$(python3 - "$SCRIPT_DIR/../tools.json" <<'PYCOUNT'
import json, sys
with open(sys.argv[1], encoding="utf-8") as source:
    tools = json.load(source)["tools"]
print(sum(tool["format"] != "identity" for tool in tools.values()))
PYCOUNT
)"
grep -Fq "Done. $expected_tools tools" "$FIXTURE/success.log" || {
  echo "parallel converter did not finish all $expected_tools registered targets" >&2
  cat "$FIXTURE/success.log" >&2
  exit 1
}

echo "PASS: parallel converter reports failure and cleans buffered logs"
