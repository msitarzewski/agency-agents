#!/usr/bin/env bash
#
# install-house.sh -- Install ONLY Eclipse Digital's curated house team.
#
# This is the safe default for the pilot. A bare `install.sh` installs every
# agent on disk, including the uncustomized bench agents that carry no Eclipse
# context and no draft policy. This wrapper always scopes the install to the
# house-team manifest so the bench can never leak into your tool config.
#
# Usage:
#   ./scripts/install-house.sh                 # install house team to Claude Code
#   ./scripts/install-house.sh --tool cursor   # any extra flags pass through to install.sh
#
# To install everything on purpose, call ./scripts/install.sh directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$REPO_ROOT/eclipse/eclipse-house-team.agents"

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: house-team manifest not found at $MANIFEST" >&2
  exit 1
fi

# Default to Claude Code (the pilot tool) unless the caller overrides --tool.
extra_args=("$@")
has_tool=false
for arg in "${extra_args[@]}"; do
  [[ "$arg" == "--tool" ]] && has_tool=true
done
if [[ "$has_tool" == false ]]; then
  extra_args=(--tool claude-code "${extra_args[@]}")
fi

exec "$SCRIPT_DIR/install.sh" --agents-file "$MANIFEST" "${extra_args[@]}"
