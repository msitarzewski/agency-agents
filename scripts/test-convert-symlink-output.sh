#!/usr/bin/env bash
# Conversion must not follow a tool-output symlink into unrelated files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

mkdir -p "$scratch/repo/scripts" "$scratch/repo/engineering" \
  "$scratch/output" "$scratch/private/agents"
cp "$SCRIPT_DIR/convert.sh" "$SCRIPT_DIR/lib.sh" "$scratch/repo/scripts/"
cat > "$scratch/repo/engineering/example.md" <<'EOF'
---
name: Example Agent
description: Example
color: blue
---
# Example Agent
EOF

printf 'private content\n' > "$scratch/private/agents/example-agent.md"
ln -s "$scratch/private" "$scratch/output/gemini-cli"
if bash "$scratch/repo/scripts/convert.sh" --tool gemini-cli --out "$scratch/output" > "$scratch/log" 2>&1; then
  echo 'FAIL: converter accepted a symlinked output directory' >&2
  exit 1
fi
grep -q 'refusing symlinked output' "$scratch/log"
[[ "$(cat "$scratch/private/agents/example-agent.md")" == 'private content' ]]
echo 'PASS: symlinked output refused before unrelated content changed'
