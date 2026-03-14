#!/usr/bin/env bash
#
# test-kimi-integration.sh — Test Kimi Code CLI integration locally
#
# Finds appropriate Python with PyYAML installed
#
# Usage:
#   ./scripts/test-kimi-integration.sh [--verbose]
#
# This script validates that the Kimi Code integration works correctly by:
#   1. Running convert.sh to generate integration files
#   2. Validating YAML syntax of all generated agent files
#   3. Checking required fields exist in agent specs
#   4. Verifying system prompt files exist
#   5. Testing with Kimi CLI if available

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="/tmp/kimi-agency-test-$$"
VERBOSE=false

# Colors
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  C_GREEN=$'\033[0;32m'
  C_RED=$'\033[0;31m'
  C_YELLOW=$'\033[1;33m'
  C_CYAN=$'\033[0;36m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_RESET=$'\033[0m'
else
  C_GREEN=''; C_RED=''; C_YELLOW=''; C_CYAN=''; C_BOLD=''; C_DIM=''; C_RESET=''
fi

ok()     { printf "${C_GREEN}[✓]${C_RESET} %s\n" "$*"; }
err()    { printf "${C_RED}[✗]${C_RESET} %s\n" "$*" >&2; }
warn()   { printf "${C_YELLOW}[!]${C_RESET} %s\n" "$*"; }
info()   { printf "${C_CYAN}[i]${C_RESET} %s\n" "$*"; }
dim()    { printf "${C_DIM}%s${C_RESET}\n" "$*"; }
header() { printf "\n${C_BOLD}%s${C_RESET}\n" "$*"; }

cleanup() {
  if [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
  fi
}
trap cleanup EXIT

# Find Python with PyYAML
find_python() {
  for py in python3 python /usr/bin/python3 /usr/bin/python; do
    if command -v "$py" >/dev/null 2>&1; then
      if $py -c "import yaml" 2>/dev/null; then
        echo "$py"
        return 0
      fi
    fi
  done
  err "No Python with PyYAML found. Install with: pip install pyyaml"
  exit 1
}
PYTHON=$(find_python)

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose|-v) VERBOSE=true; shift ;;
    --help|-h)
      echo "Usage: $0 [--verbose] [--help]"
      echo ""
      echo "Test Kimi Code CLI integration locally."
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

FAILED=0

header "=== Kimi Code Integration Tests ==="

# Step 1: Generate integration files
header "Step 1: Converting agents..."
if "$REPO_ROOT/scripts/convert.sh" --tool kimi >/dev/null 2>&1; then
  ok "Convert script completed"
else
  err "Convert script failed"
  exit 1
fi

# Count generated agents
AGENT_COUNT=$(find "$REPO_ROOT/integrations/kimi" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
if [[ $AGENT_COUNT -eq 0 ]]; then
  err "No agents generated!"
  exit 1
fi
ok "Generated $AGENT_COUNT agent directories"

# Step 2: Validate YAML syntax
header "Step 2: Validating YAML syntax..."
for agent_file in "$REPO_ROOT"/integrations/kimi/*/agent.yaml; do
  [[ -f "$agent_file" ]] || continue
  agent_name=$(basename "$(dirname "$agent_file")")
  
  if $PYTHON -c "import yaml; yaml.safe_load(open('$agent_file'))" 2>/dev/null; then
    ok "$agent_name/agent.yaml"
  else
    err "$agent_name/agent.yaml - Invalid YAML"
    (( FAILED++ )) || true
  fi
done

# Step 3: Validate schema
header "Step 3: Validating agent schema..."
for agent_file in "$REPO_ROOT"/integrations/kimi/*/agent.yaml; do
  [[ -f "$agent_file" ]] || continue
  agent_name=$(basename "$(dirname "$agent_file")")
  
  errors=()
  
  # Check version
  version=$($PYTHON -c "import yaml; print(yaml.safe_load(open('$agent_file')).get('version', 'MISSING'))" 2>/dev/null)
  if [[ "$version" != "1" ]]; then
    errors+=("version must be 1, got: $version")
  fi
  
  # Check agent.name
  name=$($PYTHON -c "import yaml; print(yaml.safe_load(open('$agent_file')).get('agent', {}).get('name', 'MISSING'))" 2>/dev/null)
  if [[ "$name" == "MISSING" || -z "$name" ]]; then
    errors+=("missing agent.name")
  fi
  
  # Check agent.system_prompt_path
  spp=$($PYTHON -c "import yaml; print(yaml.safe_load(open('$agent_file')).get('agent', {}).get('system_prompt_path', 'MISSING'))" 2>/dev/null)
  if [[ "$spp" == "MISSING" || -z "$spp" ]]; then
    errors+=("missing agent.system_prompt_path")
  fi
  
  # Check agent.tools
  tools=$($PYTHON -c "import yaml; print('HAS_TOOLS' if yaml.safe_load(open('$agent_file')).get('agent', {}).get('tools') else 'MISSING')" 2>/dev/null)
  if [[ "$tools" != "HAS_TOOLS" ]]; then
    errors+=("missing agent.tools")
  fi
  
  if [[ ${#errors[@]} -eq 0 ]]; then
    ok "$agent_name - schema valid"
  else
    err "$agent_name - schema errors:"
    for e in "${errors[@]}"; do
      echo "      $e"
    done
    (( FAILED++ )) || true
  fi
done

# Step 4: Check system prompt files exist
header "Step 4: Checking system prompt files..."
for agent_dir in "$REPO_ROOT"/integrations/kimi/*/; do
  [[ -d "$agent_dir" ]] || continue
  agent_name=$(basename "$agent_dir")
  
  if [[ -f "$agent_dir/system.md" ]]; then
    ok "$agent_name/system.md exists"
  else
    err "$agent_name/system.md missing"
    (( FAILED++ )) || true
  fi
done

# Step 5: Test with Kimi CLI if available
header "Step 5: Testing with Kimi CLI..."
if command -v kimi >/dev/null 2>&1; then
  info "Kimi CLI found: $(kimi --version 2>&1 | head -1)"
  
  # Find first agent
  FIRST_AGENT=$(find "$REPO_ROOT/integrations/kimi" -name "agent.yaml" -print -quit 2>/dev/null)
  
  if [[ -n "$FIRST_AGENT" ]]; then
    # Test that Kimi accepts the agent file (just validate, don't run)
    if kimi --agent-file "$FIRST_AGENT" --help >/dev/null 2>&1; then
      ok "Kimi CLI accepts agent file: $(basename "$(dirname "$FIRST_AGENT")")"
    else
      err "Kimi CLI rejected agent file"
      (( FAILED++ )) || true
    fi
  else
    warn "No agent files found to test"
  fi
else
  warn "Kimi CLI not found, skipping runtime tests"
  dim "    Install from: https://github.com/MoonshotAI/kimi-cli"
fi

# Summary
header "=== Test Summary ==="
if [[ $FAILED -eq 0 ]]; then
  ok "All tests passed!"
  exit 0
else
  err "$FAILED test(s) failed"
  exit 1
fi
