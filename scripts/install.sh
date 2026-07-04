#!/usr/bin/env bash
#
# --- USAGE-START ---  (sentinel for usage(); do not remove)
# install.sh -- Install The Agency agents into your local agentic tool(s).
#
# Reads converted files from integrations/ and copies them to the appropriate
# config directory for each tool. Run scripts/convert.sh first if integrations/
# is missing or stale.
#
# Usage:
#   ./scripts/install.sh [selection] [mode] [behavior]
#   Bare invocation installs all teams to detected tools (interactive when a TTY).
#
# Tools:
#   claude-code  -- Copy agents to ~/.claude/agents/
#   copilot      -- Copy agents to ~/.github/agents/ and ~/.copilot/agents/
#   antigravity  -- Copy skills to ~/.gemini/config/skills/
#   gemini-cli   -- Install agents to ~/.gemini/agents/
#   opencode     -- Copy agents to .opencode/agents/ in current directory
#   cursor       -- Copy rules to .cursor/rules/ in current directory
#   aider        -- Copy CONVENTIONS.md to current directory
#   windsurf     -- Copy .windsurfrules to current directory
#   openclaw     -- Copy workspaces to ~/.openclaw/agency-agents/
#   qwen         -- Copy SubAgents to ~/.qwen/agents/ (user-wide) or .qwen/agents/ (project)
#   codex        -- Copy custom agent TOML files to ~/.codex/agents/
#   osaurus      -- Copy skills to ~/.osaurus/skills/
#   hermes       -- Copy lazy-router plugin to ~/.hermes/plugins/ and enable it
#   vibe         -- Copy agents and prompts to ~/.vibe/agents/ and ~/.vibe/prompts/
#   all          -- Install for all detected tools (default)
#
# Selection (compose freely; empty = everything):
#   --tool <a,b>          Only these tools
#   --division <a,b>      Only these teams/divisions (comma-separated)
#   --agent <slug,slug>   Only these specific agents
#   --agents-file <path>  Agents listed in a file (one slug/name per line, # comments ok)
#
# Mode:
#   --link                Symlink instead of copy (updates propagate)
#   --path <dir>          Override the install directory (single destination)
#
# Behavior:
#   --interactive         Show the interactive wizard (default when run in a terminal)
#   --no-interactive      Skip the wizard, install all detected tools
#   --no-convert          Don't auto-run convert.sh when integration files are missing
#   --dry-run             Print the plan and exit without writing anything
#   --list [tools|teams|agents]   List and exit
#   --parallel            Install tools in parallel (output buffered per tool)
#   --jobs N              Max parallel jobs (default: nproc or 4)
#   --help                Show this help
#
# Env: CLAUDE_CONFIG_DIR, COPILOT_AGENT_DIR, CURSOR_RULES_DIR, GEMINI_AGENTS_DIR,
#      OPENCODE_AGENTS_DIR, OPENCLAW_DIR, QWEN_AGENTS_DIR, CODEX_AGENTS_DIR,
#      OSAURUS_SKILLS_DIR, HERMES_HOME, HERMES_PLUGIN_DIR, VIBE_HOME
#      override default install paths (checked before hardcoded defaults).
#
# --- USAGE-END ---  (sentinel for usage(); do not remove)
# Platform support:
#   Linux, macOS (requires bash 3.2+), Windows Git Bash / WSL

set -euo pipefail

