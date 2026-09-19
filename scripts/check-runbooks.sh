#!/usr/bin/env bash
#
# check-runbooks.sh — enforce that strategy/runbooks.json stays in sync with the
# real agent roster.
#
# strategy/runbooks.json is the machine-readable roster for the NEXUS scenario
# runbooks: the Agency Agents app reads it to turn a runbook into a one-click
# team deploy, mapping each roster slug to a catalog agent. If a slug there
# doesn't resolve to a real agent file, the app can't deploy that team — so this
# check fails the build when:
#   1. runbooks.json is not valid JSON, or an entry is missing a required field
#   2. any roster `agents[]` slug does not match an agent .md filename stem
#   3. any `doc` path does not exist
#   4. a runbook `slug` is duplicated
#
# Slugs are the agent .md filename stem (the corpus id), e.g.
# engineering/engineering-frontend-developer.md -> "engineering-frontend-developer".
# Uses python3 (already required by check-agent-originality.sh) for JSON; no jq,
# so it runs the same on macOS and CI. Mirrors scripts/check-divisions.sh.
#
# Usage: ./scripts/check-runbooks.sh

set -euo pipefail
cd "$(dirname "$0")/.."

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR: python3 is required for the runbooks check." >&2
  exit 2
}

python3 - <<'PYEOF'
import json, os, subprocess, sys

JSON = "strategy/runbooks.json"
errors = []

if not os.path.isfile(JSON):
    print(f"ERROR {JSON} not found"); sys.exit(1)

try:
    data = json.load(open(JSON))
except json.JSONDecodeError as e:
    print(f"ERROR {JSON} is not valid JSON: {e}"); sys.exit(1)

# Real slugs = filename stems of tracked agent .md files under division dirs.
NON_DIVISION = {"integrations", "examples", "strategy", "scripts", ".github"}
tracked = subprocess.check_output(["git", "ls-files", "*/*.md"]).decode().splitlines()
real = {os.path.basename(p)[:-3] for p in tracked if p.split("/")[0] not in NON_DIVISION}

runbooks = data.get("runbooks")
if not isinstance(runbooks, list) or not runbooks:
    print(f"ERROR {JSON} has no 'runbooks' array"); sys.exit(1)

seen_slugs = set()
total_refs = 0
for rb in runbooks:
    rid = rb.get("slug", "<no slug>")
    for field in ("slug", "title", "mode", "doc", "roster"):
        if field not in rb:
            errors.append(f"runbook '{rid}' is missing required field \"{field}\"")
    if rb.get("slug") in seen_slugs:
        errors.append(f"duplicate runbook slug '{rb.get('slug')}'")
    seen_slugs.add(rb.get("slug"))
    doc = rb.get("doc")
    if doc and not os.path.isfile(doc):
        errors.append(f"runbook '{rid}': doc path does not exist: {doc}")
    for g in rb.get("roster", []):
        for slug in g.get("agents", []):
            total_refs += 1
            if slug not in real:
                errors.append(f"runbook '{rid}' / group '{g.get('group','?')}': "
                              f"slug '{slug}' does not match any agent .md filename stem")

if errors:
    print(f"FAILED: {len(errors)} runbook consistency error(s). "
          f"strategy/runbooks.json must reference real agent slugs.\n")
    for e in errors:
        print(f"  ERROR {e}")
    sys.exit(1)

print(f"PASSED: {len(runbooks)} runbooks, {total_refs} agent slug references — "
      f"all resolve to real agent files.")
PYEOF
