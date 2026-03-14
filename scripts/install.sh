#!/usr/bin/env bash
#
# install.sh -- Install The Agency agents into your local agentic tool(s).
#
# Reads converted files from integrations/ and copies them to the appropriate
# config directory for each tool. Run scripts/convert.sh first if integrations/
# is missing or stale.
#
# Usage:
#   ./scripts/install.sh [--tool <name>] [--interactive] [--no-interactive] [--help]
#
# Tools:
#   claude-code  -- Copy agents to ~/.claude/agents/
#   copilot      -- Copy agents to ~/.github/agents/ and ~/.copilot/agents/
#   antigravity  -- Copy skills to ~/.gemini/antigravity/skills/
#   gemini-cli   -- Install extension to ~/.gemini/extensions/agency-agents/
#   opencode     -- Copy agents to .opencode/agent/ in current directory
#   cursor       -- Copy rules to .cursor/rules/ in current directory
#   aider        -- Copy CONVENTIONS.md to current directory
#   windsurf     -- Copy .windsurfrules to current directory
#   openclaw     -- Copy workspaces to ~/.openclaw/agency-agents/
#   qwen         -- Copy SubAgents to ~/.qwen/agents/ (user-wide) or .qwen/agents/ (project)
#   all          -- Install for all detected tools (default)
#
# Flags:
#   --tool <name>     Install only the specified tool
#   --interactive     Show interactive selector (default when run in a terminal)
#   --no-interactive  Skip interactive selector, install all detected tools
#   --help            Show this help
#
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

ALL_TOOLS=(claude-code copilot antigravity gemini-cli opencode openclaw cursor aider windsurf qwen kimi)

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
  sed -n '3,28p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
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
detect_antigravity()  { [[ -d "${HOME}/.gemini/antigravity/skills" ]]; }
detect_gemini_cli()   { command -v gemini >/dev/null 2>&1 || [[ -d "${HOME}/.gemini" ]]; }
detect_cursor()       { command -v cursor >/dev/null 2>&1 || [[ -d "${HOME}/.cursor" ]]; }
detect_opencode()     { command -v opencode >/dev/null 2>&1 || [[ -d "${HOME}/.config/opencode" ]]; }
detect_aider()        { command -v aider >/dev/null 2>&1; }
detect_openclaw()     { command -v openclaw >/dev/null 2>&1 || [[ -d "${HOME}/.openclaw" ]]; }
detect_windsurf()     { command -v windsurf >/dev/null 2>&1 || [[ -d "${HOME}/.codeium" ]]; }
detect_qwen()         { command -v qwen >/dev/null 2>&1 || [[ -d "${HOME}/.qwen" ]]; }
detect_kimi()         { command -v kimi >/dev/null 2>&1; }

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
    *)           return 1 ;;
  esac
}

# Fixed-width labels: name (14) + detail (24) = 38 visible chars
tool_label() {
  case "$1" in
    claude-code) printf "%-14s  %s" "Claude Code"  "(claude.ai/code)"        ;;
    copilot)     printf "%-14s  %s" "Copilot"      "(~/.github + ~/.copilot)" ;;
    antigravity) printf "%-14s  %s" "Antigravity"  "(~/.gemini/antigravity)" ;;
    gemini-cli)  printf "%-14s  %s" "Gemini CLI"   "(gemini extension)"      ;;
    opencode)    printf "%-14s  %s" "OpenCode"     "(opencode.ai)"           ;;
    openclaw)    printf "%-14s  %s" "OpenClaw"     "(~/.openclaw)"           ;;
    cursor)      printf "%-14s  %s" "Cursor"       "(.cursor/rules)"         ;;
    aider)       printf "%-14s  %s" "Aider"        "(CONVENTIONS.md)"        ;;
    windsurf)    printf "%-14s  %s" "Windsurf"     "(.windsurfrules)"        ;;
    qwen)        printf "%-14s  %s" "Qwen Code"    "(~/.qwen/agents)"        ;;
    kimi)        printf "%-14s  %s" "Kimi Code"    "(~/.config/kimi/agents)" ;;
  esac
}