# ---------------------------------------------------------------------------
# Colours -- only when stdout supports color
# ---------------------------------------------------------------------------
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  C_GREEN=$'\033[0;32m'
  C_YELLOW=$'\033[1;33m'
  C_RED=$'\033[0;31m'
  C_CYAN=$'\033[0;36m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_RESET=$'\033[0m'
else
  C_GREEN=''; C_YELLOW=''; C_RED=''; C_CYAN=''; C_BOLD=''; C_DIM=''; C_RESET=''
fi

ok()     { printf "${C_GREEN}[OK]${C_RESET}  %s\n" "$*"; }
warn()   { printf "${C_YELLOW}[!!]${C_RESET}  %s\n" "$*"; }
err()    { printf "${C_RED}[ERR]${C_RESET} %s\n" "$*" >&2; }
header() { printf "\n${C_BOLD}%s${C_RESET}\n" "$*"; }
dim()    { printf "${C_DIM}%s${C_RESET}\n" "$*"; }

# Progress bar: [=======>    ] 3/8 (tqdm-style)
progress_bar() {
  local current="$1" total="$2" width="${3:-20}" i filled empty
  (( total > 0 )) || return
  filled=$(( width * current / total ))
  empty=$(( width - filled ))
  printf "\r  ["
  for (( i=0; i<filled; i++ )); do printf "="; done
  if (( filled < width )); then printf ">"; (( empty-- )); fi
  for (( i=0; i<empty; i++ )); do printf " "; done
  printf "] %s/%s" "$current" "$total"
  [[ -t 1 ]] || printf "\n"
}

# ---------------------------------------------------------------------------
# Box drawing -- pure ASCII, fixed 52-char wide
#   box_top / box_mid / box_bot  -- structural lines
#   box_row <text>               -- content row, right-padded to fit
# ---------------------------------------------------------------------------
BOX_INNER=48   # chars between the two | walls

box_top() { printf "  +"; printf '%0.s-' $(seq 1 $BOX_INNER); printf "+\n"; }
box_bot() { box_top; }
box_sep() { printf "  |"; printf '%0.s-' $(seq 1 $BOX_INNER); printf "|\n"; }
strip_ansi() {
  awk '{ gsub(/\033\[[0-9;]*m/, ""); print }' <<< "$1"
}
box_row() {
  # Strip ANSI escapes when measuring visible length
  local raw="$1"
  local visible
  visible="$(strip_ansi "$raw")"
  local pad=$(( BOX_INNER - 2 - ${#visible} ))
  if (( pad < 0 )); then pad=0; fi
  printf "  | %s%*s |\n" "$raw" "$pad" ''
}
box_blank() { printf "  |%*s|\n" $BOX_INNER ''; }

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INTEGRATIONS="$REPO_ROOT/integrations"

# Shared helpers (get_field, agent_slug, slugify, incr, ANSI + TUI primitives)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

ALL_TOOLS=(claude-code copilot antigravity gemini-cli opencode openclaw cursor aider windsurf qwen kimi codex osaurus hermes vibe)

# Directories scanned for installable agents. Intentionally includes strategy/
# (its frontmatter-less NEXUS docs are filtered out by is_agent_file at scan time);
# the selectable division list below is this set minus strategy. This is NOT the
# same set as AGENT_DIRS in convert.sh / lint-agents.sh, which exclude strategy
# entirely — see divisions.json (the source of truth) and scripts/check-divisions.sh.
AGENT_DIRS=(
  academic design engineering finance game-development gis marketing paid-media product project-management
  sales security spatial-computing specialized strategy support testing
)

# ---------------------------------------------------------------------------
# Selection engine (team / agent / agents-file filtering)
# ---------------------------------------------------------------------------
# Selectable divisions = AGENT_DIRS minus strategy/ (NEXUS docs, not agents).
ALL_DIVISIONS=(
  academic design engineering finance game-development gis marketing paid-media
  product project-management sales security spatial-computing specialized support testing
)

FILTER_DIVISIONS=()      # --division
FILTER_AGENTS=()         # --agent
AGENTS_FILE=""           # --agents-file
DRY_RUN=false            # --dry-run
SELECTION_ACTIVE=false   # true once any agent-level filter is applied
_ALLOWED_SLUGS=""        # newline-delimited cache of allowed slugs

# division_files <division> — agent file paths (frontmatter only) in a division.
division_files() {
  local d="$REPO_ROOT/$1" f
  [[ -d "$d" ]] || return 0
  while IFS= read -r -d '' f; do
    is_agent_file "$f" && printf '%s\n' "$f"
  done < <(find "$d" -name "*.md" -type f -print0 2>/dev/null)
}

# division_count <division> — number of agents in a division.
division_count() { division_files "$1" | grep -c . ; }

# build_selection — compute the allowed slug set from --division/--agent/--agents-file.
# With no filter flags, SELECTION_ACTIVE stays false (install everything).
build_selection() {
  if [[ ${#FILTER_DIVISIONS[@]} -eq 0 && ${#FILTER_AGENTS[@]} -eq 0 && -z "$AGENTS_FILE" ]]; then
    SELECTION_ACTIVE=false
    return
  fi
  SELECTION_ACTIVE=true
  local slugs="" div f s line
  for div in ${FILTER_DIVISIONS[@]+"${FILTER_DIVISIONS[@]}"}; do
    while IFS= read -r f; do
      s="$(agent_slug "$f")"; [[ -n "$s" ]] && slugs+="$s"$'\n'
    done < <(division_files "$div")
  done
  for s in ${FILTER_AGENTS[@]+"${FILTER_AGENTS[@]}"}; do slugs+="$(slugify "$s")"$'\n'; done
  if [[ -n "$AGENTS_FILE" ]]; then
    [[ -f "$AGENTS_FILE" ]] || { err "agents-file not found: $AGENTS_FILE"; exit 1; }
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"                              # strip trailing comment
      line="$(printf '%s' "$line" | xargs 2>/dev/null)" # trim
      [[ -z "$line" ]] && continue
      slugs+="$(slugify "$line")"$'\n'
    done < "$AGENTS_FILE"
  fi
  _ALLOWED_SLUGS="$(printf '%s' "$slugs" | sort -u | sed '/^$/d')"
}

# slug_allowed <slug> — true if installable under the active selection
# (always true when no filter). Tolerates the antigravity "agency-" prefix.
slug_allowed() {
  $SELECTION_ACTIVE || return 0
  local s="${1#agency-}"
  printf '%s\n' "$_ALLOWED_SLUGS" | grep -qxF "$s"
}

# selected_agent_count — how many agents the current selection installs.
selected_agent_count() {
  if ! $SELECTION_ACTIVE; then
    local d n=0; for d in "${ALL_DIVISIONS[@]}"; do incr_by n "$(division_count "$d")"; done; echo "$n"
  else
    printf '%s\n' "$_ALLOWED_SLUGS" | grep -c .
  fi
}
incr_by() { printf -v "$1" '%d' "$(( ${!1:-0} + ${2:-0} ))"; }

# selected_agent_count_all — total agents across all divisions (ignores filter).
selected_agent_count_all() {
  local d n=0; for d in "${ALL_DIVISIONS[@]}"; do incr_by n "$(division_count "$d")"; done; echo "$n"
}

# worker_flags — re-emit the active selection/mode flags for parallel workers.
worker_flags() {
  local out="" d a
  $USE_LINK && out="$out --link"
  $AUTO_CONVERT || out="$out --no-convert"
  [[ -n "$OVERRIDE_PATH" ]] && out="$out --path $OVERRIDE_PATH"
  for d in ${FILTER_DIVISIONS[@]+"${FILTER_DIVISIONS[@]}"}; do out="$out --division $d"; done
  for a in ${FILTER_AGENTS[@]+"${FILTER_AGENTS[@]}"}; do out="$out --agent $a"; done
  [[ -n "$AGENTS_FILE" ]] && out="$out --agents-file $AGENTS_FILE"
  printf '%s' "$out"
}

# validate_division <name> — exit on unknown division.
validate_division() {
  local _ad
  for _ad in "${ALL_DIVISIONS[@]}"; do [[ "$_ad" == "$1" ]] && return 0; done
  err "Unknown division '$1'. Valid: ${ALL_DIVISIONS[*]}"
  exit 1
}

# ---------------------------------------------------------------------------
# Install mechanics (copy vs symlink, path override, capacity guard)
# ---------------------------------------------------------------------------
USE_LINK=false        # --link
OVERRIDE_PATH=""      # --path (single-destination override)

# install_file <src> <dest> — copy, or symlink when --link is set.
install_file() {
  if $USE_LINK; then ln -sf "$1" "$2"; else cp "$1" "$2"; fi
}

# resolve_dest <tool> <default> — --path > $ENV_VAR > default.
resolve_dest() {
  local tool="$1" def="$2" var=""
  [[ -n "$OVERRIDE_PATH" ]] && { printf '%s' "$OVERRIDE_PATH"; return; }
  case "$tool" in
    claude-code) var="CLAUDE_CONFIG_DIR" ;;
    copilot)     var="COPILOT_AGENT_DIR" ;;
    cursor)      var="CURSOR_RULES_DIR" ;;
    gemini-cli)  var="GEMINI_AGENTS_DIR" ;;
    opencode)    var="OPENCODE_AGENTS_DIR" ;;
    openclaw)    var="OPENCLAW_DIR" ;;
    qwen)        var="QWEN_AGENTS_DIR" ;;
    codex)       var="CODEX_AGENTS_DIR" ;;
    osaurus)     var="OSAURUS_SKILLS_DIR" ;;
    hermes)      var="HERMES_PLUGIN_DIR" ;;
    vibe)        var="VIBE_HOME" ;;
  esac
  if [[ -n "$var" && -n "${!var:-}" ]]; then printf '%s' "${!var}"; else printf '%s' "$def"; fi
}

# resolve_tool_path <tool> — best-effort binary path for the detection UI.
resolve_tool_path() {
  local bin=""
  case "$1" in
    claude-code) bin="claude" ;; copilot) bin="code" ;; gemini-cli) bin="gemini" ;;
    opencode) bin="opencode" ;; openclaw) bin="openclaw" ;; cursor) bin="cursor" ;;
    aider) bin="aider" ;; windsurf) bin="windsurf" ;; qwen) bin="qwen" ;;
    kimi) bin="kimi" ;; codex) bin="codex" ;; antigravity) bin="" ;;
    osaurus) bin="osaurus" ;; hermes) bin="hermes" ;; vibe) bin="vibe" ;;
  esac
  [[ -n "$bin" ]] && command -v "$bin" 2>/dev/null
}

# ensure_converted <tool> — auto-run convert.sh if a converted tool's output
# is missing (absorbs #426). No-op for source tools and when --no-convert.
ensure_converted() {
  local tool="$1"
  $AUTO_CONVERT || return 0
  case "$tool" in claude-code|copilot) return 0 ;; esac
  local d="$INTEGRATIONS/$tool"
  if [[ ! -d "$d" ]] || [[ -z "$(find "$d" -type f 2>/dev/null | head -1)" ]]; then
    warn "$tool: integration files missing — running convert.sh --tool $tool"
    "$SCRIPT_DIR/convert.sh" --tool "$tool" >/dev/null 2>&1 \
      && ok "$tool: generated integration files" \
      || err "$tool: convert.sh failed; run it manually"
  fi
}
AUTO_CONVERT=true     # --no-convert disables

# Per-tool soft capacity (opencode silently drops past ~119 — upstream #27988).
tool_cap() { case "$1" in opencode) echo 119 ;; *) echo 0 ;; esac; }

# capacity_warn <tool> <count> — warn if a tool can't register this many.
capacity_warn() {
  local cap; cap="$(tool_cap "$1")"
  if [[ "$cap" -gt 0 && "$2" -gt "$cap" ]]; then
    warn "$1: registers only ~$cap agents (upstream bug anomalyco/opencode#27988)."
    warn "      You selected $2 — ~$(( $2 - cap )) won't load. Narrow with --division to fix."
  fi
}

