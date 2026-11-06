#!/usr/bin/env bash
# Jaystudio setup: installs the CLI/runtime pieces behind the Jaystudio skill.
# The skill files and .mcp.json are already in this repo; this installs the binaries they call.
set -euo pipefail

echo "== 1. Remotion skills: bundled in .claude/skills/jaystudio/remotion (refresh: npx skills add remotion-dev/skills)"

echo "== 2. mcp-video"
pip install -U mcp-video || pip install --user -U mcp-video
mcp-video doctor || true

echo "== 3. VibeFrame MCP (pre-fetch)"
npm view @vibeframe/mcp-server version >/dev/null && echo "vibeframe available via npx"

echo "== 4. Claude Code Video Toolkit"
ROOT="${VIDEO_TOOLKIT_ROOT:-$HOME/claude-code-video-toolkit}"
if [ -d "$ROOT/.git" ]; then git -C "$ROOT" pull --ff-only || true
else git clone --depth 1 https://github.com/digitalsamba/claude-code-video-toolkit "$ROOT"; fi
(cd "$ROOT" && uv sync --extra mcp >/dev/null && uv run tools/verify_setup.py || true)

echo "== 5. Pixelle-MCP (Python 3.11 via uv)"
uv tool install --python 3.11 pixelle || uv tool upgrade pixelle
echo "Run 'pixelle init' once (ComfyUI URL or RunningHub key + LLM), then 'pixelle start'."

echo "Done. MCP servers are registered in .mcp.json (mcp-video, vibeframe, video-toolkit, pixelle)."
