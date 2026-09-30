#!/usr/bin/env bash
# Auto-detected tools must receive the same --path collision guard as explicit lists.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/agency-all-path.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/repo/scripts" "$tmp/repo/engineering" \
  "$tmp/repo/integrations/gemini-cli/agents" "$tmp/repo/integrations/qwen/agents" \
  "$tmp/home/.gemini" "$tmp/home/.qwen"
cp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/lib.sh" "$tmp/repo/scripts/"
cat > "$tmp/repo/divisions.json" <<'EOF'
{
  "divisions": {
    "engineering": {}
  }
}
EOF
cat > "$tmp/repo/engineering/agent.md" <<'EOF'
---
name: Shared Agent
description: Example agent
---
Instructions.
EOF
printf 'Gemini output\n' > "$tmp/repo/integrations/gemini-cli/agents/shared-agent.md"
printf 'Qwen output\n' > "$tmp/repo/integrations/qwen/agents/shared-agent.md"

# Both detected tools write shared-agent.md to the same --path. Before the
# guard, Qwen silently replaced Gemini's file and the install exited zero.
if HOME="$tmp/home" PATH=/usr/bin:/bin bash "$tmp/repo/scripts/install.sh" \
    --no-interactive --tool all --path "$tmp/dest" --no-convert > "$tmp/output" 2>&1; then
  echo 'FAIL: --tool all accepted colliding per-agent outputs' >&2
  exit 1
fi
if [[ -e "$tmp/dest/shared-agent.md" ]]; then
  echo 'FAIL: collision was detected after writing output' >&2
  exit 1
fi
grep -q 'would overwrite each other' "$tmp/output" || {
  echo 'FAIL: collision did not explain the conflicting tools' >&2
  exit 1
}
echo 'PASS: --tool all rejects a shared destination collision before writing'

# Distinct filenames can safely share the override directory.
mkdir -p "$tmp/repo/integrations/codex/agents" "$tmp/compatible-home/.gemini" "$tmp/compatible-home/.codex"
printf 'name = "Shared Agent"\n' > "$tmp/repo/integrations/codex/agents/shared-agent.toml"
if ! HOME="$tmp/compatible-home" PATH=/usr/bin:/bin bash "$tmp/repo/scripts/install.sh" \
    --no-interactive --tool all --path "$tmp/compatible-dest" --no-convert > "$tmp/compatible-output" 2>&1; then
  echo 'FAIL: --tool all rejected tools with distinct output filenames' >&2
  exit 1
fi
[[ -f "$tmp/compatible-dest/shared-agent.md" && -f "$tmp/compatible-dest/shared-agent.toml" ]] || {
  echo 'FAIL: compatible tools did not both install' >&2
  exit 1
}
echo 'PASS: --tool all permits compatible tools to share a destination'
