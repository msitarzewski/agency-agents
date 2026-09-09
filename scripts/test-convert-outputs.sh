#!/usr/bin/env bash
#
# test-convert-outputs.sh — regression eval for the GENERATED product.
#
# Why: every converter bug so far passed lint and the existing tests while the
# product users actually install was broken. #778 shipped a double-wrapped
# description ('"..."') that parsed as valid YAML, so a wrapper check passed;
# #817 dropped a whole tool from --parallel and every remaining tool still
# looked fine. Both are invariant violations, not syntax errors. This script
# encodes what "correct output" means and checks all of it, for every agent,
# for every converted tool.
#
# Layer A — invariants (need no history):
#   round-trip   parsed(generated).description == source description
#   strict-parse every generated frontmatter/TOML/YAML parses with a real parser
#   count        every tool emits exactly one output per roster agent
#   source       every SOURCE agent's frontmatter strict-parses (the desktop app
#                reads sources with js-yaml — #473 was exactly this) and its
#                description carries no leaked quote character
#
# Layer B — drift (needs the committed manifest):
#   scripts/convert-outputs.sha256 (v2) holds
#     agent  <slug>  <hash>   one line per roster agent: that agent's generated output
#                             across every tool (its files, its section of the
#                             accumulated aider/windsurf files, its hermes JSON entry)
#     tool   <tool>  <hash>   the tool's NON-agent files (README, plugin code, manifests):
#                             moves only when a generator/template changes
#     contract <file> <hash>  divisions.json, tools.json, runbooks.json
#   Adding or editing one agent flips exactly its own line, so two agent PRs
#   never collide on this file. Hashes are platform-neutral: forward-slash paths
#   and LF line endings, so a Windows checkout produces the same manifest.
#
#   Contributors adding/editing agents do NOT need to touch the manifest: CI runs
#   this with --drift=advisory on pull requests (drift is printed, not failed) and
#   maintainers regenerate it when the PR lands. A generator change should ship
#   with --update so the tool line moves in the same commit.
#
# Usage:
#   ./scripts/test-convert-outputs.sh                   # generate into a temp dir, check everything
#   ./scripts/test-convert-outputs.sh --update          # ...and rewrite the manifest
#   ./scripts/test-convert-outputs.sh --drift=advisory  # drift is reported but does not fail (CI on PRs)
#   ./scripts/test-convert-outputs.sh --out=DIR         # check an already-generated DIR (no generation)
#
# Exit 0 only when every invariant passes AND the manifest matches (or --update,
# or --drift=advisory).
# Runs on bash 3.2 (macOS) and 5 (Linux); parsing is done by python3.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$REPO_ROOT/scripts/convert-outputs.sha256"

UPDATE=false; DIFF=false; OUT=""; DRIFT=strict
for a in "$@"; do
  case "$a" in
    --update) UPDATE=true ;;
    --diff)   DIFF=true ;;
    --drift=advisory) DRIFT=advisory ;;
    --drift=strict)   DRIFT=strict ;;
    --out=*)  OUT="${a#--out=}" ;;
    -h|--help) sed -n '2,44p' "$0"; exit 0 ;;
    *) printf 'unknown flag: %s\n' "$a" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required." >&2; exit 2; }
python3 -c 'import yaml, tomllib' 2>/dev/null \
  || { echo "ERROR: python3 needs PyYAML and tomllib (3.11+)." >&2; exit 2; }

# get_field (quote-aware) and agent_slug — the same helpers convert.sh uses,
# so the "expected" side is derived exactly the way the generator derives it.
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-outputs.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# --- roster: every agent file under a registered division --------------------
divisions_from_json() {
  awk '/"divisions"[[:space:]]*:[[:space:]]*\{/{f=1; next} f' "$REPO_ROOT/divisions.json" \
    | grep -oE '^[[:space:]]*"[a-z0-9-]+"[[:space:]]*:' \
    | sed -E 's/[[:space:]]*"([a-z0-9-]+)"[[:space:]]*:/\1/'
}

SOURCES="$TMP/sources.tsv"; : > "$SOURCES"
while IFS= read -r div; do
  [[ -n "$div" && -d "$REPO_ROOT/$div" ]] || continue
  while IFS= read -r f; do
    [[ "$(head -1 "$f")" == "---" ]] || continue
    printf '%s\t%s\t%s\t%s\n' \
      "$(agent_slug "$f")" "$(get_field description "$f")" "$(get_field name "$f")" "${f#"$REPO_ROOT"/}" \
      >> "$SOURCES"
  done < <(find "$REPO_ROOT/$div" -name '*.md' -type f | sort)
