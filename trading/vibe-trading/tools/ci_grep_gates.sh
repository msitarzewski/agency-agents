#!/usr/bin/env bash
# ci_grep_gates.sh — repo-wide safety floor enforced in CI.
#
# Three gates run sequentially; any failure exits non-zero and names the
# offending files. Run locally before pushing:
#
#     bash tools/ci_grep_gates.sh
#
# CONTRIBUTING.md references this script as the source of truth for the
# pre-commit / CI safety checks (do NOT inline these patterns elsewhere —
# update this file and let CI fan it out).
#
# Gates:
#   (a) No `yaml.load(` calls that bypass `safe_load` (RCE risk).
#   (b) No literal "WorldQuant" anywhere (trademark; spec.md §License).
#   (c) No per-stock-code data leaking into the wiki/alpha-library tree
#       (spec.md §"Vendor 数据 ToS").
#
# Exclusions: .git, node_modules, __pycache__, .venv, dist, build, this
# script itself. The HTML scan in (c) is scoped to wiki/alpha-library/**
# because hero banners in wiki/home/*.html legitimately mention a single
# example ticker — the gate exists to catch *bulk* data dumps, not prose.

set -u
set -o pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
NC=$'\033[0m'

FAILED=0
SELF="tools/ci_grep_gates.sh"
EXCLUDE_DIRS=(--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build --exclude-dir=.pytest_cache --exclude-dir=.ruff_cache)

# -------------------------------------------------------------- gate (a)
echo "[gate a] no unsafe yaml.load() ..."
A_HITS=$(grep -rn --include='*.py' "${EXCLUDE_DIRS[@]}" 'yaml\.load(' . 2>/dev/null \
    | grep -v 'safe_load' \
    | grep -v "$SELF" \
    || true)
if [ -n "$A_HITS" ]; then
    echo "${RED}FAIL${NC}: yaml.load() without safe_load:"
    echo "$A_HITS"
    FAILED=1
else
    echo "${GREEN}ok${NC}"
fi

# -------------------------------------------------------------- gate (b)
# docs/ is excluded: those are internal planning docs that discuss the
# trademark policy itself (e.g. "the string 'WorldQuant' must not appear in
# user-facing artifacts"). docs/ is not shipped to PyPI / public consumers
# (memory: feedback_no_push_docs). The gate's real target is source code,
# READMEs, HTML/JSON manifests, and the wiki.
echo "[gate b] no 'WorldQuant' trademark string in shipped artifacts ..."
B_HITS=$(grep -rni --include='*.py' --include='*.md' --include='*.html' --include='*.json' \
    "${EXCLUDE_DIRS[@]}" --exclude-dir=docs 'worldquant' . 2>/dev/null \
    | grep -v "$SELF" \
    || true)
if [ -n "$B_HITS" ]; then
    echo "${RED}FAIL${NC}: literal 'WorldQuant' found (use 'Kakushadze 101 Formulaic Alphas'):"
    echo "$B_HITS"
    FAILED=1
else
    echo "${GREEN}ok${NC}"
fi

# -------------------------------------------------------------- gate (c)
echo "[gate c] no per-stock-code data in wiki/alpha-library ..."
if [ -d "wiki" ]; then
    # CN A-share style: 6 digits + .SH/.SZ/.BJ — scan json/csv anywhere in wiki/,
    # html only inside wiki/alpha-library (marketing pages elsewhere may show
    # one example ticker in prose).
    C_HITS_JSON_CSV=$(grep -rEn --include='*.json' --include='*.csv' \
        "${EXCLUDE_DIRS[@]}" '[0-9]{6}\.(SH|SZ|BJ)|[A-Z]{1,5}\.US' wiki/ 2>/dev/null || true)
    C_HITS_HTML=""
    if [ -d "wiki/alpha-library" ]; then
        C_HITS_HTML=$(grep -rEn --include='*.html' \
            "${EXCLUDE_DIRS[@]}" '[0-9]{6}\.(SH|SZ|BJ)|[A-Z]{1,5}\.US' wiki/alpha-library/ 2>/dev/null || true)
    fi
    C_HITS="$C_HITS_JSON_CSV"
    if [ -n "$C_HITS_HTML" ]; then
        C_HITS="${C_HITS}${C_HITS:+$'\n'}${C_HITS_HTML}"
    fi
    if [ -n "$C_HITS" ]; then
        echo "${RED}FAIL${NC}: per-stock-code data found in wiki/ (spec.md §Vendor 数据 ToS):"
        echo "$C_HITS"
        FAILED=1
    else
        echo "${GREEN}ok${NC}"
    fi
else
    echo "${YELLOW}skip${NC}: no wiki/ directory"
fi

# --------------------------------------------------------------- result
if [ "$FAILED" -ne 0 ]; then
    echo
    echo "${RED}ci_grep_gates: one or more gates failed${NC}"
    exit 1
fi

echo
echo "${GREEN}ci_grep_gates: all gates passed${NC}"
exit 0
