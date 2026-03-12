#!/usr/bin/env bash
#
# Installs The Agency agent files into your Claude Code agents directory.
#
# Usage: ./scripts/install.sh
#
# By default, agents are installed to ~/.claude/agents/
# Override with: CLAUDE_AGENTS_DIR=/path/to/agents ./scripts/install.sh

set -euo pipefail

AGENT_DIRS=(
  design
  engineering
  marketing
  product
  project-management
  testing
  support
  spatial-computing
  specialized
  strategy
)

TARGET_DIR="${CLAUDE_AGENTS_DIR:-$HOME/.claude/agents}"

echo "Installing The Agency agents to: $TARGET_DIR"
echo ""

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

installed=0
skipped=0

for dir in "${AGENT_DIRS[@]}"; do
  if [[ ! -d "$dir" ]]; then
    echo "WARN  source directory not found, skipping: $dir"
    skipped=$((skipped + 1))
    continue
  fi

  mkdir -p "$TARGET_DIR/$dir"

  for file in "$dir"/*.md; do
    [[ -f "$file" ]] || continue
    # Only install markdown files that look like agent definitions,
    # i.e., those starting with YAML frontmatter ("---").
    first_line="$(head -n 1 "$file" | tr -d '[:space:]')"
    if [[ "$first_line" != '---' ]]; then
      echo "INFO  skipping non-agent markdown file (missing YAML frontmatter): $file"
      continue
    fi
    cp "$file" "$TARGET_DIR/$dir/"
    installed=$((installed + 1))
  done
done

echo "Installed $installed agent file(s) to $TARGET_DIR"

if [[ $skipped -gt 0 ]]; then
  echo "Skipped $skipped missing source director(ies)."
fi

echo ""
echo "Done! Start a Claude Code session and activate any agent:"
echo "  \"Hey Claude, activate Frontend Developer mode\""
