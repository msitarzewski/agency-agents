#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
DEST="${HOME}/.claude/agents"

AGENT_DIRS=(
  design
  engineering
  game-development
  marketing
  paid-media
  product
  project-management
  testing
  support
  spatial-computing
  specialized
  sales
  strategy
)

mkdir -p "$DEST"

count=0
for dir in "${AGENT_DIRS[@]}"; do
  full_dir="$REPO_ROOT/$dir"
  [[ -d "$full_dir" ]] || continue
  for f in "$full_dir"/*.md; do
    [[ -f "$f" ]] || continue
    first_line="$(head -1 "$f")"
    [[ "$first_line" == "---" ]] || continue
    cp "$f" "$DEST/"
    (( count++ )) || true
  done
done

echo "Agency agents: $count agent(s) installed to $DEST"
