#!/usr/bin/env bash
#
# check-hermes-config-rewrite.sh — regression test for the
# ensure_hermes_plugin_enabled() heredoc in scripts/install.sh.
#
# Reproduces and guards against the indent bug: the previous heredoc hardcoded
# a 2-space indent when inserting into plugins.enabled, which broke any
# config that used a different list-item indent (Hermes' default is 4 spaces).
# Symptom: plugins.enabled collapses onto one line as a plain scalar string
# when re-parsed, and the script's idempotency check fails to detect that
# the plugin is already there.
#
# Usage: ./scripts/check-hermes-config-rewrite.sh
# Exits non-zero on any failure. Mirrors scripts/check-X.sh style.

set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/check-hermes-config-rewrite.py