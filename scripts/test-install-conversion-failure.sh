#!/usr/bin/env bash
# A failed automatic conversion must not install a partial generated roster.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-failure.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/repo/scripts" "$tmp/repo/integrations/codex" "$tmp/repo/engineering" "$tmp/home"
cp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/lib.sh" "$tmp/repo/scripts/"
cat > "$tmp/repo/divisions.json" <<'EOF'
{
  "divisions": {
    "engineering": {}
  }
}
EOF
for name in first second; do
  cat > "$tmp/repo/engineering/$name.md" <<EOF
---
name: $name
description: $name agent
---
Instructions for $name.
EOF
done
printf 'Generated output placeholder\n' > "$tmp/repo/integrations/codex/README.md"

# Simulate an interrupted converter that leaves one of two agents generated.
cat > "$tmp/repo/scripts/convert.sh" <<'EOF'
#!/usr/bin/env bash
mkdir -p "$(dirname "$0")/../integrations/codex/agents"
printf 'name = "first"\n' > "$(dirname "$0")/../integrations/codex/agents/first.toml"
exit 23
EOF
chmod +x "$tmp/repo/scripts/convert.sh"

if HOME="$tmp/home" bash "$tmp/repo/scripts/install.sh" --no-interactive --tool codex > "$tmp/output" 2>&1; then
  echo 'FAIL: install succeeded after automatic conversion failed' >&2
  exit 1
fi
if [[ -d "$tmp/home/.codex/agents" ]] && find "$tmp/home/.codex/agents" -type f | grep -q .; then
  echo 'FAIL: install copied incomplete generated output' >&2
  exit 1
fi
if [[ -e "$tmp/repo/integrations/codex/agents/first.toml" ]]; then
  echo 'FAIL: partial generated output would be used on the next install' >&2
  exit 1
fi
grep -q 'convert.sh failed' "$tmp/output" || {
  echo 'FAIL: conversion failure was not reported' >&2
  exit 1
}
echo 'PASS: failed conversion stops installation before copying partial output'