done < <(divisions_from_json)
N="$(wc -l < "$SOURCES" | tr -d ' ')"
[[ "$N" -gt 0 ]] || { echo "ERROR: no source agents found." >&2; exit 2; }

# --- generate: every converted tool, sequentially, into a scratch dir ---------
TOOLS="antigravity gemini-cli opencode cursor aider windsurf openclaw qwen zcode kimi codex osaurus hermes vibe"
if [[ -z "$OUT" ]]; then
  OUT="$TMP/out"; mkdir -p "$OUT"
  for t in $TOOLS; do
    "$SCRIPT_DIR/convert.sh" --tool "$t" --out "$OUT" >/dev/null 2>&1 \
      || { echo "ERROR: convert.sh --tool $t failed." >&2; exit 1; }
  done
fi

# --- check: invariants + manifest (python does the parsing) -------------------
REPO_ROOT="$REPO_ROOT" OUT="$OUT" SOURCES="$SOURCES" N="$N" MANIFEST="$MANIFEST" \
UPDATE="$UPDATE" DIFF="$DIFF" DRIFT="$DRIFT" TOOLS="$TOOLS" python3 - <<'PY'
import os, re, sys, glob, json, hashlib, yaml, tomllib

R, OUT, N = os.environ["REPO_ROOT"], os.environ["OUT"], int(os.environ["N"])
MANIFEST, UPDATE, DIFF = os.environ["MANIFEST"], os.environ["UPDATE"] == "true", os.environ["DIFF"] == "true"
ADVISORY = os.environ.get("DRIFT") == "advisory"
TOOLS = os.environ["TOOLS"].split()

# slug -> (description, name, source path)
src = {}
for line in open(os.environ["SOURCES"], encoding="utf-8"):
    slug, desc, name, path = line.rstrip("\n").split("\t", 3)
    src[slug] = (desc, name, path)

fails, passes = [], 0
def ok(msg):   global passes; passes += 1
def bad(msg):  fails.append(msg)
def check(cond, msg): (ok if cond else bad)(msg)

# Per-tool output spec: (glob under OUT/<tool>, format). Formats were read off
# real generated output, not assumed:
#   yaml-fm   markdown with --- YAML frontmatter    round-trip description
#   toml      TOML with a description key           round-trip description
#   toml-id   TOML carrying only an identifier      id == slug + companion prompt file
#             (vibe: system_prompt_id -> prompts/<slug>.md)
#   yaml-id   YAML carrying only an identifier      id == slug + companion file
#             (kimi: agent.name -> <slug>/system.md)
#   accum     one file for all agents: "## Name" then the description line
#             (windsurf: bare line; aider: "> " blockquote)  round-trip both
#   plain     no structured metadata                count only
#   json      hermes agents.json                    count
SPEC = {
    "antigravity": ("agency-*/SKILL.md", "yaml-fm"),
    "osaurus":     ("agency-*/SKILL.md", "yaml-fm"),
    "gemini-cli":  ("agents/*.md",       "yaml-fm"),
    "opencode":    ("agents/*.md",       "yaml-fm"),
    "qwen":        ("agents/*.md",       "yaml-fm"),
    "zcode":       ("agents/*.md",       "yaml-fm"),
    "cursor":      ("rules/*.mdc",       "yaml-fm"),
    "codex":       ("agents/*.toml",     "toml"),
    "vibe":        ("agents/*.toml",     "toml-id"),
    "kimi":        ("*/agent.yaml",      "yaml-id"),
    "openclaw":    ("*/SOUL.md",         "plain"),
    "aider":       ("CONVENTIONS.md",    "accum"),
    "windsurf":    (".windsurfrules",    "accum"),
    "hermes":      ("agency-agents-router/data/agents.json", "json"),
}

def slug_of(path):
    base = os.path.basename(path)
    if base in ("SKILL.md", "agent.yaml", "SOUL.md", "system.md", "AGENTS.md", "IDENTITY.md"):
        d = os.path.basename(os.path.dirname(path))
        return d[len("agency-"):] if d.startswith("agency-") else d
    return os.path.splitext(base)[0]