# do_list <what> — print tools/teams/agents and exit.
do_list() {
  case "$1" in
    tools)
      printf '%s\n' "${ALL_TOOLS[@]}" ;;
    teams|divisions)
      local d; for d in "${ALL_DIVISIONS[@]}"; do printf '%-22s %3s agents\n' "$d" "$(division_count "$d")"; done ;;
    agents)
      local d f; for d in "${ALL_DIVISIONS[@]}"; do
        while IFS= read -r f; do printf '%-20s %s\n' "$d" "$(agent_slug "$f")"; done < <(division_files "$d")
      done ;;
    *)
      echo "Tools (${#ALL_TOOLS[@]}):"; printf '  %s\n' "${ALL_TOOLS[@]}"; echo
      echo "Teams (${#ALL_DIVISIONS[@]}):"
      local d; for d in "${ALL_DIVISIONS[@]}"; do printf '  %-22s %3s agents\n' "$d" "$(division_count "$d")"; done ;;
  esac
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
  # Extract everything between the USAGE-START / USAGE-END sentinels
  # (excluding the sentinel lines themselves) and strip the leading "# ".
  # Using sentinels instead of hard-coded line numbers means adding lines
  # to the header comment block won't silently break --help output.
  sed -n '/^# --- USAGE-START ---/,/^# --- USAGE-END ---/p' "$0" \
    | sed -e '1d;$d' -e 's/^# \{0,1\}//'
  exit 0
}

# Default parallel job count (nproc on Linux; sysctl on macOS when nproc missing)
parallel_jobs_default() {
  local n
  n=$(nproc 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  n=$(sysctl -n hw.ncpu 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  echo 4
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
check_integrations() {
  if [[ ! -d "$INTEGRATIONS" ]]; then
    err "integrations/ not found. Run ./scripts/convert.sh first."
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------
detect_claude_code() { [[ -d "${HOME}/.claude" ]]; }
detect_copilot()      { command -v code >/dev/null 2>&1 || [[ -d "${HOME}/.github" || -d "${HOME}/.copilot" ]]; }
detect_antigravity()  { [[ -d "${HOME}/.gemini/config/skills" ]]; }
detect_gemini_cli()   { command -v gemini >/dev/null 2>&1 || [[ -d "${HOME}/.gemini" ]]; }
detect_cursor()       { command -v cursor >/dev/null 2>&1 || [[ -d "${HOME}/.cursor" ]]; }
detect_opencode()     { command -v opencode >/dev/null 2>&1 || [[ -d "${HOME}/.config/opencode" ]]; }
detect_aider()        { command -v aider >/dev/null 2>&1; }
detect_openclaw()     { command -v openclaw >/dev/null 2>&1 || [[ -d "${HOME}/.openclaw" ]]; }
detect_windsurf()     { command -v windsurf >/dev/null 2>&1 || [[ -d "${HOME}/.codeium" ]]; }
detect_qwen()         { command -v qwen >/dev/null 2>&1 || [[ -d "${HOME}/.qwen" ]]; }
detect_kimi()         { command -v kimi >/dev/null 2>&1; }
detect_codex()        { command -v codex >/dev/null 2>&1 || [[ -d "${HOME}/.codex" ]]; }
detect_osaurus()      { command -v osaurus >/dev/null 2>&1 || [[ -d "${HOME}/.osaurus" ]]; }
detect_hermes()       { command -v hermes >/dev/null 2>&1 || [[ -d "${HERMES_HOME:-${HOME}/.hermes}" ]]; }
detect_vibe()         { command -v vibe >/dev/null 2>&1 || [[ -d "${VIBE_HOME:-${HOME}/.vibe}" ]]; }

is_detected() {
  case "$1" in
    claude-code) detect_claude_code ;;
    copilot)     detect_copilot     ;;
    antigravity) detect_antigravity ;;
    gemini-cli)  detect_gemini_cli  ;;
    opencode)    detect_opencode    ;;
    openclaw)    detect_openclaw    ;;
    cursor)      detect_cursor      ;;
    aider)       detect_aider       ;;
    windsurf)    detect_windsurf    ;;
    qwen)        detect_qwen        ;;
    kimi)        detect_kimi        ;;
    codex)       detect_codex       ;;
    osaurus)     detect_osaurus     ;;
    hermes)      detect_hermes      ;;
    vibe)        detect_vibe        ;;
    *)           return 1 ;;
  esac
}

# Fixed-width labels: name (14) + detail (24) = 38 visible chars
tool_label() {
  case "$1" in
    claude-code) printf "%-14s  %s" "Claude Code"  "(claude.ai/code)"        ;;
    copilot)     printf "%-14s  %s" "Copilot"      "(~/.github + ~/.copilot)" ;;
    antigravity) printf "%-14s  %s" "Antigravity"  "(~/.gemini/config/skills)" ;;
    gemini-cli)  printf "%-14s  %s" "Gemini CLI"   "(~/.gemini/agents)"      ;;
    opencode)    printf "%-14s  %s" "OpenCode"     "(opencode.ai)"           ;;
    openclaw)    printf "%-14s  %s" "OpenClaw"     "(~/.openclaw/agency-agents)" ;;
    cursor)      printf "%-14s  %s" "Cursor"       "(.cursor/rules)"         ;;
    aider)       printf "%-14s  %s" "Aider"        "(CONVENTIONS.md)"        ;;
    windsurf)    printf "%-14s  %s" "Windsurf"     "(.windsurfrules)"        ;;
    qwen)        printf "%-14s  %s" "Qwen Code"    "(~/.qwen/agents)"        ;;
    kimi)        printf "%-14s  %s" "Kimi Code"    "(~/.config/kimi/agents)" ;;
    codex)       printf "%-14s  %s" "Codex"        "(~/.codex/agents)"       ;;
    osaurus)     printf "%-14s  %s" "Osaurus"      "(~/.osaurus/skills)"     ;;
    hermes)      printf "%-14s  %s" "Hermes"       "(~/.hermes/plugins)"     ;;
    vibe)        printf "%-14s  %s" "Mistral Vibe" "(~/.vibe/agents)"        ;;
  esac
}

# ---------------------------------------------------------------------------
# Interactive selector
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Interactive wizard (pure-bash TUI):  Tools -> Teams -> Review -> install
# Uses lib.sh primitives (tui_begin/read_key/draw_frame). Falls back to the
# legacy auto-detect path when there is no TTY.
# ---------------------------------------------------------------------------

# Persistent selection state across screens.
TOOL_SEL=()      # 1/0 per ALL_TOOLS
TEAM_SEL=()      # 1/0 per ALL_DIVISIONS

# division_emoji <div> — a glyph for the team list (unicode only).
division_emoji() {
  if ! supports_unicode; then printf '*'; return; fi
  case "$1" in
    academic) printf '📚';; design) printf '🎨';; engineering) printf '💻';;
    finance) printf '💵';; game-development) printf '🎮';; gis) printf '🌍';; marketing) printf '📢';;
    paid-media) printf '💰';; product) printf '📊';; project-management) printf '🎬';;
    sales) printf '💼';; security) printf '🔒';; spatial-computing) printf '🥽';;
    specialized) printf '🎯';; support) printf '🛟';; testing) printf '🧪';; *) printf '•';;
  esac
}

