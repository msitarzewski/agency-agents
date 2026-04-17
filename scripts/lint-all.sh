#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/lint-agents.sh
./scripts/lint-strategy.sh
./scripts/lint-integrations.sh

echo "All lint suites passed."
