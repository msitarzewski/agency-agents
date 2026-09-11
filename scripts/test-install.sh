#!/usr/bin/env bash
#
# test-install.sh — regression tests for scripts/install.sh.
#
# install.sh is the largest script in the repo and every install bug so far has
# been a silent one: agents land in the wrong directory, a path with a space is
# split into two, a filter installs everything. These tests pin the observable
# contract — where files land and how many — so those regressions fail loudly.
#
# Design constraints (same as the rest of scripts/):
#   * bash 3.2 + BSD userland, no jq, no GNU-only flags.
#   * Never touches the real $HOME. Every case runs with HOME set to a fresh
#     sandbox, so a broken default path writes into the sandbox, not your config.
#   * Only exercises the two source tools (claude-code, copilot) so no case
#     depends on convert.sh output being present or fresh.
#
# Usage: ./scripts/test-install.sh [-v]
#   -v  echo the installer's own output for failing cases

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL="$SCRIPT_DIR/install.sh"
# shellcheck source=scripts/lib.sh
. "$SCRIPT_DIR/lib.sh"

VERBOSE=false
[[ "${1:-}" == "-v" ]] && VERBOSE=true

passed=0
failed=0
xfailed=0
SANDBOX_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agency-install-tests.XXXXXX")"
trap 'rm -rf "$SANDBOX_ROOT"' EXIT

pass() { printf '  ok   %s\n' "$1"; passed=$((passed + 1)); }
fail() {
  printf '  FAIL %s\n' "$1"
  [[ -n "${2:-}" ]] && printf '       %s\n' "$2"
  failed=$((failed + 1))
}

# assert_eq <expected> <actual> <label>
assert_eq() {
  if [[ "$1" == "$2" ]]; then pass "$3"; else fail "$3" "expected '$1', got '$2'"; fi
}

# xfail_eq <expected> <actual> <label> <tracking> — a case that is known to fail
# until a specific fix lands. It never turns the suite red: a mismatch is the
# documented status quo today, and a match means the fix landed and the case
# should be promoted to a plain assert_eq (one-word edit).
xfail_eq() {
  if [[ "$1" == "$2" ]]; then
    pass "$3"
    printf '       ^ %s appears to have landed — promote this case to assert_eq\n' "$4"
  else
    printf '  xfail %s\n' "$3"
    printf '       expected '\''%s'\'', got '\''%s'\'' — fixed by %s\n' "$1" "$2" "$4"
    xfailed=$((xfailed + 1))
  fi
}

# sandbox <name> — fresh HOME for one case; echoes its path.
sandbox() {
  local d="$SANDBOX_ROOT/$1"
  rm -rf "$d"; mkdir -p "$d"
  printf '%s' "$d"
}

# run_install <home> [args...] — run the installer with an isolated HOME.
# Captures stdout+stderr in RUN_OUT and the exit status in RUN_STATUS.
run_install() {
  local home="$1"; shift
  RUN_OUT="$(HOME="$home" "$INSTALL" --no-interactive "$@" 2>&1)"
  RUN_STATUS=$?
  $VERBOSE && printf '%s\n' "$RUN_OUT"
  return 0
}

# count_md <dir> — .md files directly in <dir> (0 when the dir does not exist).
count_md() {
  [[ -d "$1" ]] || { printf '0'; return; }
  find "$1" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' '
}

# ---------------------------------------------------------------------------
# Expected values, derived from the repo the same way install.sh derives them
# (divisions.json -> directories -> files with frontmatter), never hardcoded.
# ---------------------------------------------------------------------------
divisions_from_json() {
  awk '/"divisions"[[:space:]]*:[[:space:]]*\{/{f=1; next} f' "$REPO_ROOT/divisions.json" \
    | grep -oE '^[[:space:]]*"[a-z0-9-]+"[[:space:]]*:' \
    | sed -E 's/[[:space:]]*"([a-z0-9-]+)"[[:space:]]*:/\1/'
}

ALL_DIVISIONS=()
while IFS= read -r _d; do [[ -n "$_d" ]] && ALL_DIVISIONS+=("$_d"); done < <(divisions_from_json)

agent_files_in() {
  local d="$REPO_ROOT/$1" f
  [[ -d "$d" ]] || return 0
  while IFS= read -r f; do is_agent_file "$f" && printf '%s\n' "$f"; done \
    < <(find "$d" -name "*.md" -type f | sort)
}

TOTAL_AGENTS=0
for _div in "${ALL_DIVISIONS[@]}"; do
  TOTAL_AGENTS=$(( TOTAL_AGENTS + $(agent_files_in "$_div" | wc -l | tr -d ' ') ))
