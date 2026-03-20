#!/usr/bin/env bash
# Fork msitarzewski/agency-agents to your GitHub user, point origin at the fork, push current branch.
# Requires: git, GitHub CLI (gh), authenticated via `gh auth login`
#
# Usage:
#   ./scripts/setup-my-fork-and-push.sh
#   USE_SSH=1 ./scripts/setup-my-fork-and-push.sh

set -euo pipefail

UPSTREAM_OWNER="${UPSTREAM_OWNER:-msitarzewski}"
UPSTREAM_REPO="${UPSTREAM_REPO:-agency-agents}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Error: run this from inside the agency-agents git repo." >&2
  exit 1
}
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh (GitHub CLI) not found. Install: https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: not logged in. Run: gh auth login" >&2
  exit 1
fi

echo "==> Fork ${UPSTREAM_OWNER}/${UPSTREAM_REPO} on GitHub (no new clone)"
gh repo fork "${UPSTREAM_OWNER}/${UPSTREAM_REPO}" --clone=false

LOGIN="$(gh api user -q .login)"
if [[ -z "$LOGIN" ]]; then
  echo "Error: could not read GitHub login from gh api user" >&2
  exit 1
fi

if [[ "${USE_SSH:-0}" == "1" ]]; then
  ORIGIN_URL="git@github.com:${LOGIN}/${UPSTREAM_REPO}.git"
else
  ORIGIN_URL="https://github.com/${LOGIN}/${UPSTREAM_REPO}.git"
fi

UPSTREAM_URL="https://github.com/${UPSTREAM_OWNER}/${UPSTREAM_REPO}.git"

echo "==> git remote set-url origin ${ORIGIN_URL}"
git remote set-url origin "$ORIGIN_URL"

if git remote get-url upstream >/dev/null 2>&1; then
  echo "==> remote upstream already exists; leaving it unchanged"
else
  echo "==> git remote add upstream ${UPSTREAM_URL}"
  git remote add upstream "$UPSTREAM_URL"
fi

BRANCH="$(git branch --show-current)"
if [[ -z "$BRANCH" ]]; then
  echo "Error: detached HEAD; checkout a branch first." >&2
  exit 1
fi

echo "==> git push -u origin ${BRANCH}"
git push -u origin "$BRANCH"

echo ""
echo "Done. Remotes:"
git remote -v
