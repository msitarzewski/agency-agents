#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

./scripts/convert.sh --out "$TMP_DIR" >/tmp/agency_integrations_convert.out 2>/tmp/agency_integrations_convert.err

check_dir() {
  local path="$1"
  [[ -d "$path" ]] || { echo "ERROR missing directory: $path" >&2; exit 1; }
}

check_glob() {
  local pattern="$1"
  compgen -G "$pattern" >/dev/null || { echo "ERROR no files matched: $pattern" >&2; exit 1; }
}

check_dir "$TMP_DIR/antigravity"
check_glob "$TMP_DIR/antigravity/*/SKILL.md"

check_dir "$TMP_DIR/gemini-cli/skills"
[[ -f "$TMP_DIR/gemini-cli/gemini-extension.json" ]] || { echo "ERROR missing gemini-extension.json" >&2; exit 1; }
check_glob "$TMP_DIR/gemini-cli/skills/*/SKILL.md"

check_dir "$TMP_DIR/opencode/agents"
check_glob "$TMP_DIR/opencode/agents/*.md"

check_dir "$TMP_DIR/cursor/rules"
check_glob "$TMP_DIR/cursor/rules/*.mdc"

[[ -f "$TMP_DIR/aider/CONVENTIONS.md" ]] || { echo "ERROR missing aider CONVENTIONS.md" >&2; exit 1; }
[[ -f "$TMP_DIR/windsurf/.windsurfrules" ]] || { echo "ERROR missing windsurf .windsurfrules" >&2; exit 1; }

check_dir "$TMP_DIR/openclaw"
check_glob "$TMP_DIR/openclaw/*/SOUL.md"
check_glob "$TMP_DIR/openclaw/*/AGENTS.md"
check_glob "$TMP_DIR/openclaw/*/IDENTITY.md"

check_dir "$TMP_DIR/qwen/agents"
check_glob "$TMP_DIR/qwen/agents/*.md"

check_dir "$TMP_DIR/kimi"
check_glob "$TMP_DIR/kimi/*/agent.yaml"
check_glob "$TMP_DIR/kimi/*/system.md"

python3 - <<'PY2'
from pathlib import Path
import re
import sys

readme = Path('README.md').read_text(encoding='utf-8')
integ = Path('integrations/README.md').read_text(encoding='utf-8')
patterns = {
    'Claude Code': r'Claude Code',
    'GitHub Copilot': r'GitHub Copilot|Copilot',
    'Antigravity': r'Antigravity',
    'Gemini CLI': r'Gemini CLI',
    'OpenCode': r'OpenCode',
    'OpenClaw': r'OpenClaw',
    'Cursor': r'Cursor',
    'Aider': r'Aider',
    'Windsurf': r'Windsurf',
    'Qwen Code': r'Qwen Code|Qwen',
    'Kimi Code': r'Kimi Code|Kimi',
}
errors = []
for label, pattern in patterns.items():
    if not re.search(pattern, readme):
        errors.append(f'README.md missing tool reference: {label}')
    if not re.search(pattern, integ):
        errors.append(f'integrations/README.md missing tool reference: {label}')
if errors:
    for item in errors:
        print(f'ERROR {item}', file=sys.stderr)
    sys.exit(1)
PY2

echo "Integration lint: PASS (convert output + documentation tool references)"