done
ENG_AGENTS=$(agent_files_in engineering | wc -l | tr -d ' ')
# `awk NR==1` rather than `head -1`: head exits at the first line and the
# still-writing function dies on SIGPIPE, which prints a spurious error.
FIRST_ENG_FILE="$(agent_files_in engineering | awk 'NR==1')"
FIRST_ENG_SLUG="$(agent_slug "$FIRST_ENG_FILE")"

echo "Testing $INSTALL"
echo "  repo: $REPO_ROOT"
echo "  ${#ALL_DIVISIONS[@]} divisions, $TOTAL_AGENTS agents (engineering: $ENG_AGENTS)"
echo ""

# ---------------------------------------------------------------------------
# 1. Help and listings
# ---------------------------------------------------------------------------
echo "help + listings"

home="$(sandbox help)"
RUN_OUT="$(HOME="$home" "$INSTALL" --help 2>&1)"; RUN_STATUS=$?
assert_eq 0 "$RUN_STATUS" "--help exits 0"
case "$RUN_OUT" in *"Usage:"*) pass "--help prints usage" ;; *) fail "--help prints usage" ;; esac

home="$(sandbox list-teams)"
run_install "$home" --list teams
assert_eq 0 "$RUN_STATUS" "--list teams exits 0"
missing=""
for _div in "${ALL_DIVISIONS[@]}"; do
  case "$RUN_OUT" in *"$_div"*) ;; *) missing="$missing $_div" ;; esac
done
assert_eq "" "$missing" "--list teams names every division in divisions.json"

home="$(sandbox list-agents)"
run_install "$home" --list agents
listed=$(printf '%s\n' "$RUN_OUT" | grep -c "$FIRST_ENG_SLUG")
[[ "$listed" -ge 1 ]] && pass "--list agents includes $FIRST_ENG_SLUG" \
  || fail "--list agents includes $FIRST_ENG_SLUG"

# ---------------------------------------------------------------------------
# 2. --dry-run writes nothing
# ---------------------------------------------------------------------------
echo ""
echo "dry-run"

home="$(sandbox dry-run)"
run_install "$home" --tool claude-code --dry-run
assert_eq 0 "$RUN_STATUS" "--dry-run exits 0"
assert_eq 0 "$(find "$home" -type f | wc -l | tr -d ' ')" "--dry-run creates no files"

# ---------------------------------------------------------------------------
# 3. Default destination + --path override
# ---------------------------------------------------------------------------
echo ""
echo "destinations"

home="$(sandbox default-dest)"
run_install "$home" --tool claude-code
assert_eq "$TOTAL_AGENTS" "$(count_md "$home/.claude/agents")" \
  "claude-code installs every agent to \$HOME/.claude/agents"
assert_eq 0 "$(count_md "$home/.claude")" "claude-code writes nothing into the config root"

home="$(sandbox path-override)"
dest="$home/custom-dir"
run_install "$home" --tool claude-code --path "$dest"
assert_eq "$TOTAL_AGENTS" "$(count_md "$dest")" "--path overrides the default destination"
assert_eq 0 "$(count_md "$home/.claude/agents")" "--path leaves the default destination empty"

# Env var override, and --path winning over it. COPILOT_AGENT_DIR is used here
# because it unambiguously names the agents directory itself.
home="$(sandbox env-override)"
dest="$home/from-env"
RUN_OUT="$(HOME="$home" COPILOT_AGENT_DIR="$dest" "$INSTALL" --no-interactive --tool copilot 2>&1)"
assert_eq "$TOTAL_AGENTS" "$(count_md "$dest")" "COPILOT_AGENT_DIR overrides the default destination"

home="$(sandbox env-vs-path)"
RUN_OUT="$(HOME="$home" COPILOT_AGENT_DIR="$home/from-env" "$INSTALL" --no-interactive \
  --tool copilot --path "$home/from-flag" 2>&1)"
assert_eq "$TOTAL_AGENTS" "$(count_md "$home/from-flag")" "--path wins over the env var"
assert_eq 0 "$(count_md "$home/from-env")" "env var destination is unused when --path is given"

