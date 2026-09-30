#!/usr/bin/env bash
# Existing agents must not be registered again, and failed registration must
# not be reported as a successful OpenClaw install.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/repo/scripts" "$scratch/repo/engineering" \
  "$scratch/repo/integrations/openclaw/example-agent" "$scratch/bin"
cp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/lib.sh" "$scratch/repo/scripts/"
cp "$SCRIPT_DIR/../divisions.json" "$scratch/repo/"
cat > "$scratch/repo/engineering/example.md" <<'EOF'
---
name: Example Agent
description: Example
color: blue
---
# Example Agent
EOF
for f in SOUL.md AGENTS.md IDENTITY.md; do
  printf '# Example Agent\n' > "$scratch/repo/integrations/openclaw/example-agent/$f"
done
cat > "$scratch/bin/openclaw" <<'EOF'
#!/usr/bin/env bash
if [[ "$1 $2 $3" == 'agents list --json' ]]; then
  if [[ "$OPENCLAW_TEST_MODE" == list-fail ]]; then
    exit 48
  elif [[ "$OPENCLAW_TEST_MODE" == existing ]]; then
    printf '[{"id":"example-agent"}]\n'
  else
    printf '[]\n'
  fi
elif [[ "$1 $2" == 'agents add' ]]; then
  printf 'add called\n' >> "$OPENCLAW_TEST_LOG"
  exit 47
else
  exit 1
fi
EOF
chmod +x "$scratch/bin/openclaw"

export OPENCLAW_TEST_LOG="$scratch/add.log"
export PATH="$scratch/bin:$PATH"
export HOME="$scratch/home"
export OPENCLAW_TEST_MODE=existing
bash "$scratch/repo/scripts/install.sh" --tool openclaw --agent example-agent \
  --no-convert --path "$scratch/destination" > "$scratch/existing.log" 2>&1
[[ ! -e "$OPENCLAW_TEST_LOG" ]] || {
  echo 'FAIL: compact JSON existing agent was registered again' >&2
  exit 1
}

export OPENCLAW_TEST_MODE=missing
if bash "$scratch/repo/scripts/install.sh" --tool openclaw --agent example-agent \
  --no-convert --path "$scratch/destination" > "$scratch/missing.log" 2>&1; then
  echo 'FAIL: failed OpenClaw registration was reported as successful' >&2
  exit 1
fi
grep -q 'failed to register' "$scratch/missing.log"

rm -f "$OPENCLAW_TEST_LOG"
export OPENCLAW_TEST_MODE=list-fail
if bash "$scratch/repo/scripts/install.sh" --tool openclaw --agent example-agent \
  --no-convert --path "$scratch/destination" > "$scratch/list-fail.log" 2>&1; then
  echo 'FAIL: failed OpenClaw roster query was reported as successful' >&2
  exit 1
fi
grep -q 'could not list registered agents' "$scratch/list-fail.log"
[[ ! -e "$OPENCLAW_TEST_LOG" ]]
echo 'PASS: OpenClaw existing-agent detection and registration failure reporting'
