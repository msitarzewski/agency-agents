#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

test -f docs/local-nexus-sprint-template.md || fail "missing docs/local-nexus-sprint-template.md"

rg -n "strategy/QUICKSTART\.md|strategy/nexus-strategy\.md|agent-activation-prompts\.md|handoff-templates\.md|specialized/agents-orchestrator\.md|testing/testing-evidence-collector\.md|testing/testing-reality-checker\.md" docs/local-nexus-sprint-template.md >/tmp/nexus_template_refs.out 2>/tmp/nexus_template_refs.err \
  || fail "template does not reference required repo assets"

rg -n "local-nexus-sprint-template\.md" docs/full-utilization-guide.md >/tmp/nexus_template_guide.out 2>/tmp/nexus_template_guide.err \
  || fail "full-utilization guide does not link the new template"

rg -n "local-nexus-sprint-template\.md" README.md >/tmp/nexus_template_readme.out 2>/tmp/nexus_template_readme.err \
  || fail "README does not reference the new template"

echo "PASS: local nexus sprint template"