# ---------------------------------------------------------------------------
# 3b. CLAUDE_CONFIG_DIR is the config root, not the agents dir (issue #578)
#
# Claude Code replaces ~/.claude with $CLAUDE_CONFIG_DIR, so agents belong in
# $CLAUDE_CONFIG_DIR/agents — matching the default ${HOME}/.claude/agents.
# Before the fix, resolve_dest returned the variable verbatim and agents
# landed in the config root where Claude Code never loads them; detection
# also missed relocated configs entirely.
# ---------------------------------------------------------------------------
home="$(sandbox claude-config-dir)"
cfg="$home/.config/claude-code"
RUN_OUT="$(HOME="$home" CLAUDE_CONFIG_DIR="$cfg" "$INSTALL" --no-interactive --tool claude-code 2>&1)"; RUN_STATUS=$?
assert_eq 0 "$RUN_STATUS" "CLAUDE_CONFIG_DIR install exits 0"
assert_eq "$TOTAL_AGENTS" "$(count_md "$cfg/agents")" "CLAUDE_CONFIG_DIR installs agents into \$CLAUDE_CONFIG_DIR/agents"
assert_eq 0 "$(count_md "$cfg")" "CLAUDE_CONFIG_DIR leaves the config root itself empty"

# Trailing slash and a pre-existing /agents suffix both resolve cleanly.
home="$(sandbox claude-config-dir-slash)"
cfg="$home/.config/claude-code/"
RUN_OUT="$(HOME="$home" CLAUDE_CONFIG_DIR="$cfg" "$INSTALL" --no-interactive --tool claude-code 2>&1)"; RUN_STATUS=$?
assert_eq 0 "$RUN_STATUS" "trailing-slash CLAUDE_CONFIG_DIR install exits 0"
assert_eq "$TOTAL_AGENTS" "$(count_md "$home/.config/claude-code/agents")" \
  "a trailing slash on CLAUDE_CONFIG_DIR still resolves to .../agents"

home="$(sandbox claude-config-dir-agents)"
cfg="$home/.config/claude-code/agents"
RUN_OUT="$(HOME="$home" CLAUDE_CONFIG_DIR="$cfg" "$INSTALL" --no-interactive --tool claude-code 2>&1)"; RUN_STATUS=$?
assert_eq 0 "$RUN_STATUS" "pre-suffixed CLAUDE_CONFIG_DIR install exits 0"
assert_eq "$TOTAL_AGENTS" "$(count_md "$cfg")" \
  "a CLAUDE_CONFIG_DIR already ending in /agents is used verbatim (no double-nesting)"

# ---------------------------------------------------------------------------
# 4. Paths with spaces (regression: word-splitting in the install loop)
# ---------------------------------------------------------------------------
echo ""
echo "paths with spaces"

home="$(sandbox 'spaces')"
dest="$home/My Agents/claude code"
run_install "$home" --tool claude-code --path "$dest"
assert_eq "$TOTAL_AGENTS" "$(count_md "$dest")" "installs into a path containing spaces"
assert_eq 0 "$(find "$home" -maxdepth 1 -name 'My' -o -maxdepth 1 -name 'Agents' | wc -l | tr -d ' ')" \
  "a spaced path is not split into separate directories"

# ---------------------------------------------------------------------------
# 4b. Parallel workers get their arguments intact (PR #755)
#
# --parallel hands the parent's selection state to child workers. On main that
# happens through a command-shaped string expanded unquoted, so a --path or
# --agents-file containing whitespace or glob characters is word-split and
# pathname-expanded on the way in. The install then writes nothing while still
# reporting "Done! Installed 2 tool(s)" and exiting 0 — a silent miss, which is
# why the exit-status assertion below cannot catch it on its own and the file
# count is what actually pins the regression.
#
# Two tools are required: a single tool stays on the serial path and never
# reaches the worker spawn.
#
# --jobs 1 is deliberate. Workers are still spawned through the same xargs/sh
# hand-off, so argument propagation — the thing under test — is exercised in
# full; serializing them just keeps a second, unrelated defect out of this case.
# With two workers running concurrently against one shared --path, the parent
# exits non-zero on roughly 3 runs in 5 (measured on macOS, bash 3.2) once the
# workers actually copy anything. That race is invisible on main only because
# the workers currently install nothing at all. See the PR discussion.
# ---------------------------------------------------------------------------
echo ""
echo "parallel workers"

# Two tools that write the same filenames into one shared --path would silently
# overwrite each other (claude-code and copilot both copy the raw source as
# <division>-<slug>.md). The installer must refuse, not clobber. Both tools work
# under --no-convert, which keeps this case cheap in CI.
home="$(sandbox path-collision)"
dest="$home/My [Agents]/dest dir"
run_install "$home" --tool claude-code,copilot --no-convert --agent "$FIRST_ENG_SLUG" --path "$dest"
assert_eq 1 "$RUN_STATUS" "two tools that write the same filenames into one --path are refused"
assert_eq 1 "$(printf '%s' "$RUN_OUT" | grep -c 'overwrite')" "the refusal explains the collision"
assert_eq 0 "$(count_md "$dest")" "a refused install writes nothing"

