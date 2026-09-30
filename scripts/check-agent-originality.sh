#!/usr/bin/env bash
#
# check-agent-originality.sh — Flag agent files that substantially duplicate
# an existing agent (or another agent in the same change set).
#
# Why: a new agent should be genuinely new. Find-replace "re-skins" of an
# existing agent (e.g. swapping a country/platform name) are easy to miss in
# review because they're mergeable and well-formed — but they bloat the
# library with duplicates. This compares each candidate against the whole
# existing roster using entity-neutralized 8-word shingle overlap, so a
# swapped proper noun can't hide the copy.
#
# Usage:
#   ./scripts/check-agent-originality.sh [file ...]
#     With files: checks those agent .md files (used by CI on changed files).
#     With no args: checks every agent in the repo against every other (audit).
#
# Exit status:
#   0  all candidates below the FAIL threshold
#   1  at least one candidate at/above FAIL threshold (likely duplicate)
#
# Tunables (env):
#   ORIGINALITY_FAIL   default 40  — at/above this %, treated as a duplicate (exit 1)
#   ORIGINALITY_WARN   default 20  — at/above this %, surfaced as a warning (no fail)
#
# Calibration: across the existing agent library the worst same-pair
# similarity is ~1.5% (median 0%). Anything in the double digits is a strong
# anomaly; the defaults leave a wide safety margin against false positives.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR: python3 is required for the originality check." >&2
  exit 2
}

ORIGINALITY_FAIL="${ORIGINALITY_FAIL:-40}" \
ORIGINALITY_WARN="${ORIGINALITY_WARN:-20}" \
REPO_ROOT="$REPO_ROOT" \
python3 - "$@" <<'PYEOF'
import os, re, sys, glob, json

REPO_ROOT = os.environ["REPO_ROOT"]
FAIL = float(os.environ["ORIGINALITY_FAIL"])
WARN = float(os.environ["ORIGINALITY_WARN"])

# Division set — divisions.json (repo root) is the single source of truth, and
# scripts/check-divisions.sh (CI) enforces it against the directories on disk.
# Read it directly rather than hardcoding the list here so this check can never
# drift out of sync with the catalog the way a copied literal silently would.
with open(os.path.join(REPO_ROOT, "divisions.json")) as _fh:
    AGENT_DIRS = sorted(json.load(_fh)["divisions"].keys())

# Proper nouns we neutralize so a find-replace re-skin (swap the country/platform
# and little else) still scores as a near-duplicate. Extend as new markets appear.
ENTITY = re.compile(
    r'\b(vietnam|vietnamese|china|chinese|douyin|tiktok|korea|korean|japan|japanese|'
    r'india|indian|indonesia|indonesian|thailand|thai|philippines|filipino|brazil|'
    r'brazilian|mexico|mexican|wechat|weixin|weibo|xiaohongshu|rednote|kuaishou|'
    r'bilibili|zhihu|baidu|shopee|lazada|zalo|tokopedia|taobao|tmall|pinduoduo|'
    r'instagram|facebook|youtube|reels|shorts|linkedin|twitter|threads|snapchat)\b')

def strip_frontmatter(t):
    if t.startswith('---'):
        parts = t.split('---', 2)
        if len(parts) >= 3:
            return parts[2]
    return t

def tokens(text):
    text = ENTITY.sub(' ', strip_frontmatter(text).lower())
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return text.split()

def shingles(words, k=8):
    return set(' '.join(words[i:i+k]) for i in range(max(0, len(words) - k + 1)))

def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0

def is_agent(path):
    try:
        with open(path) as fh:
            return fh.readline().strip() == '---'
    except OSError:
        return False

def rel(p):
    try:
        return os.path.relpath(p, REPO_ROOT)
    except ValueError:
        return p

# --- Build the existing-library corpus -------------------------------------
corpus = {}
for d in AGENT_DIRS:
    for f in glob.glob(os.path.join(REPO_ROOT, d, '**', '*.md'), recursive=True):
        if is_agent(f):
            corpus[os.path.abspath(f)] = shingles(tokens(open(f).read()))

# --- Determine candidates ---------------------------------------------------
args = sys.argv[1:]
if args:
    candidates = []
    for a in args:
        p = a if os.path.isabs(a) else os.path.join(os.getcwd(), a)
        p = os.path.abspath(p)
        if not os.path.isfile(p):
            print(f"  skip (not found): {a}")
            continue
        if not is_agent(p):
            print(f"  skip (no frontmatter, not an agent): {rel(p)}")
            continue
        candidates.append(p)
else:
    candidates = list(corpus.keys())   # audit mode: everything vs everything

if not candidates:
    print("No agent files to check.")
    sys.exit(0)

cand_sh = {p: corpus.get(p) or shingles(tokens(open(p).read())) for p in candidates}
cand_set = set(candidates)

worst = 0.0
fails, warns = [], []

for p in candidates:
    sh = cand_sh[p]
    best_name, best_score = "", 0.0
    # vs existing library (exclude the candidate itself by path)
    for cf, csh in corpus.items():
        if cf == p:
            continue
        s = jaccard(sh, csh)
        if s > best_score:
            best_name, best_score = rel(cf), s
    # vs other candidates in this same change set
    for op in candidates:
        if op == p:
            continue
        s = jaccard(sh, cand_sh[op])
        if s > best_score:
            best_name, best_score = rel(op) + " (same change set)", s

    pct = best_score * 100
    worst = max(worst, pct)
    tag = "OK   "
    if pct >= FAIL:
        tag = "FAIL "; fails.append((rel(p), best_name, pct))
    elif pct >= WARN:
        tag = "WARN "; warns.append((rel(p), best_name, pct))
    print(f"  [{tag}] {pct:5.1f}%  {rel(p)}")
    if best_name:
        print(f"            closest: {best_name}")

print()
print(f"Thresholds: WARN >= {WARN:.0f}%, FAIL >= {FAIL:.0f}%  "
      f"(existing-library baseline max ~1.5%)")

if fails:
    print()
    print(f"FAILED: {len(fails)} agent(s) substantially duplicate existing content:")
    for name, match, pct in fails:
        print(f"  - {name}  ~{pct:.0f}% like  {match}")
    print()
    print("A new agent should be genuinely new. If this is intended market/platform")
    print("localization, make the body distinct (different platforms, tactics, examples)")
    print("rather than a find-replace of an existing agent.")
    sys.exit(1)

if warns:
    print(f"\n{len(warns)} warning(s) — review for overlap, but not blocking.")
print("\nPASSED")
sys.exit(0)
PYEOF
