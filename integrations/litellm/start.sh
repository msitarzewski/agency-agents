#!/usr/bin/env bash
# XCT Agent Gateway — startup script for Plan B (A2A full integration)
#
# Usage:
#   ./start.sh [--litellm-base URL] [--litellm-key KEY] [--model MODEL] [--port PORT]
#   ./start.sh --stop   # kill running gateway

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GATEWAY_DIR="$SCRIPT_DIR/gateway"

LITELLM_BASE="${LITELLM_API_BASE:-http://localhost:4000}"
LITELLM_KEY="${LITELLM_API_KEY:-sk-1234}"
DEFAULT_MODEL="${DEFAULT_MODEL:-fake-openai-endpoint}"
GATEWAY_PORT="${GATEWAY_PORT:-9000}"
PID_FILE="/tmp/xct_agent_gateway.pid"
LOG_FILE="/tmp/xct_agent_gateway.log"

if [[ "${1:-}" == "--stop" ]]; then
  if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null && echo "Gateway stopped (PID $PID)" || echo "Process not found"
    rm -f "$PID_FILE"
  else
    pkill -f "xct-agents/integrations/litellm/gateway" 2>/dev/null && echo "Gateway stopped" || echo "No gateway running"
  fi
  exit 0
fi

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --litellm-base) LITELLM_BASE="$2"; shift 2;;
    --litellm-key)  LITELLM_KEY="$2"; shift 2;;
    --model)        DEFAULT_MODEL="$2"; shift 2;;
    --port)         GATEWAY_PORT="$2"; shift 2;;
    *) shift;;
  esac
done

echo "Starting XCT Agent Gateway..."
echo "  Agents repo:  $REPO_ROOT"
echo "  LiteLLM:      $LITELLM_BASE"
echo "  Default model: $DEFAULT_MODEL"
echo "  Gateway port:  $GATEWAY_PORT"
echo "  Log:          $LOG_FILE"

cd "$REPO_ROOT"

AGENTS_REPO_PATH="$REPO_ROOT" \
LITELLM_API_BASE="$LITELLM_BASE" \
LITELLM_API_KEY="$LITELLM_KEY" \
DEFAULT_MODEL="$DEFAULT_MODEL" \
python3 -m uvicorn integrations.litellm.gateway.main:app \
  --host 0.0.0.0 \
  --port "$GATEWAY_PORT" \
  > "$LOG_FILE" 2>&1 &

GW_PID=$!
echo "$GW_PID" > "$PID_FILE"
echo "Gateway started (PID $GW_PID)"

# Wait and verify
sleep 3
if curl -s "http://localhost:$GATEWAY_PORT/health" > /dev/null 2>&1; then
  AGENT_COUNT=$(curl -s "http://localhost:$GATEWAY_PORT/health" | python3 -c "import json,sys; print(json.load(sys.stdin)['agents_loaded'])")
  echo "✅ Gateway healthy — $AGENT_COUNT agents loaded"
  echo ""
  echo "Test with:"
  echo "  curl -X POST http://localhost:4000/v1/chat/completions \\"
  echo "    -H 'Authorization: Bearer $LITELLM_KEY' \\"
  echo "    -H 'Content-Type: application/json' \\"
  echo "    -d '{\"model\": \"a2a/xct-frontend-developer\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
else
  echo "❌ Gateway failed to start. Check $LOG_FILE"
  exit 1
fi