# Generic multi-select. Inputs (globals): OPT_LABEL[], OPT_SEL[];
# SEL_TITLE, SEL_HINT, SEL_SUMMARY_FN, SEL_NAV, SEL_WARN_FN.
# Mutates OPT_SEL[]; sets SEL_RESULT = next|back|quit.
selector() {
  local n=${#OPT_LABEL[@]} cur=0 top=0 query="" searching=false key i idx vn rows W
  rows=$(( $(term_rows) - 9 )); (( rows < 3 )) && rows=3
  while true; do
    local view=() qlc
    qlc="$(printf '%s' "$query" | tr '[:upper:]' '[:lower:]')"
    for (( i=0; i<n; i++ )); do
      if [[ -z "$query" || "$(printf '%s' "${OPT_LABEL[$i]}" | tr '[:upper:]' '[:lower:]')" == *"$qlc"* ]]; then
        view+=("$i")
      fi
    done
    vn=${#view[@]}
    (( cur>=vn )) && cur=$(( vn>0 ? vn-1 : 0 ))
    (( cur<top )) && top=$cur
    (( cur>=top+rows )) && top=$(( cur-rows+1 ))
    W=$(( $(term_cols) - 4 )); (( W>74 )) && W=74; (( W<40 )) && W=40
    local buf="" hlen=$(( W - ${#SEL_TITLE} - 5 )); (( hlen<1 )) && hlen=1
    buf+="  ${C_BOLD}${C_CYAN}${BX_TL}${BX_H}${BX_H} ${SEL_TITLE} $(repeat "$BX_H" "$hlen")${BX_TR}${C_RESET}"$'\n'
    buf+="  ${C_DIM}${SEL_HINT}${C_RESET}"$'\n\n'
    (( vn==0 )) && buf+="   ${C_DIM}(no matches)${C_RESET}"$'\n'
    for (( i=top; i<top+rows && i<vn; i++ )); do
      idx=${view[$i]}
      local mark cg label="${OPT_LABEL[$idx]}"
      [[ "${OPT_SEL[$idx]}" == 1 ]] && mark="${C_GREEN}${GLYPH_ON}${C_RESET}" || mark="${C_DIM}·${C_RESET}"
      if (( i==cur )); then cg="${C_CYAN}${GLYPH_CUR}${C_RESET}"; label="${C_BOLD}${label}${C_RESET}"; else cg=" "; fi
      buf+="   $cg [$mark] $label"$'\n'
    done
    local shown=$(( vn<rows ? vn : rows )); for (( i=shown; i<rows; i++ )); do buf+=$'\n'; done
    # Consistent footer: summary -> nav -> warnings (-> search line)
    buf+=$'\n'"  ${C_BOLD}$("$SEL_SUMMARY_FN")${C_RESET}"$'\n'
    buf+="  ${C_DIM}${SEL_NAV}${C_RESET}"$'\n'
    local _w; _w="$("$SEL_WARN_FN")"; [[ -n "$_w" ]] && buf+="  ${C_YELLOW}${_w}${C_RESET}"$'\n'
    if $searching; then buf+="  ${C_CYAN}search:${C_RESET} ${query}_"$'\n'
    elif [[ -n "$query" ]]; then buf+="  ${C_CYAN}/${query}${C_RESET}  ${C_DIM}(esc clears)${C_RESET}"$'\n'; fi
    draw_frame "$buf"

    key="$(read_key)"
    if $searching; then
      case "$key" in
        ENTER) searching=false ;;
        ESC)   query=""; searching=false ;;
        BACKSPACE) query="${query%?}" ;;
        *) [[ ${#key} -eq 1 ]] && query="$query$key" ;;
      esac
      continue
    fi
    case "$key" in
      UP|k)        (( cur>0 ))    && cur=$(( cur-1 )) ;;
      DOWN|j)      (( cur<vn-1 )) && cur=$(( cur+1 )) ;;
      SPACE)       (( vn>0 )) && { idx=${view[$cur]}; OPT_SEL[$idx]=$(( 1 - ${OPT_SEL[$idx]} )); } ;;
      a|A)         for (( i=0; i<n; i++ )); do OPT_SEL[$i]=1; done ;;
      n|N)         for (( i=0; i<n; i++ )); do OPT_SEL[$i]=0; done ;;
      /)           searching=true ;;
      ENTER|RIGHT) SEL_RESULT=next; return ;;
      LEFT)        SEL_RESULT=back; return ;;
      ESC)         [[ -n "$query" ]] && query="" || { SEL_RESULT=back; return; } ;;
      q|Q)         SEL_RESULT=quit; return ;;
      EOF)         SEL_RESULT=quit; return ;;
    esac
  done
}

# --- Screen: Tools ---
_no_warn() { :; }
_tools_summary() {
  local i c=0; for (( i=0; i<${#OPT_SEL[@]}; i++ )); do [[ "${OPT_SEL[$i]}" == 1 ]] && c=$(( c+1 )); done
  printf '%s of %s tools selected' "$c" "${#OPT_SEL[@]}"
}
screen_tools() {
  OPT_LABEL=(); OPT_SEL=()
  local i det path label
  for (( i=0; i<${#ALL_TOOLS[@]}; i++ )); do
    local t="${ALL_TOOLS[$i]}"
    path="$(resolve_tool_path "$t" 2>/dev/null || true)"
    if is_detected "$t" 2>/dev/null; then det="${C_GREEN}${GLYPH_DET}${C_RESET}"; else det="${C_DIM}${GLYPH_OFF}${C_RESET}"; fi
    label="$(printf '%s %-13s %s' "$det" "$(tool_simple_name "$t")" "${C_DIM}${path:-not found}${C_RESET}")"
    OPT_LABEL+=("$label"); OPT_SEL+=("${TOOL_SEL[$i]:-0}")
  done
  SEL_TITLE="The Agency · Installer  —  1/3 · Tools"
  SEL_HINT="Pick where to install.  ${GLYPH_DET} = detected on this machine."
  SEL_SUMMARY_FN=_tools_summary
  SEL_NAV="space toggle · a all · n none · / search · enter next · q quit"
  SEL_WARN_FN=_no_warn
  selector
  for (( i=0; i<${#OPT_SEL[@]}; i++ )); do TOOL_SEL[$i]="${OPT_SEL[$i]}"; done
}

tool_simple_name() {
  case "$1" in
    claude-code) echo "Claude Code";; copilot) echo "Copilot";; antigravity) echo "Antigravity";;
    gemini-cli) echo "Gemini CLI";; opencode) echo "OpenCode";; openclaw) echo "OpenClaw";;
    cursor) echo "Cursor";; aider) echo "Aider";; windsurf) echo "Windsurf";;
    qwen) echo "Qwen Code";; kimi) echo "Kimi Code";; codex) echo "Codex";; osaurus) echo "Osaurus";; *) echo "$1";;
  esac
}