def find_desc(obj):
    """First 'description' string anywhere in a parsed mapping (TOML/YAML nest freely)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("description"), str): return obj["description"]
        for v in obj.values():
            r = find_desc(v)
            if r is not None: return r
    return None

def frontmatter(text):
    if not text.startswith("---"): raise ValueError("no frontmatter")
    parts = text.split("\n---", 1)
    return yaml.safe_load(parts[0][3:])

def parsed_desc(path, fmt):
    text = open(path, encoding="utf-8").read()
    if fmt == "yaml-fm": data = frontmatter(text)
    elif fmt == "toml":  data = tomllib.loads(text)
    elif fmt == "yaml":  data = yaml.safe_load(text)
    else: return None
    if not isinstance(data, dict): raise ValueError("top level is not a mapping")
    return find_desc(data)

# --- expected values: an INDEPENDENT strict parse of every source ---------------
# The generator reads sources through lib.sh's get_field. If the expected side
# were derived the same way, a get_field bug would move both sides together and
# hide itself — that is exactly how #778's double-wrap stayed invisible. So the
# expected name/description come from PyYAML parsing the source frontmatter
# (the desktop app's js-yaml contract), and get_field's values are discarded.
# A source that does not strict-parse is an app-contract failure in itself; it
# is reported below and excluded from round-trips (desc=None).
src_bad = []
for slug, (_gf_desc, _gf_name, path) in list(src.items()):
    try:
        data = frontmatter(open(os.path.join(R, path), encoding="utf-8").read())
        assert isinstance(data, dict) and isinstance(data.get("name"), str) \
            and isinstance(data.get("description"), str), "missing name/description"
        assert data["description"][:1] not in ('"', "'"), "description starts with a quote character"
        src[slug] = (data["description"], data["name"], path)
    except Exception as e:
        src_bad.append(f"source {path}: {str(e).splitlines()[0]}")
        src[slug] = (None, _gf_name, path)

# --- Layer A: per-tool count + strict-parse + round-trip -----------------------
def report(tool, bad_parse, bad_trip, label):
    if bad_trip > 3: bad(f"{tool}: ...and {bad_trip-3} more mismatches")
    if not bad_parse and not bad_trip: ok(f"{tool}: all {N} {label}")

for tool in TOOLS:
    pat, fmt = SPEC[tool]
    files = sorted(glob.glob(os.path.join(OUT, tool, pat)))

    if fmt == "accum":
        # One file for every agent. For each roster agent: "## <name>" exactly
        # once, and the description on the next non-blank line (aider quotes it
        # with "> "). Counting "## " lines would count body sections too.
        text = open(files[0], encoding="utf-8").read().split("\n") if files else []
        miss = 0
        for slug, (desc, name, path) in src.items():
            if desc is None: continue   # source failed strict parse; reported below
            idx = [i for i, l in enumerate(text) if l.rstrip() == f"## {name}"]
            if len(idx) != 1:
                miss += 1
                if miss <= 3: bad(f"{tool}: '## {name}' appears {len(idx)}x (want exactly 1)")
                continue
            nxt = next((l for l in text[idx[0]+1:idx[0]+4] if l.strip()), "")
            got = (nxt[2:] if nxt.startswith("> ") else nxt).strip()
            if got != desc:
                miss += 1
                if miss <= 3:
                    bad(f"{tool}: {slug} description mismatch\n"
                        f"        source:    {desc[:70]!r}\n        generated: {got[:70]!r}")
        report(tool, 0, miss, "present with descriptions round-tripped")
        continue

    if fmt == "json":
        try:
            data = json.load(open(files[0], encoding="utf-8")) if files else []
            items = data if isinstance(data, list) else data.get("agents", [])
            check(len(items) == N, f"{tool}: agents.json lists {len(items)} agents, roster has {N}")
        except Exception as e:
            bad(f"{tool}: agents.json unreadable ({e})")
        continue

    check(len(files) == N, f"{tool}: {len(files)} outputs, roster has {N}")
    if fmt == "plain": continue

    bad_parse = bad_trip = 0
    for f in files:
        slug = slug_of(f)
        if slug not in src:
            bad(f"{tool}: {os.path.relpath(f, OUT)} has no roster source for slug '{slug}'"); continue
        try:
            text = open(f, encoding="utf-8").read()
            if fmt == "yaml-fm":               data = frontmatter(text)
            elif fmt in ("toml", "toml-id"):   data = tomllib.loads(text)
            else:                              data = yaml.safe_load(text)   # yaml-id
            if not isinstance(data, dict): raise ValueError("top level is not a mapping")
        except Exception as e:
            bad_parse += 1; bad(f"{tool}: {os.path.relpath(f, OUT)} does not parse ({type(e).__name__}: {e})"); continue

        if fmt in ("yaml-fm", "toml"):
            got, want = find_desc(data), src[slug][0]
            if want is None: continue   # source failed strict parse; reported below
            if got != want:
                bad_trip += 1
                if bad_trip <= 3:
                    bad(f"{tool}: {slug} description round-trip mismatch\n"
                        f"        source:    {want[:70]!r}\n        generated: {str(got)[:70]!r}")
        else:
            # Identifier formats carry no description; the id must be the slug
            # and the prose file it points at must exist.
            if fmt == "toml-id":
                ident, companion = data.get("system_prompt_id"), os.path.join(OUT, tool, "prompts", f"{slug}.md")
            else:
                ident, companion = (data.get("agent") or {}).get("name"), os.path.join(os.path.dirname(f), "system.md")
            if ident != slug:
                bad_trip += 1
                if bad_trip <= 3: bad(f"{tool}: {os.path.relpath(f, OUT)} identifier {ident!r} != slug {slug!r}")
            elif not os.path.isfile(companion):
                bad_trip += 1
                if bad_trip <= 3: bad(f"{tool}: {slug} companion file missing: {os.path.relpath(companion, OUT)}")
    report(tool, bad_parse, bad_trip,
           "parse and round-trip" if fmt in ("yaml-fm", "toml") else "parse, carry their slug, and have their prose file")

# --- Layer A (app-facing): every SOURCE frontmatter strict-parsed above -------
for m in src_bad[:5]: bad(m)
if len(src_bad) > 5: bad(f"...and {len(src_bad)-5} more source frontmatter problems")
if not src_bad: ok(f"all {N} source agents strict-parse (app contract)")

# --- Layer B: manifest (v2: per-agent lines, platform-neutral hashes) ----------
def norm_bytes(b): return b.replace(b"\r\n", b"\n")
def sha(b): return hashlib.sha256(b).hexdigest()
def rel(f): return os.path.relpath(f, OUT).replace(os.sep, "/")

slugs = set(src)
names = {name: slug for slug, (_d, name, _p) in src.items()}
per_agent = {slug: [] for slug in slugs}     # slug -> [(label, bytes)]
per_tool  = {t: [] for t in TOOLS}           # tool -> [(label, bytes)] for non-agent files

def owner_of(path):
    """Which roster agent a generated file belongs to, by exact path component or stem."""
    parts = rel(path).split("/")[1:]         # drop the tool dir
    for comp in parts[:-1]:
        d = comp[len("agency-"):] if comp.startswith("agency-") else comp
        if d in slugs: return d
    stem = os.path.splitext(parts[-1])[0]
    return stem if stem in slugs else None

for tool in TOOLS:
    pat, fmt = SPEC[tool]
    for f in sorted(glob.glob(os.path.join(OUT, tool, "**", "*"), recursive=True)):
        if not os.path.isfile(f): continue
        data = norm_bytes(open(f, "rb").read())
        if fmt == "accum" and rel(f) == f"{tool}/{pat}":
            # One file for all agents: attribute each "## <name>" section to its agent;
            # anything outside a known section (preamble) is the tool's contract.
            lines_ = data.decode("utf-8", "replace").split("\n")
            cur, buf, pre = None, [], []
            def flush():
                if cur: per_agent[cur].append((f"{tool}:section", "\n".join(buf).encode()))
            for l in lines_:
                m = names.get(l.rstrip()[3:]) if l.startswith("## ") else None
                if m: flush(); cur, buf = m, [l]; continue
                (buf if cur else pre).append(l)
            flush()
            per_tool[tool].append((rel(f) + ":preamble", "\n".join(pre).encode()))
            continue
        if fmt == "json" and rel(f) == f"{tool}/{pat}":
            try:
                items = json.loads(data.decode("utf-8"))
                items = items if isinstance(items, list) else items.get("agents", [])
                for it in items:
                    sl = it.get("slug") if isinstance(it, dict) else None
                    if sl in slugs: per_agent[sl].append((f"{tool}:entry", json.dumps(it, sort_keys=True, ensure_ascii=False).encode()))
                    else: per_tool[tool].append((rel(f) + ":stray-entry", json.dumps(it, sort_keys=True, ensure_ascii=False).encode()))
            except Exception:
                per_tool[tool].append((rel(f), data))
            continue
        o = owner_of(f)
        if o is None and os.path.basename(f).lower() == "readme.md":
            # Roster-derived text in generated docs ("Generated agent count: 273") must not move
            # the tool line — only template changes should.
            data = re.sub(rb"(?m)^(Generated agent count: )\d+$", rb"\1N", data)
        (per_agent[o] if o else per_tool[tool]).append((rel(f), data))

def digest(entries):
    h = hashlib.sha256()
    for label, b in sorted(entries, key=lambda e: e[0]):
        h.update(label.encode()); h.update(b"\0"); h.update(sha(b).encode()); h.update(b"\n")
    return h.hexdigest()

rows = [("agent", slug, digest(per_agent[slug])) for slug in sorted(slugs)]
rows += [("tool", t, digest(per_tool[t])) for t in TOOLS]
for c in ("divisions.json", "tools.json", "strategy/runbooks.json"):
    p = os.path.join(R, c)
    rows.append(("contract", c, sha(norm_bytes(open(p, "rb").read())) if os.path.exists(p) else "MISSING"))
new = ("# convert-outputs manifest v2 — one line per agent (its output across every tool), one per tool\n"
       "# (non-agent files), one per contract. Platform-neutral hashes. Regenerate: scripts/test-convert-outputs.sh --update\n"
       + "".join(f"{k}\t{key}\t{h}\n" for k, key, h in rows))

def drift_report(old_text):
    old = {}
    for l in old_text.splitlines():
        if l.startswith("#") or "\t" not in l: continue
        f = l.split("\t")
        if len(f) == 3: old[(f[0], f[1])] = f[2]
        elif len(f) == 2: return None                    # v1 manifest
    cur = {(k, key): h for k, key, h in rows}
    changed = sorted(key for (k, key), h in cur.items() if (k, key) in old and old[(k, key)] != h and k == "agent")
    added   = sorted(key for (k, key) in cur if k == "agent" and (k, key) not in old)
    removed = sorted(key for (k, key) in old if k == "agent" and (k, key) not in cur)
    tools   = sorted(key for (k, key), h in cur.items() if k != "agent" and old.get((k, key)) != h)
    return changed, added, removed, tools

if UPDATE:
    open(MANIFEST, "w", newline="\n").write(new); ok(f"manifest written: {os.path.relpath(MANIFEST, R)}")
elif not os.path.exists(MANIFEST):
    bad(f"manifest missing: run with --update to create {os.path.relpath(MANIFEST, R)}")
else:
    d = drift_report(open(MANIFEST, encoding="utf-8").read())
    if d is None:
        bad("manifest is the old v1 format (per-tool aggregate hashes) — run --update once to migrate")
    else:
        changed, added, removed, tools = d
        if not (changed or added or removed or tools):
            ok("manifest matches (no output or contract drift)")
        else:
            def few(xs, n=8): return ", ".join(xs[:n]) + (f", … ({len(xs)} total)" if len(xs) > n else "")
            parts = []
            if added:   parts.append(f"new agents: {few(added)}")
            if changed: parts.append(f"changed agents: {few(changed)}")
            if removed: parts.append(f"removed agents: {few(removed)}")
            if tools:   parts.append(f"tool/contract lines: {', '.join(tools)}")
            msg = "manifest drift — " + "; ".join(parts)
            if len(changed) >= max(20, N // 4):
                msg += f"\n        {len(changed)} of {N} agents changed at once — that is a converter/template change, not an agent edit; review the generator diff"

            if ADVISORY:
                print(f"  ADVISORY {msg}\n           (expected for agent additions/edits; maintainers regenerate the manifest when this lands)")
                ok("manifest drift reported (advisory mode)")
            else:
                bad(msg + "\n        Agent lines move when agents are added/edited — regenerate with --update when landing."
                          "\n        A tool/contract line moving means a generator or contract changed — review it.")

# --- report --------------------------------------------------------------------
for m in fails: print(f"  FAIL {m}")
print(f"\nResults: {passes} passed, {len(fails)} failed  ({N} roster agents x {len(TOOLS)} tools)")
print("FAILED" if fails else "PASSED")
sys.exit(1 if fails else 0)
PY
