#!/usr/bin/env bash
#
# setup.sh -- Install novyx-mcp for persistent agent memory.
#
# Usage:
#   ./integrations/novyx-memory/setup.sh

set -euo pipefail

echo "Installing novyx-mcp..."

if command -v pip3 >/dev/null 2>&1; then
  pip3 install novyx-mcp
elif command -v pip >/dev/null 2>&1; then
  pip install novyx-mcp
else
  echo "Error: pip not found. Install Python 3 first." >&2
  exit 1
fi

# Verify installation
if python3 -c "import novyx_mcp" 2>/dev/null; then
  echo ""
  echo "novyx-mcp installed successfully."
  echo ""
  echo "Next steps:"
  echo "  1. Add novyx-mcp to your MCP client config (see integrations/novyx-memory/README.md)"
  echo "  2. Add a Memory Integration section to any agent prompt"
  echo "  3. Memories are stored locally in ~/.novyx/local.db by default"
  echo "  4. Set NOVYX_API_KEY to enable cloud sync (optional)"
else
  echo "Error: novyx-mcp installed but could not be imported." >&2
  exit 1
fi
