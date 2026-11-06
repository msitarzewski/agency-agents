#!/usr/bin/env bash
# Runs once when the Codespace / dev container is created.
set -euo pipefail
echo "== ffmpeg (video tools)"
sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg >/dev/null
echo "== uv + mcp-video"
pip install --user -q uv mcp-video
echo "== Jaystudio Brand OS"
cd apps/jaystudio
npm install --no-fund --no-audit
[ -f .env ] || cp .env.example .env
echo "Xong. App tự chạy ở cổng 4321 (tab Ports). Video toolkit + Pixelle: bash .claude/skills/jaystudio/setup.sh"