# ---------------------------------------------------------------------------
# Interactive selector
# ---------------------------------------------------------------------------
interactive_select() {
  # bash 3-compatible arrays
  declare -a selected=()
  declare -a detected_map=()

  local t
  for t in "${ALL_TOOLS[@]}"; do
    if is_detected "$t" 2>/dev/null; then
      selected+=(1); detected_map+=(1)
    else
      selected+=(0); detected_map+=(0)
    fi
  done

  while true; do
    # --- header ---
    printf "\n"
    box_top
    box_row "${C_BOLD}  The Agency -- Tool Installer${C_RESET}"
    box_bot
    printf "\n"
    printf "  ${C_DIM}System scan:  [*] = detected on this machine${C_RESET}\n"
    printf "\n"

    # --- tool rows ---
    local i=0
    for t in "${ALL_TOOLS[@]}"; do
      local num=$(( i + 1 ))
      local label
      label="$(tool_label "$t")"
      local dot
      if [[ "${detected_map[$i]}" == "1" ]]; then
        dot="${C_GREEN}[*]${C_RESET}"
      else
        dot="${C_DIM}[ ]${C_RESET}"
      fi
      local chk
      if [[ "${selected[$i]}" == "1" ]]; then
        chk="${C_GREEN}[x]${C_RESET}"
      else
        chk="${C_DIM}[ ]${C_RESET}"
      fi
      printf "  %s  %s)  %s  %s\n" "$chk" "$num" "$dot" "$label"
      (( i++ )) || true
    done

    # --- controls ---
    printf "\n"
    printf "  ------------------------------------------------\n"
    printf "  ${C_CYAN}[1-%s]${C_RESET} toggle   ${C_CYAN}[a]${C_RESET} all   ${C_CYAN}[n]${C_RESET} none   ${C_CYAN}[d]${C_RESET} detected\n" "${#ALL_TOOLS[@]}"
    printf "  ${C_GREEN}[Enter]${C_RESET} install   ${C_RED}[q]${C_RESET} quit\n"
    printf "\n"
    printf "  >> "
    read -r input </dev/tty

    case "$input" in
      q|Q)
        printf "\n"; ok "Aborted."; exit 0 ;;
      a|A)
        for (( j=0; j<${#ALL_TOOLS[@]}; j++ )); do selected[$j]=1; done ;;
      n|N)
        for (( j=0; j<${#ALL_TOOLS[@]}; j++ )); do selected[$j]=0; done ;;
      d|D)
        for (( j=0; j<${#ALL_TOOLS[@]}; j++ )); do selected[$j]="${detected_map[$j]}"; done ;;
      "")
        local any=false
        local s
        for s in "${selected[@]}"; do [[ "$s" == "1" ]] && any=true && break; done
        if $any; then
          break
        else
          printf "  ${C_YELLOW}Nothing selected -- pick a tool or press q to quit.${C_RESET}\n"
          sleep 1
        fi ;;
      *)
        local toggled=false
        local num
        for num in $input; do
          if [[ "$num" =~ ^[0-9]+$ ]]; then
            local idx=$(( num - 1 ))
            if (( idx >= 0 && idx < ${#ALL_TOOLS[@]} )); then
              if [[ "${selected[$idx]}" == "1" ]]; then
                selected[$idx]=0
              else
                selected[$idx]=1
              fi
              toggled=true
            fi
          fi
        done
        if ! $toggled; then
          printf "  ${C_RED}Invalid. Enter a number 1-%s, or a command.${C_RESET}\n" "${#ALL_TOOLS[@]}"
          sleep 1
        fi ;;
    esac

    # Clear UI for redraw
    local lines=$(( ${#ALL_TOOLS[@]} + 14 ))
    local l
    for (( l=0; l<lines; l++ )); do printf '\033[1A\033[2K'; done
  done

  # Build output array
  SELECTED_TOOLS=()
  local i=0
  for t in "${ALL_TOOLS[@]}"; do
    [[ "${selected[$i]}" == "1" ]] && SELECTED_TOOLS+=("$t")
    (( i++ )) || true
  done
}

# ---------------------------------------------------------------------------
# Installers
# ---------------------------------------------------------------------------

install_claude_code() {
  local dest="${HOME}/.claude/agents"
  local count=0
  mkdir -p "$dest"
  local dir f first_line
  for dir in design engineering game-development marketing paid-media sales product project-management \
              testing support spatial-computing specialized; do
    [[ -d "$REPO_ROOT/$dir" ]] || continue
    while IFS= read -r -d '' f; do
      first_line="$(head -1 "$f")"
      [[ "$first_line" == "---" ]] || continue
      cp "$f" "$dest/"
      (( count++ )) || true
    done < <(find "$REPO_ROOT/$dir" -name "*.md" -type f -print0)
  done
  ok "Claude Code: $count agents -> $dest"
}

install_copilot() {
  local dest_github="${HOME}/.github/agents"
  local dest_copilot="${HOME}/.copilot/agents"
  local count=0
  mkdir -p "$dest_github" "$dest_copilot"
  local dir f first_line
  for dir in design engineering game-development marketing paid-media sales product project-management \
              testing support spatial-computing specialized; do
    [[ -d "$REPO_ROOT/$dir" ]] || continue
    while IFS= read -r -d '' f; do
      first_line="$(head -1 "$f")"
      [[ "$first_line" == "---" ]] || continue
      cp "$f" "$dest_github/"
      cp "$f" "$dest_copilot/"
      (( count++ )) || true
    done < <(find "$REPO_ROOT/$dir" -name "*.md" -type f -print0)
  done
  ok "Copilot: $count agents -> $dest_github"
  ok "Copilot: $count agents -> $dest_copilot"
}

install_antigravity() {
  local src="$INTEGRATIONS/antigravity"
  local dest="${HOME}/.gemini/antigravity/skills"
  local count=0
  [[ -d "$src" ]] || { err "integrations/antigravity missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    mkdir -p "$dest/$name"
    cp "$d/SKILL.md" "$dest/$name/SKILL.md"
    (( count++ )) || true
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)
  ok "Antigravity: $count skills -> $dest"
}

install_gemini_cli() {
  local src="$INTEGRATIONS/gemini-cli"
  local dest="${HOME}/.gemini/extensions/agency-agents"
  local count=0
  local manifest="$src/gemini-extension.json"
  local skills_dir="$src/skills"
  [[ -d "$src" ]] || { err "integrations/gemini-cli missing. Run ./scripts/convert.sh --tool gemini-cli first."; return 1; }
  [[ -f "$manifest" ]] || { err "integrations/gemini-cli/gemini-extension.json missing. Run ./scripts/convert.sh --tool gemini-cli first."; return 1; }
  [[ -d "$skills_dir" ]] || { err "integrations/gemini-cli/skills missing. Run ./scripts/convert.sh --tool gemini-cli first."; return 1; }
  mkdir -p "$dest/skills"
  cp "$manifest" "$dest/gemini-extension.json"
  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    mkdir -p "$dest/skills/$name"
    cp "$d/SKILL.md" "$dest/skills/$name/SKILL.md"
    (( count++ )) || true
  done < <(find "$skills_dir" -mindepth 1 -maxdepth 1 -type d -print0)
  ok "Gemini CLI: $count skills -> $dest"
}

install_opencode() {
  local src="$INTEGRATIONS/opencode/agents"
  local dest="${PWD}/.opencode/agents"
  local count=0
  [[ -d "$src" ]] || { err "integrations/opencode missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local f
  while IFS= read -r -d '' f; do
    cp "$f" "$dest/"; (( count++ )) || true
  done < <(find "$src" -maxdepth 1 -name "*.md" -print0)
  ok "OpenCode: $count agents -> $dest"
  warn "OpenCode: project-scoped. Run from your project root to install there."
}

install_openclaw() {
  local src="$INTEGRATIONS/openclaw"
  local dest="${HOME}/.openclaw/agency-agents"
  local count=0
  [[ -d "$src" ]] || { err "integrations/openclaw missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    mkdir -p "$dest/$name"
    cp "$d/SOUL.md" "$dest/$name/SOUL.md"
    cp "$d/AGENTS.md" "$dest/$name/AGENTS.md"
    cp "$d/IDENTITY.md" "$dest/$name/IDENTITY.md"
    # Register with OpenClaw so agents are usable by agentId immediately
    if command -v openclaw >/dev/null 2>&1; then
      openclaw agents add "$name" --workspace "$dest/$name" --non-interactive || true
    fi
    (( count++ )) || true
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)
  ok "OpenClaw: $count workspaces -> $dest"
  if command -v openclaw >/dev/null 2>&1; then
    warn "OpenClaw: run 'openclaw gateway restart' to activate new agents"
  fi
}

install_cursor() {
  local src="$INTEGRATIONS/cursor/rules"
  local dest="${PWD}/.cursor/rules"
  local count=0
  [[ -d "$src" ]] || { err "integrations/cursor missing. Run convert.sh first."; return 1; }
  mkdir -p "$dest"
  local f
  while IFS= read -r -d '' f; do
    cp "$f" "$dest/"; (( count++ )) || true
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
  cp "$src" "$dest"
  ok "Aider: installed -> $dest"
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
  cp "$src" "$dest"
  ok "Windsurf: installed -> $dest"
  warn "Windsurf: project-scoped. Run from your project root to install there."
}

install_qwen() {
  local src="$INTEGRATIONS/qwen/agents"
  local dest="${PWD}/.qwen/agents"
  local count=0

  [[ -d "$src" ]] || { err "integrations/qwen missing. Run convert.sh first."; return 1; }

  mkdir -p "$dest"

  local f
  while IFS= read -r -d '' f; do
    cp "$f" "$dest/"
    (( count++ )) || true
  done < <(find "$src" -maxdepth 1 -name "*.md" -print0)

  ok "Qwen Code: installed $count agents to $dest"
  warn "Qwen Code: project-scoped. Run from your project root to install there."
  warn "Tip: Run '/agents manage' in Qwen Code to refresh, or restart session"
}

install_kimi() {
  local src="$INTEGRATIONS/kimi"
  local dest="${HOME}/.config/kimi/agents"
  local count=0

  [[ -d "$src" ]] || { err "integrations/kimi missing. Run convert.sh first."; return 1; }

  mkdir -p "$dest"

  local d
  while IFS= read -r -d '' d; do
    local name; name="$(basename "$d")"
    mkdir -p "$dest/$name"
    cp "$d/agent.yaml" "$dest/$name/agent.yaml"
    cp "$d/system.md" "$dest/$name/system.md"
    (( count++ )) || true
  done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)

  ok "Kimi Code: installed $count agents to $dest"
  ok "Usage: kimi --agent-file ~/.config/kimi/agents/<agent-name>/agent.yaml"
}

install_tool() {
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
  esac
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
main() {
  local tool="all"
  local interactive_mode="auto"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool)            tool="${2:?'--tool requires a value'}"; shift 2; interactive_mode="no" ;;
      --interactive)     interactive_mode="yes"; shift ;;
      --no-interactive)  interactive_mode="no"; shift ;;
      --help|-h)         usage ;;
      *)                 err "Unknown option: $1"; usage ;;
    esac
  done

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

  if $use_interactive; then
    interactive_select

  elif [[ "$tool" != "all" ]]; then
    SELECTED_TOOLS=("$tool")

  else
    # Non-interactive: auto-detect
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

  printf "\n"
  header "The Agency -- Installing agents"
  printf "  Repo:       %s\n" "$REPO_ROOT"
  printf "  Installing: %s\n" "${SELECTED_TOOLS[*]}"
  printf "\n"

  local installed=0 t
  for t in "${SELECTED_TOOLS[@]}"; do
    install_tool "$t"
    (( installed++ )) || true
  done

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