# --- Screen: Teams ---
_teams_agents() {
  local i c=0 d
  for (( i=0; i<${#ALL_DIVISIONS[@]}; i++ )); do
    [[ "${OPT_SEL[$i]}" == 1 ]] && { d="${ALL_DIVISIONS[$i]}"; c=$(( c + ${TEAM_COUNTS[$i]} )); }
  done
  echo "$c"
}
_teams_summary() {
  local sel=0 i a; a="$(_teams_agents)"
  for (( i=0; i<${#OPT_SEL[@]}; i++ )); do [[ "${OPT_SEL[$i]}" == 1 ]] && sel=$(( sel+1 )); done
  printf '%s agents · %s of %s teams' "$a" "$sel" "${#OPT_SEL[@]}"
}
_teams_warn() {
  local a cap; a="$(_teams_agents)"; cap="$(tool_cap opencode)"
  if _opencode_selected && [[ "$a" -gt "$cap" ]]; then
    printf "⚠ OpenCode registers ~%s; ~%s of %s won't load (#27988)" "$cap" "$(( a - cap ))" "$a"
  fi
}
_opencode_selected() {
  local i; for (( i=0; i<${#TOOL_SEL[@]}; i++ )); do
    [[ "${ALL_TOOLS[$i]}" == "opencode" && "${TOOL_SEL[$i]}" == 1 ]] && return 0
  done; return 1
}
screen_teams() {
  OPT_LABEL=(); OPT_SEL=()
  local i
  for (( i=0; i<${#ALL_DIVISIONS[@]}; i++ )); do
    local d="${ALL_DIVISIONS[$i]}"
    OPT_LABEL+=("$(printf '%s %-20s %s' "$(division_emoji "$d")" "$d" "${C_DIM}${TEAM_COUNTS[$i]} agents${C_RESET}")")
    OPT_SEL+=("${TEAM_SEL[$i]:-1}")
  done
  SEL_TITLE="The Agency · Installer  —  2/3 · Teams"
  SEL_HINT="Pick which teams to install.  Fewer teams keeps OpenCode under its limit."
  SEL_SUMMARY_FN=_teams_summary
  SEL_NAV="space toggle · a all · n none · / search · enter next · ← back · q quit"
  SEL_WARN_FN=_teams_warn
  selector
  for (( i=0; i<${#OPT_SEL[@]}; i++ )); do TEAM_SEL[$i]="${OPT_SEL[$i]}"; done
}

# --- Screen: Review ---
REVIEW_RESULT=""
# grid_2col <cellwidth> <items...> — lay items out in two column-major columns
# (left column filled top-to-bottom first). Plain text cells (no ANSI) so the
# width padding stays correct.
grid_2col() {
  local w="$1"; shift
  local n=$# r rows left right out=""
  (( n==0 )) && { printf '     %snone%s\n' "$C_DIM" "$C_RESET"; return; }
  local items=("$@")
  rows=$(( (n + 1) / 2 ))
  for (( r=0; r<rows; r++ )); do
    left="${items[$r]}"
    right="${items[$(( r + rows ))]:-}"
    if [[ -n "$right" ]]; then out+="$(printf '     %-*s  %s' "$w" "$left" "$right")"$'\n'
    else out+="     $left"$'\n'; fi
  done
  printf '%s' "$out"
}

screen_review() {
  local tools=() teams=() i agents
  for (( i=0; i<${#TOOL_SEL[@]}; i++ )); do [[ "${TOOL_SEL[$i]}" == 1 ]] && tools+=("$(tool_simple_name "${ALL_TOOLS[$i]}")"); done
  for (( i=0; i<${#TEAM_SEL[@]}; i++ )); do [[ "${TEAM_SEL[$i]}" == 1 ]] && teams+=("${ALL_DIVISIONS[$i]}"); done
  agents=0; for (( i=0; i<${#TEAM_SEL[@]}; i++ )); do [[ "${TEAM_SEL[$i]}" == 1 ]] && agents=$(( agents + ${TEAM_COUNTS[$i]} )); done
  local cur=0   # 0=Install 1=mode toggle
  while true; do
    local buf="" m
    # pager
    buf+="  ${C_BOLD}${C_CYAN}${BX_TL}${BX_H}${BX_H} The Agency · Installer  —  3/3 · Review $(repeat "$BX_H" 28)${BX_TR}${C_RESET}"$'\n'
    # description
    buf+="  ${C_DIM}Confirm your selection, then install.${C_RESET}"$'\n\n'
    # content: the selections + the mode toggle
    buf+="   ${C_BOLD}Tools${C_RESET} ${C_DIM}(${#tools[@]})${C_RESET}"$'\n'
    buf+="$(grid_2col 16 ${tools[@]+"${tools[@]}"})"$'\n'
    buf+="   ${C_BOLD}Teams${C_RESET} ${C_DIM}(${#teams[@]})${C_RESET}"$'\n'
    buf+="$(grid_2col 20 ${teams[@]+"${teams[@]}"})"$'\n\n'
    $USE_LINK && m="symlink" || m="copy"
    if (( cur==1 )); then buf+="   ${C_CYAN}${GLYPH_CUR}${C_RESET} Mode: ${C_BOLD}${m}${C_RESET}  ${C_DIM}(space toggles copy/symlink)${C_RESET}"$'\n'
    else buf+="     Mode: ${m}  ${C_DIM}(space toggles copy/symlink)${C_RESET}"$'\n'; fi
    buf+=$'\n'
    # summary
    buf+="  ${C_BOLD}Installing ${agents} agents · ${#teams[@]} teams · ${#tools[@]} tools${C_RESET}"$'\n'
    # navigation (Install is the action cursor target)
    if (( cur==0 )); then buf+="  ${C_CYAN}${GLYPH_CUR}${C_RESET} ${C_BOLD}${C_GREEN}Install${C_RESET}   ${C_DIM}↑/↓ move · enter install · ← back · q quit${C_RESET}"$'\n'
    else buf+="    ${C_GREEN}Install${C_RESET}   ${C_DIM}↑/↓ move · space toggle mode · ← back · q quit${C_RESET}"$'\n'; fi
    # warnings
    local cap; cap="$(tool_cap opencode)"
    if printf '%s\n' "${tools[@]}" | grep -qx "OpenCode" && [[ "$agents" -gt "$cap" ]]; then
      buf+="  ${C_YELLOW}⚠ OpenCode registers ~${cap}; ~$(( agents - cap )) of ${agents} won't load (#27988)${C_RESET}"$'\n'
    fi
    draw_frame "$buf"
    local key; key="$(read_key)"
    case "$key" in
      UP|DOWN|k|j|TAB) cur=$(( 1 - cur )) ;;
      SPACE) (( cur==1 )) && { $USE_LINK && USE_LINK=false || USE_LINK=true; } ;;
      ENTER) if (( cur==0 )); then REVIEW_RESULT=install; return; fi ;;
      LEFT)  REVIEW_RESULT=back; return ;;
      q|Q|EOF) REVIEW_RESULT=quit; return ;;
    esac
  done
}

# interactive_wizard — drive the three screens; commit to SELECTED_TOOLS /
# FILTER_DIVISIONS / USE_LINK. Returns 1 if no TTY (caller falls back).
interactive_wizard() {
  init_ansi
  TEAM_COUNTS=(); local i
  for (( i=0; i<${#ALL_DIVISIONS[@]}; i++ )); do TEAM_COUNTS+=("$(division_count "${ALL_DIVISIONS[$i]}")"); done
  # seed defaults: tools = detected, teams = all
  TOOL_SEL=(); for (( i=0; i<${#ALL_TOOLS[@]}; i++ )); do is_detected "${ALL_TOOLS[$i]}" 2>/dev/null && TOOL_SEL+=(1) || TOOL_SEL+=(0); done
  TEAM_SEL=(); for (( i=0; i<${#ALL_DIVISIONS[@]}; i++ )); do TEAM_SEL+=(1); done

  tui_begin || return 1
  local screen=tools
  while true; do
    case "$screen" in
      tools)  screen_tools;  case "$SEL_RESULT" in next) screen=teams;; quit) tui_end; exit 0;; esac ;;
      teams)  screen_teams;  case "$SEL_RESULT" in next) screen=review;; back) screen=tools;; quit) tui_end; exit 0;; esac ;;
      review) screen_review; case "$REVIEW_RESULT" in install) break;; back) screen=teams;; quit) tui_end; exit 0;; esac ;;
    esac
  done
  tui_end

  # commit
  SELECTED_TOOLS=()
  for (( i=0; i<${#TOOL_SEL[@]}; i++ )); do [[ "${TOOL_SEL[$i]}" == 1 ]] && SELECTED_TOOLS+=("${ALL_TOOLS[$i]}"); done
  FILTER_DIVISIONS=()
  local all=1
  for (( i=0; i<${#TEAM_SEL[@]}; i++ )); do [[ "${TEAM_SEL[$i]}" == 1 ]] || all=0; done
  if [[ "$all" == 0 ]]; then
    for (( i=0; i<${#TEAM_SEL[@]}; i++ )); do [[ "${TEAM_SEL[$i]}" == 1 ]] && FILTER_DIVISIONS+=("${ALL_DIVISIONS[$i]}"); done
  fi
  build_selection
  return 0
}

# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------

install_claude_code() {
  local dest; dest="$(resolve_dest claude-code "${HOME}/.claude/agents")"
  local count=0 dir f slug
  mkdir -p "$dest"
  for dir in "${AGENT_DIRS[@]}"; do
    [[ -d "$REPO_ROOT/$dir" ]] || continue
    while IFS= read -r -d '' f; do
      is_agent_file "$f" || continue
      slug="$(agent_slug "$f")"; slug_allowed "$slug" || continue
      install_file "$f" "$dest/"; incr count
    done < <(find "$REPO_ROOT/$dir" -name "*.md" -type f -print0)
  done
  ok "Claude Code: $count agents -> $dest"
}

install_copilot() {
  local dest_github; dest_github="$(resolve_dest copilot "${HOME}/.github/agents")"
  local dest_copilot="${HOME}/.copilot/agents"
  local count=0 dir f slug
  mkdir -p "$dest_github" "$dest_copilot"
  for dir in "${AGENT_DIRS[@]}"; do
    [[ -d "$REPO_ROOT/$dir" ]] || continue
    while IFS= read -r -d '' f; do
      is_agent_file "$f" || continue
      slug="$(agent_slug "$f")"; slug_allowed "$slug" || continue
      install_file "$f" "$dest_github/"
      install_file "$f" "$dest_copilot/"
      incr count
    done < <(find "$REPO_ROOT/$dir" -name "*.md" -type f -print0)
  done
  ok "Copilot: $count agents -> $dest_github"
  ok "Copilot: $count agents -> $dest_copilot"
  warn "Copilot: Verify VS Code setting 'chat.agentFilesLocations' includes your install path."
  dim  "         Open Settings (Ctrl/Cmd+,) -> search 'chat.agentFilesLocations'"
}

install_antigravity() {
  local src="$INTEGRATIONS/antigravity"
  local dest; dest="$(resolve_dest antigravity "${HOME}/.gemini/config/skills")"
  local count=0
  [[ -d "$src" ]] || { err "integrations/antigravity missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    slug_allowed "$name" || continue
    mkdir -p "$dest/$name"
    install_file "$d/SKILL.md" "$dest/$name/SKILL.md"
    incr count
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)
  ok "Antigravity: $count skills -> $dest"
}

install_osaurus() {
  local src="$INTEGRATIONS/osaurus"
  local dest; dest="$(resolve_dest osaurus "${HOME}/.osaurus/skills")"
  local count=0
  [[ -d "$src" ]] || { err "integrations/osaurus missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    slug_allowed "$name" || continue
    mkdir -p "$dest/$name"
    install_file "$d/SKILL.md" "$dest/$name/SKILL.md"
    incr count
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)
  ok "Osaurus: $count skills -> $dest"
}

install_gemini_cli() {
  local src="$INTEGRATIONS/gemini-cli/agents"
  local dest; dest="$(resolve_dest gemini-cli "${HOME}/.gemini/agents")"
  local count=0
  [[ -d "$src" ]] || { err "integrations/gemini-cli/agents missing. Run ./scripts/convert.sh --tool gemini-cli first."; return 1; }
  mkdir -p "$dest"
  local f
  while IFS= read -r -d '' f; do
    slug_allowed "$(basename "$f" .md)" || continue
    install_file "$f" "$dest/"
    incr count
  done < <(find "$src" -maxdepth 1 -name "*.md" -print0)
  ok "Gemini CLI: $count agents -> $dest"
}

install_opencode() {
  local src="$INTEGRATIONS/opencode"
  local dest; dest="$(resolve_dest opencode "${PWD}/.opencode/agents")"
  local count=0
  [[ -d "$src" ]] || { err "integrations/opencode missing. Run convert.sh first."; return 1; }
  # Support both flat layout (integrations/opencode/*.md) and nested (integrations/opencode/agents/*.md)
  local search_dir="$src"
  [[ -d "$src/agents" ]] && search_dir="$src/agents"
  mkdir -p "$dest"
  local f base
  while IFS= read -r -d '' f; do
    base="$(basename "$f")"
    [[ "$base" == "README.md" ]] && continue
    slug_allowed "${base%.md}" || continue
    install_file "$f" "$dest/"; incr count
  done < <(find "$search_dir" -maxdepth 1 -name "*.md" -print0)
  if (( count == 0 )); then
    warn "OpenCode: no agent files found in $search_dir. Run convert.sh --tool opencode first."
  else
    ok "OpenCode: $count agents -> $dest"
  fi
  capacity_warn opencode "$count"
  warn "OpenCode: project-scoped. Run from your project root to install there."
}

install_openclaw() {
  local src="$INTEGRATIONS/openclaw"
  local dest; dest="$(resolve_dest openclaw "${HOME}/.openclaw/agency-agents")"
  local count=0
  local existing_agents=""
  [[ -d "$src" ]] || { err "integrations/openclaw missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  if command -v openclaw >/dev/null 2>&1; then
    existing_agents=$'\n'"$(openclaw agents list --json 2>/dev/null | sed -n 's/^[[:space:]]*\"id\": \"\\([^\"]*\\)\".*/\\1/p')"$'\n'
  fi
  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    slug_allowed "$name" || continue
    [[ -f "$d/SOUL.md" && -f "$d/AGENTS.md" && -f "$d/IDENTITY.md" ]] || continue
    mkdir -p "$dest/$name"
    install_file "$d/SOUL.md" "$dest/$name/SOUL.md"
    install_file "$d/AGENTS.md" "$dest/$name/AGENTS.md"
    install_file "$d/IDENTITY.md" "$dest/$name/IDENTITY.md"
    if command -v openclaw >/dev/null 2>&1; then
      if [[ "$existing_agents" != *$'\n'"$name"$'\n'* ]]; then
        openclaw agents add "$name" --workspace "$dest/$name" --non-interactive || true
      fi
    fi
    (( count++ )) || true
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)
  if (( count == 0 )); then
    err "integrations/openclaw contains no generated workspaces. Run ./scripts/convert.sh --tool openclaw first."
    return 1
  fi
  ok "OpenClaw: $count workspaces -> $dest"
  if command -v openclaw >/dev/null 2>&1; then
    warn "OpenClaw: run 'openclaw gateway restart' to activate new agents"
  fi
}

install_cursor() {
  local src="$INTEGRATIONS/cursor/rules"
  local dest; dest="$(resolve_dest cursor "${PWD}/.cursor/rules")"
  local count=0
  [[ -d "$src" ]] || { err "integrations/cursor missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local f
  while IFS= read -r -d '' f; do
    slug_allowed "$(basename "$f" .mdc)" || continue
    install_file "$f" "$dest/"; incr count
  done < <(find "$src" -maxdepth 1 -name "*.mdc" -print0)
  ok "Cursor: $count rules -> $dest"
  warn "Cursor: project-scoped. Run from your project root to install there."
}

install_aider() {
  local src="$INTEGRATIONS/aider/CONVENTIONS.md"
  local dest="${PWD}/CONVENTIONS.md"
  [[ -f "$src" ]] || { err "integrations/aider/CONVENTIONS.md missing. Run convert.sh first."; return 1; }
  if [[ -f "$dest" ]]; then
    warn "Aider: CONVENTIONS.md already exists at $dest (remove to reinstall)."
    return 0
  fi
  install_file "$src" "$dest"
  ok "Aider: installed -> $dest"
  $SELECTION_ACTIVE && warn "Aider: single-file format — team/agent filtering N/A (installs the full roster)."
  warn "Aider: project-scoped. Run from your project root to install there."
}

install_windsurf() {
  local src="$INTEGRATIONS/windsurf/.windsurfrules"
  local dest="${PWD}/.windsurfrules"
  [[ -f "$src" ]] || { err "integrations/windsurf/.windsurfrules missing. Run convert.sh first."; return 1; }
  if [[ -f "$dest" ]]; then
    warn "Windsurf: .windsurfrules already exists at $dest (remove to reinstall)."
    return 0
  fi
  install_file "$src" "$dest"
  ok "Windsurf: installed -> $dest"
  $SELECTION_ACTIVE && warn "Windsurf: single-file format — team/agent filtering N/A (installs the full roster)."
  warn "Windsurf: project-scoped. Run from your project root to install there."
}

install_qwen() {
  local src="$INTEGRATIONS/qwen/agents"
  local dest; dest="$(resolve_dest qwen "${PWD}/.qwen/agents")"
  local count=0

  [[ -d "$src" ]] || { err "integrations/qwen missing. Run convert.sh first."; return 1; }

  mkdir -p "$dest"

  local f
  while IFS= read -r -d '' f; do
    slug_allowed "$(basename "$f" .md)" || continue
    install_file "$f" "$dest/"
    incr count
  done < <(find "$src" -maxdepth 1 -name "*.md" -print0)

  ok "Qwen Code: installed $count agents to $dest"
  warn "Qwen Code: project-scoped. Run from your project root to install there."
  warn "Tip: Run '/agents manage' in Qwen Code to refresh, or restart session"
}

install_kimi() {
  local src="$INTEGRATIONS/kimi"
  local dest; dest="$(resolve_dest kimi "${HOME}/.config/kimi/agents")"
  local count=0

  [[ -d "$src" ]] || { err "integrations/kimi missing. Run convert.sh first."; return 1; }

  mkdir -p "$dest"

  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    slug_allowed "$name" || continue
    mkdir -p "$dest/$name"
    install_file "$d/agent.yaml" "$dest/$name/agent.yaml"
    install_file "$d/system.md" "$dest/$name/system.md"
    incr count
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)

  ok "Kimi Code: installed $count agents to $dest"
  ok "Usage: kimi --agent-file ~/.config/kimi/agents/<agent-name>/agent.yaml"
}

install_codex() {
  local src="$INTEGRATIONS/codex/agents"
  local dest; dest="$(resolve_dest codex "${HOME}/.codex/agents")"
  local count=0
  [[ -d "$src" ]] || { err "integrations/codex missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local f
  while IFS= read -r -d '' f; do
    slug_allowed "$(basename "$f" .toml)" || continue
    install_file "$f" "$dest/"
    incr count
  done < <(find "$src" -maxdepth 1 -name "*.toml" -print0)
  ok "Codex: $count agents -> $dest"
}

install_vibe() {
  local src_agents="$INTEGRATIONS/vibe/agents"
  local src_prompts="$INTEGRATIONS/vibe/prompts"
  local dest; dest="$(resolve_dest vibe "${HOME}/.vibe")"
  local count=0
  
  [[ -d "$src_agents" && -d "$src_prompts" ]] || { err "integrations/vibe missing. Run convert.sh first."; return 1; }
  
  mkdir -p "$dest/agents" "$dest/prompts"
  
  local agent_file prompt_file slug
  
  while IFS= read -r -d '' agent_file; do
    slug="$(basename "$agent_file" .toml)"
    slug_allowed "$slug" || continue
    
    # Find the corresponding prompt file
    prompt_file="$src_prompts/$slug.md"
    
    [[ -f "$prompt_file" ]] || continue
    
    install_file "$agent_file" "$dest/agents/"
    install_file "$prompt_file" "$dest/prompts/"
    incr count
  done < <(find "$src_agents" -maxdepth 1 -name "*.toml" -print0)
  
  ok "Mistral Vibe: $count agents -> $dest/agents/ and $dest/prompts/"
}

vibe_home_dir() {
  printf '%s\n' "${VIBE_HOME:-${HOME}/.vibe}"
}

hermes_home_dir() {
  printf '%s\n' "${HERMES_HOME:-${HOME}/.hermes}"
}

ensure_hermes_plugin_enabled() {
  local hermes_home config plugin backup
  hermes_home="$(hermes_home_dir)"
  config="${hermes_home}/config.yaml"
  plugin="agency-agents-router"
  mkdir -p "$hermes_home"
  backup="${config}.bak.agency-agents-plugin.$$"
  [[ -f "$config" ]] && cp "$config" "$backup"
  python3 - "$config" "$plugin" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
plugin = sys.argv[2]
text = path.read_text() if path.exists() else ""
lines = text.splitlines()

# Already enabled?
in_plugins = False
in_enabled = False
for line in lines:
    if line.startswith("plugins:"):
        in_plugins = True
        in_enabled = False
        continue
    if in_plugins and line and not line.startswith((" ", "\t")):
        in_plugins = False
        in_enabled = False
    stripped_line = line.strip()
    if in_plugins and stripped_line == "enabled:":
        in_enabled = True
        continue
    if in_plugins and stripped_line.startswith("enabled:") and "[]" in stripped_line:
        in_enabled = False
        continue
    if in_enabled:
        stripped = line.strip()
        if stripped.startswith("-"):
            value = stripped[1:].strip().strip('"\'')
            if value == plugin:
                sys.exit(0)
        elif line.startswith("  ") and stripped.endswith(":"):
            in_enabled = False

if not lines:
    lines = ["plugins:", "  enabled:", f"  - {plugin}"]
elif not any(line.startswith("plugins:") for line in lines):
    if lines and lines[-1].strip():
        lines.append("")
    lines.extend(["plugins:", "  enabled:", f"  - {plugin}"])
else:
    out = []
    in_plugins = False
    inserted = False
    saw_enabled = False
    for idx, line in enumerate(lines):
        if line.startswith("plugins:"):
            in_plugins = True
            out.append(line)
            continue
        if in_plugins and line and not line.startswith((" ", "\t")):
            if not saw_enabled and not inserted:
                out.extend(["  enabled:", f"  - {plugin}"])
                inserted = True
            in_plugins = False
            out.append(line)
            continue
        if in_plugins and line.strip().startswith("enabled:") and "[]" in line:
            saw_enabled = True
            out.extend(["  enabled:", f"  - {plugin}"])
            inserted = True
            continue
        if in_plugins and line.strip() == "enabled:":
            saw_enabled = True
            out.append(line)
            # Insert before the next sibling key or top-level key; if the list is
            # empty this still creates a valid block.
            out.append(f"  - {plugin}")
            inserted = True
            continue
        out.append(line)
    if in_plugins and not saw_enabled and not inserted:
        out.extend(["  enabled:", f"  - {plugin}"])
    lines = out
path.write_text("\n".join(lines) + "\n")
PY
  if [[ -f "$backup" ]]; then
    ok "Hermes: enabled plugin $plugin in $config (backup: $backup)"
  else
    ok "Hermes: created config.yaml with plugins.enabled: $plugin"
  fi
}

install_hermes() {
  local src="$INTEGRATIONS/hermes/agency-agents-router"
  local hermes_home; hermes_home="$(hermes_home_dir)"
  local dest; dest="$(resolve_dest hermes "${hermes_home}/plugins/agency-agents-router")"
  [[ -f "$src/plugin.yaml" && -f "$src/__init__.py" && -f "$src/data/agents.json" ]] || {
    err "integrations/hermes/agency-agents-router missing. Run ./scripts/convert.sh --tool hermes first."
    return 1
  }
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  if $USE_LINK; then
    ln -s "$src" "$dest"
  else
    cp -R "$src" "$dest"
  fi
  ensure_hermes_plugin_enabled || warn "Hermes: plugin installed but config.yaml was not updated."
  local count
  count="$(python3 - "$src/data/agents.json" <<'PY'
from pathlib import Path
import json, sys
print(len(json.loads(Path(sys.argv[1]).read_text())))
PY
)"
  ok "Hermes: lazy-router plugin ($count agents on disk) -> $dest"
  warn "Hermes: restart sessions/gateway so the new plugin toolset is discovered."
  if $SELECTION_ACTIVE; then
    warn "Hermes: selection flags ignored; router keeps the full roster on disk and loads agents lazily."
  fi
}

install_tool() {
  ensure_converted "$1"
  case "$1" in
    claude-code) install_claude_code ;;
    copilot)     install_copilot     ;;
    antigravity) install_antigravity ;;
    gemini-cli)  install_gemini_cli  ;;
    opencode)    install_opencode    ;;
    openclaw)    install_openclaw    ;;
    cursor)      install_cursor      ;;
    aider)       install_aider       ;;
    windsurf)    install_windsurf    ;;
    qwen)        install_qwen        ;;
    kimi)        install_kimi        ;;
    codex)       install_codex       ;;
    osaurus)     install_osaurus     ;;
    hermes)      install_hermes      ;;
    vibe)        install_vibe        ;;
  esac
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
main() {
  local tool="all"
  local interactive_mode="auto"
  local use_parallel=false
  local parallel_jobs
  parallel_jobs="$(parallel_jobs_default)"

  local list_what=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool)            tool="${2:?'--tool requires a value'}"; shift 2; interactive_mode="no" ;;
      --division)
        local _d
        IFS=',' read -ra _divs <<< "${2:?'--division requires a value'}"
        for _d in "${_divs[@]}"; do
          _d="$(printf '%s' "$_d" | xargs)"; [[ -z "$_d" ]] && continue
          validate_division "$_d"; FILTER_DIVISIONS+=("$_d")
        done
        interactive_mode="no"; shift 2 ;;
      --agent)
        local _a
        IFS=',' read -ra _ags <<< "${2:?'--agent requires a value'}"
        for _a in "${_ags[@]}"; do
          _a="$(printf '%s' "$_a" | xargs)"; [[ -n "$_a" ]] && FILTER_AGENTS+=("$_a")
        done
        interactive_mode="no"; shift 2 ;;
      --agents-file)     AGENTS_FILE="${2:?'--agents-file requires a value'}"; interactive_mode="no"; shift 2 ;;
      --link)            USE_LINK=true; shift ;;
      --path)            OVERRIDE_PATH="${2:?'--path requires a value'}"; shift 2 ;;
      --no-convert)      AUTO_CONVERT=false; shift ;;
      --dry-run)         DRY_RUN=true; interactive_mode="no"; shift ;;
      --list)            if [[ -z "${2:-}" || "${2:-}" == --* ]]; then list_what="all"; shift; else list_what="$2"; shift 2; fi ;;
      --interactive)     interactive_mode="yes"; shift ;;
      --no-interactive)  interactive_mode="no"; shift ;;
      --parallel)        use_parallel=true; shift ;;
      --jobs)            parallel_jobs="${2:?'--jobs requires a value'}"; shift 2 ;;
      --help|-h)         usage ;;
      *)                 err "Unknown option: $1"; usage ;;
    esac
  done

  [[ -n "$list_what" ]] && { do_list "$list_what"; exit 0; }
  build_selection

  check_integrations

  # Validate explicit tool
  if [[ "$tool" != "all" ]]; then
    local valid=false t
    for t in "${ALL_TOOLS[@]}"; do [[ "$t" == "$tool" ]] && valid=true && break; done
    if ! $valid; then
      err "Unknown tool '$tool'. Valid: ${ALL_TOOLS[*]}"
      exit 1
    fi
  fi

  # Decide whether to show interactive UI
  local use_interactive=false
  if   [[ "$interactive_mode" == "yes" ]]; then
    use_interactive=true
  elif [[ "$interactive_mode" == "auto" && -t 0 && -t 1 && "$tool" == "all" ]]; then
    use_interactive=true
  fi

  SELECTED_TOOLS=()

  if $use_interactive && interactive_wizard; then
    : # wizard committed SELECTED_TOOLS + FILTER_DIVISIONS

  elif [[ "$tool" != "all" ]]; then
    SELECTED_TOOLS=("$tool")

  else
    # Non-interactive (or no TTY): auto-detect
    header "The Agency -- Scanning for installed tools..."
    printf "\n"
    local t
    for t in "${ALL_TOOLS[@]}"; do
      if is_detected "$t" 2>/dev/null; then
        SELECTED_TOOLS+=("$t")
        printf "  ${C_GREEN}[*]${C_RESET}  %s  ${C_DIM}detected${C_RESET}\n" "$(tool_label "$t")"
      else
        printf "  ${C_DIM}[ ]  %s  not found${C_RESET}\n" "$(tool_label "$t")"
      fi
    done
  fi

  if [[ ${#SELECTED_TOOLS[@]} -eq 0 ]]; then
    warn "No tools selected or detected. Nothing to install."
    printf "\n"
    dim "  Tip: use --tool <name> to force-install a specific tool."
    dim "  Available: ${ALL_TOOLS[*]}"
    exit 0
  fi

  # --dry-run: print the plan and exit without writing anything.
  if $DRY_RUN; then
    local agents; agents="$(selected_agent_count)"
    printf "\n"; header "The Agency -- Dry run (nothing written)"
    printf "  Tools:   %s\n" "${SELECTED_TOOLS[*]}"
    if $SELECTION_ACTIVE; then
      [[ ${#FILTER_DIVISIONS[@]} -gt 0 ]] && printf "  Teams:   %s\n" "${FILTER_DIVISIONS[*]}"
      [[ ${#FILTER_AGENTS[@]} -gt 0 ]]    && printf "  Agents:  %s\n" "${FILTER_AGENTS[*]}"
      [[ -n "$AGENTS_FILE" ]]             && printf "  File:    %s\n" "$AGENTS_FILE"
    else
      printf "  Teams:   all (%s)\n" "${#ALL_DIVISIONS[@]}"
    fi
    printf "  Agents:  %s   Mode: %s\n" "$agents" "$($USE_LINK && echo symlink || echo copy)"
    local _t _cap
    for _t in "${SELECTED_TOOLS[@]}"; do
      _cap="$(tool_cap "$_t")"
      [[ "$_cap" -gt 0 && "$agents" -gt "$_cap" ]] && \
        warn "$_t caps ~$_cap — ~$(( agents - _cap )) of $agents won't register (anomalyco/opencode#27988)"
    done
    printf "\n"; exit 0
  fi

  # When parent runs install.sh --parallel, it spawns workers with AGENCY_INSTALL_WORKER=1
  # so each worker only runs install_tool(s) and skips header/done box (avoids duplicate output).
  if [[ -n "${AGENCY_INSTALL_WORKER:-}" ]]; then
    local t
    for t in "${SELECTED_TOOLS[@]}"; do
      install_tool "$t"
    done
    return 0
  fi

  printf "\n"
  header "The Agency -- Installing agents"
  printf "  Repo:       %s\n" "$REPO_ROOT"
  local n_selected=${#SELECTED_TOOLS[@]}
  printf "  Installing: %s\n" "${SELECTED_TOOLS[*]}"
  if $SELECTION_ACTIVE; then
    [[ ${#FILTER_DIVISIONS[@]} -gt 0 ]] && printf "  Teams:      %s\n" "${FILTER_DIVISIONS[*]}"
    printf "  Agents:     %s of %s\n" "$(selected_agent_count)" "$(selected_agent_count_all)"
  fi
  $USE_LINK && printf "  Mode:       ${C_CYAN}symlink${C_RESET} (--link)\n"
  if $use_parallel; then
    ok "Installing $n_selected tools in parallel (output buffered per tool)."
  fi
  printf "\n"

  local installed=0 t i=0
  if $use_parallel; then
    local install_out_dir
    install_out_dir="$(mktemp -d)"
    export AGENCY_INSTALL_OUT_DIR="$install_out_dir"
    export AGENCY_INSTALL_SCRIPT="$SCRIPT_DIR/install.sh"
    export AGENCY_INSTALL_EXTRA="$(worker_flags)"
    printf '%s\n' "${SELECTED_TOOLS[@]}" | xargs -P "$parallel_jobs" -I {} sh -c 'AGENCY_INSTALL_WORKER=1 "$AGENCY_INSTALL_SCRIPT" --tool "{}" --no-interactive $AGENCY_INSTALL_EXTRA > "$AGENCY_INSTALL_OUT_DIR/{}" 2>&1'
    for t in "${SELECTED_TOOLS[@]}"; do
      [[ -f "$install_out_dir/$t" ]] && cat "$install_out_dir/$t"
    done
    rm -rf "$install_out_dir"
    installed=$n_selected
  else
    for t in "${SELECTED_TOOLS[@]}"; do
      (( i++ )) || true
      progress_bar "$i" "$n_selected"
      printf "\n"
      printf "  ${C_DIM}[%s/%s]${C_RESET} %s\n" "$i" "$n_selected" "$t"
      install_tool "$t"
      (( installed++ )) || true
    done
  fi

  # Done box
  local msg="  Done!  Installed $installed tool(s)."
  printf "\n"
  box_top
  box_row "${C_GREEN}${C_BOLD}${msg}${C_RESET}"
  box_bot
  printf "\n"
  dim "  Run ./scripts/convert.sh to regenerate after adding or editing agents."
  printf "\n"
}

main "$@"