# The propagation cases below therefore use a NON-colliding pair: claude-code
# writes <division>-<slug>.md and codex writes <slug>.toml, so BOTH outputs must
# survive in the shared --path — which is a stronger check than one tool's count
# alone (a count of 1 cannot tell "two wrote, one clobbered" from "one wrote").
# codex has no committed output (integrations/ is generated and gitignored), so
# these cases let the installer convert.
home="$(sandbox parallel-serial-control)"
dest="$home/My [Agents]/dest dir"
list="$home/my agents list.txt"
{ echo "# same selection as the parallel case below"; echo "$FIRST_ENG_SLUG"; } > "$list"
run_install "$home" --tool claude-code,codex --agents-file "$list" --path "$dest"
assert_eq 0 "$RUN_STATUS" "serial control: two non-colliding tools, spaced/globbed --path, exits 0"
assert_eq 1 "$(count_md "$dest")" "serial control: claude-code installs exactly the one selected agent"
assert_eq 1 "$(find "$dest" -maxdepth 1 -name '*.toml' -type f 2>/dev/null | wc -l | tr -d ' ')" \
  "serial control: codex's output survives alongside claude-code's"

home="$(sandbox parallel)"
dest="$home/My [Agents]/dest dir"
list="$home/my agents list.txt"
{ echo "# one agent, listed in a file whose own path has spaces"; echo "$FIRST_ENG_SLUG"; } > "$list"
run_install "$home" --tool claude-code,codex --parallel --jobs 1 --agents-file "$list" --path "$dest"
assert_eq 0 "$RUN_STATUS" "--parallel with a spaced/globbed --path exits 0"
xfail_eq 1 "$(count_md "$dest")" \
  "--parallel installs exactly the one selected agent (spaced --path + --agents-file)" "PR #755"

# ---------------------------------------------------------------------------
# 5. Selection filters
# ---------------------------------------------------------------------------
echo ""
echo "selection"

home="$(sandbox division)"
dest="$home/dest"
run_install "$home" --tool claude-code --division engineering --path "$dest"
assert_eq "$ENG_AGENTS" "$(count_md "$dest")" "--division installs only that division"

home="$(sandbox agent)"
dest="$home/dest"
run_install "$home" --tool claude-code --agent "$FIRST_ENG_SLUG" --path "$dest"
assert_eq 1 "$(count_md "$dest")" "--agent installs exactly one agent"

home="$(sandbox agents-file)"
dest="$home/dest"
list="$home/agents.txt"
{ echo "# comment line"; echo ""; echo "$FIRST_ENG_SLUG"; } > "$list"
run_install "$home" --tool claude-code --agents-file "$list" --path "$dest"
assert_eq 1 "$(count_md "$dest")" "--agents-file skips comments and blank lines"

home="$(sandbox unknown-tool)"
run_install "$home" --tool definitely-not-a-tool
[[ "$RUN_STATUS" -ne 0 ]] && pass "unknown --tool exits non-zero" \
  || fail "unknown --tool exits non-zero" "exited 0"

# ---------------------------------------------------------------------------
# 6. --link and idempotency
# ---------------------------------------------------------------------------
echo ""
echo "link + repeat runs"

home="$(sandbox link)"
dest="$home/dest"
run_install "$home" --tool claude-code --link --division engineering --path "$dest"
links=$(find "$dest" -maxdepth 1 -type l | wc -l | tr -d ' ')
assert_eq "$ENG_AGENTS" "$links" "--link creates symlinks, not copies"

home="$(sandbox idempotent)"
dest="$home/dest"
run_install "$home" --tool claude-code --division engineering --path "$dest"
first=$(count_md "$dest")
run_install "$home" --tool claude-code --division engineering --path "$dest"
assert_eq "$first" "$(count_md "$dest")" "re-running installs the same set, not duplicates"

# ---------------------------------------------------------------------------
echo ""
if [[ $xfailed -gt 0 ]]; then
  echo "Results: $passed passed, $failed failed, $xfailed known-broken (xfail)."
else
  echo "Results: $passed passed, $failed failed."
fi
if [[ $failed -gt 0 ]]; then
  echo "FAILED"
  exit 1
fi
echo "PASSED"
