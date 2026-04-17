#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REQUIRED_FILES=(
  strategy/QUICKSTART.md
  strategy/EXECUTIVE-BRIEF.md
  strategy/nexus-strategy.md
  strategy/coordination/agent-activation-prompts.md
  strategy/coordination/handoff-templates.md
  strategy/playbooks/phase-0-discovery.md
  strategy/playbooks/phase-1-strategy.md
  strategy/playbooks/phase-2-foundation.md
  strategy/playbooks/phase-3-build.md
  strategy/playbooks/phase-4-hardening.md
  strategy/playbooks/phase-5-launch.md
  strategy/playbooks/phase-6-operate.md
  strategy/runbooks/scenario-startup-mvp.md
  strategy/runbooks/scenario-enterprise-feature.md
  strategy/runbooks/scenario-marketing-campaign.md
  strategy/runbooks/scenario-incident-response.md
)

errors=0

err() {
  echo "ERROR $*" >&2
  errors=$((errors + 1))
}

for file in "${REQUIRED_FILES[@]}"; do
  [[ -f "$file" ]] || err "missing required strategy file: $file"
done

while IFS= read -r -d '' file; do
  [[ -s "$file" ]] || err "$file: empty file"
  first_nonempty="$(grep -m 1 -E '\S' "$file" || true)"
  [[ "$first_nonempty" == \#* ]] || err "$file: first non-empty line must be a markdown heading"
done < <(find strategy -name '*.md' -type f -print0 | sort -z)

python3 - <<'PY2'
from pathlib import Path
import re
import sys

root = Path('.').resolve()
strategy_files = sorted(Path('strategy').rglob('*.md'))
link_re = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
code_path_re = re.compile(r'`(strategy/[^`]+\.md(?:#[^`]+)?)`')
errors = []

for path in strategy_files:
    text = path.read_text(encoding='utf-8')
    for match in link_re.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        target = target.split()[0]
        target_no_anchor = target.split('#', 1)[0]
        resolved = (path.parent / target_no_anchor).resolve()
        if not resolved.exists():
            errors.append(f"{path}: broken markdown link -> {target}")
    for match in code_path_re.finditer(text):
        target = match.group(1)
        if '[' in target or '*' in target:
            continue
        target_no_anchor = target.split('#', 1)[0]
        resolved = (root / target_no_anchor).resolve()
        if not resolved.exists():
            errors.append(f"{path}: broken strategy path reference -> {target}")

if errors:
    for item in errors:
        print(f"ERROR {item}", file=sys.stderr)
    sys.exit(1)
PY2

if [[ "$errors" -gt 0 ]]; then
  echo "FAILED: strategy lint found ${errors} error(s)." >&2
  exit 1
fi

echo "Strategy lint: PASS (${#REQUIRED_FILES[@]} required files + link/path checks)"
