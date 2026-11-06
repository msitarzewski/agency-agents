#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/repo/scripts" "$scratch/repo/integrations/vibe/agents" "$scratch/repo/integrations/vibe/prompts" "$scratch/home"
cp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/lib.sh" "$scratch/repo/scripts/"
cp "$SCRIPT_DIR/../divisions.json" "$scratch/repo/"
printf 'agent_type = "agent"\n' > "$scratch/repo/integrations/vibe/agents/example.toml"
if HOME="$scratch/home" bash "$scratch/repo/scripts/install.sh" --no-interactive --no-convert --tool vibe --path "$scratch/dest" > "$scratch/result" 2>&1; then
  echo 'FAIL: a missing required prompt reported install success' >&2; exit 1
fi
grep -q 'example.*prompt' "$scratch/result"
printf '# Example\n' > "$scratch/repo/integrations/vibe/prompts/example.md"
HOME="$scratch/home" bash "$scratch/repo/scripts/install.sh" --no-interactive --no-convert --tool vibe --path "$scratch/dest" > "$scratch/result" 2>&1
[[ -f "$scratch/dest/agents/example.toml" && -f "$scratch/dest/prompts/example.md" ]]
echo 'PASS: missing prompt fails, complete pair installs'
