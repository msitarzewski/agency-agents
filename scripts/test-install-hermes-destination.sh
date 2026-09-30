#!/usr/bin/env bash
# Hermes installation must replace only a directory owned by this plugin.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/agency-hermes-dest.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
repo="$tmp/repo"
home="$tmp/home"
plugin="$home/.hermes/plugins/agency-agents-router"
mkdir -p "$repo/scripts" "$repo/engineering" \
  "$repo/integrations/hermes/agency-agents-router/data" "$plugin"
cp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/lib.sh" "$repo/scripts/"
cat > "$repo/divisions.json" <<'EOF'
{
  "divisions": {
    "engineering": {}
  }
}
EOF
cat > "$repo/integrations/hermes/agency-agents-router/plugin.yaml" <<'EOF'
name: agency-agents-router
EOF
printf '# Plugin\n' > "$repo/integrations/hermes/agency-agents-router/__init__.py"
printf '[]\n' > "$repo/integrations/hermes/agency-agents-router/data/agents.json"
printf 'personal content\n' > "$plugin/personal.txt"

if HOME="$home" bash "$repo/scripts/install.sh" --no-interactive --tool hermes --no-convert > "$tmp/output" 2>&1; then
  echo 'FAIL: Hermes replaced an unrelated directory with the plugin name' >&2
  exit 1
fi
[[ -f "$plugin/personal.txt" ]] || {
  echo 'FAIL: Hermes removed unrelated user content' >&2
  exit 1
}
grep -q 'refusing to replace' "$tmp/output" || {
  echo 'FAIL: Hermes rejection did not explain the destination conflict' >&2
  exit 1
}
echo 'PASS: unrelated destination remains untouched'

cat > "$plugin/plugin.yaml" <<'EOF'
name: agency-agents-router
EOF
printf 'outdated\n' > "$plugin/old.txt"
HOME="$home" bash "$repo/scripts/install.sh" --no-interactive --tool hermes --no-convert > "$tmp/upgrade-output" 2>&1
[[ -f "$plugin/__init__.py" && -f "$plugin/data/agents.json" && ! -e "$plugin/old.txt" ]] || {
  echo 'FAIL: a prior Agency plugin was not upgraded' >&2
  exit 1
}
echo 'PASS: a prior Agency plugin upgrades normally'

fresh_home="$tmp/fresh-home"
HOME="$fresh_home" bash "$repo/scripts/install.sh" --no-interactive --tool hermes --no-convert > "$tmp/fresh-output" 2>&1
[[ -f "$fresh_home/.hermes/plugins/agency-agents-router/plugin.yaml" ]] || {
  echo 'FAIL: fresh Hermes installation did not create the plugin' >&2
  exit 1
}
echo 'PASS: fresh Hermes installation works normally'

# A trailing slash must not turn "replace the plugin" into "empty whatever a
# symlink points at": `rm -rf link/` follows the link and deletes the target's
# contents. Seen on real installs via HERMES_PLUGIN_DIR=".../agency-agents-router/".
link_home="$tmp/link-home"
link_plugin="$link_home/.hermes/plugins/agency-agents-router"
personal="$tmp/personal"
mkdir -p "$personal" "$(dirname "$link_plugin")"
printf 'name: agency-agents-router\n' > "$personal/plugin.yaml"
printf 'personal content\n' > "$personal/personal.txt"
ln -s "$personal" "$link_plugin"
HOME="$link_home" HERMES_PLUGIN_DIR="$link_plugin/" bash "$repo/scripts/install.sh" --no-interactive --tool hermes --no-convert > "$tmp/slash-output" 2>&1 || true
[[ -f "$personal/personal.txt" ]] || {
  echo 'FAIL: a trailing slash deleted the contents of a symlinked directory' >&2
  exit 1
}
echo 'PASS: a trailing slash on a symlinked destination leaves its target intact'

relink_home="$tmp/relink-home"
HOME="$relink_home" bash "$repo/scripts/install.sh" --no-interactive --tool hermes --no-convert --link > "$tmp/link-output" 2>&1
HOME="$relink_home" HERMES_PLUGIN_DIR="$relink_home/.hermes/plugins/agency-agents-router/" \
  bash "$repo/scripts/install.sh" --no-interactive --tool hermes --no-convert > "$tmp/relink-output" 2>&1
[[ -f "$repo/integrations/hermes/agency-agents-router/plugin.yaml" ]] || {
  echo 'FAIL: re-installing over a --link install deleted the plugin source in the clone' >&2
  exit 1
}
echo 'PASS: re-installing over a --link install keeps the clone intact'
