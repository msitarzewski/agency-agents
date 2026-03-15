#!/usr/bin/env bash
#
# setup.sh -- Install an MCP-compatible memory server for persistent agent memory.
#
# Usage:
#   ./integrations/mcp-memory/setup.sh

set -euo pipefail

echo "MCP Memory Integration Setup"
echo "=============================="
echo ""

# Install your preferred MCP memory server.
# The memory integration requires an MCP server that provides:
#   - remember: store decisions, deliverables, context
#   - recall: search memories by keyword or semantic similarity
#   - rollback: revert to a previous state
#
# Example (replace with your chosen server):
#   pip install <your-mcp-memory-server>
#   npm install <your-mcp-memory-server>

echo "This integration requires an MCP-compatible memory server."
echo ""
echo "Your MCP memory server must provide these tools:"
echo "  - remember: store decisions, deliverables, and context"
echo "  - recall: search memories by keyword or semantic similarity"
echo "  - rollback: revert to a previous state"
echo "  - search: find specific memories across sessions"
echo ""
echo "Install your preferred MCP memory server, then add it to your"
echo "MCP client config. See integrations/mcp-memory/README.md for details."
echo ""

# Check if an MCP client config exists in common locations
CONFIG_FOUND=false

if [ -f "$HOME/.config/claude/mcp.json" ]; then
  echo "Found MCP config at ~/.config/claude/mcp.json"
  CONFIG_FOUND=true
fi

if [ -f "$HOME/.cursor/mcp.json" ]; then
  echo "Found MCP config at ~/.cursor/mcp.json"
  CONFIG_FOUND=true
fi

if [ -f ".mcp.json" ]; then
  echo "Found MCP config at .mcp.json"
  CONFIG_FOUND=true
fi

if [ "$CONFIG_FOUND" = false ]; then
  echo "No MCP client config found."
  echo ""
  echo "Add your memory server to your MCP client config:"
  echo ""
  echo '  {'
  echo '    "mcpServers": {'
  echo '      "memory": {'
  echo '        "command": "your-mcp-memory-server",'
  echo '        "args": []'
  echo '      }'
  echo '    }'
  echo '  }'
fi

echo ""
echo "Next steps:"
echo "  1. Install an MCP memory server (pip install or npm install)"
echo "  2. Add it to your MCP client config"
echo "  3. Add a Memory Integration section to any agent prompt"
echo "     (see integrations/mcp-memory/README.md for the pattern)"
