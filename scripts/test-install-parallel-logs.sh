#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/repo/scripts" "$scratch/repo/engineering" "$scratch/repo/integrations" "$scratch/home"
cp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/lib.sh" "$scratch/repo/scripts/"
cp "$SCRIPT_DIR/../divisions.json" "$scratch/repo/"
export HOME="$scratch/home"
export CLAUDE_CONFIG_DIR="$HOME/.claude" COPILOT_AGENT_DIR="$HOME/.github/agents"
for agent in first second; do
  printf '%s\n' '---' "name: $agent" 'description: Example agent' 'color: blue' '---' '# Example agent' > "$scratch/repo/engineering/$agent.md"
done
mkdir -p "$scratch/bin" "$scratch/tmp"
cat > "$scratch/bin/cp" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"/.claude/agents/"* && "${FAIL_WORKER:-yes}" == yes ]]; then
  echo 'fixture worker copy failed' >&2
  exit 47
fi
exec /bin/cp "$@"
EOF
chmod +x "$scratch/bin/cp"
export PATH="$scratch/bin:$PATH" TMPDIR="$scratch/tmp"
expected_status=0
printf 'failure\n' | xargs -P 2 -I {} sh -c 'exit 47' || expected_status=$?
status=0
bash "$scratch/repo/scripts/install.sh" --tool claude-code,copilot --division engineering \
  --no-convert --parallel --jobs 2 > "$scratch/failure.log" 2>&1 || status=$?
[[ "$status" == "$expected_status" && "$status" != 0 ]] || { cat "$scratch/failure.log"; echo "FAIL: worker failure status changed: $status"; exit 1; }
grep -q 'fixture worker copy failed' "$scratch/failure.log" || {
  echo 'FAIL: buffered worker failure is hidden' >&2; exit 1;
}
[[ -f "$HOME/.github/agents/first.md" ]]
if grep -q 'Done!  Installed' "$scratch/failure.log"; then
  echo 'FAIL: a failed parallel install still reported Done' >&2; exit 1
fi
[[ -z "$(ls -A "$scratch/tmp")" ]] || { echo 'FAIL: worker output directory leaked'; exit 1; }
export FAIL_WORKER=no
bash "$scratch/repo/scripts/install.sh" --tool claude-code,copilot --division engineering \
  --no-convert --parallel --jobs 2 > "$scratch/success.log" 2>&1
grep -q 'Done!  Installed 2 tool(s)' "$scratch/success.log"
[[ -f "$HOME/.claude/agents/first.md" ]]
[[ -z "$(ls -A "$scratch/tmp")" ]]
echo 'PASS: failed parallel worker logs are replayed, status is preserved, and buffers are removed'
