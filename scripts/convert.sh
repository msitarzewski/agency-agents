#!/usr/bin/env bash
#
# convert.sh — Convert agency agent .md files into tool-specific formats.
#
# Reads all agent files from the standard category directories and outputs
# converted files to integrations/<tool>/. Run this to regenerate all
# integration files after adding or modifying agents.
#
# Usage:
#   ./scripts/convert.sh [--tool <name>] [--out <dir>] [--parallel] [--jobs N] [--help]
#
# Tools:
#   antigravity  — Antigravity skill files (~/.gemini/antigravity/skills/)
#   gemini-cli   — Gemini CLI extension (skills/ + gemini-extension.json)
#   opencode     — OpenCode agent files (.opencode/agents/*.md)
#   cursor       — Cursor rule files (.cursor/rules/*.mdc)
#   aider        — Single CONVENTIONS.md for Aider
#   windsurf     — Single .windsurfrules for Windsurf
#   openclaw     — OpenClaw workspaces (integrations/openclaw/<agent>/SOUL.md)
#   qwen         — Qwen Code SubAgent files (~/.qwen/agents/*.md)
#   kimi         — Kimi Code CLI agent files (~/.config/kimi/agents/)
#   all          — All tools (default)
#
# Output is written to integrations/<tool>/ relative to the repo root.
# This script never touches user config dirs — see install.sh for that.
#
#   --parallel       When tool is 'all', run independent tools in parallel (output order may vary).
#   --jobs N         Max parallel jobs when using --parallel (default: nproc or 4).

set -euo pipefail

# --- Colour helpers ---
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; RESET=''
fi

info()    { printf "${GREEN}[OK]${RESET}  %s\n" "$*"; }
warn()    { printf "${YELLOW}[!!]${RESET}  %s\n" "$*"; }
error()   { printf "${RED}[ERR]${RESET} %s\n" "$*" >&2; }
header()  { echo -e "\n${BOLD}$*${RESET}"; }

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

# --- Paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$REPO_ROOT/integrations"
TODAY="$(date +%Y-%m-%d)"

AGENT_DIRS=(
  academic design engineering finance game-development marketing paid-media product project-management
  sales spatial-computing specialized strategy support testing
)

# --- Usage ---
usage() {
  sed -n '3,26p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# Default parallel job count (nproc on Linux; sysctl on macOS when nproc missing)
parallel_jobs_default() {
  local n
  n=$(nproc 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  n=$(sysctl -n hw.ncpu 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  echo 4
}

# --- Frontmatter helpers ---

# Extract a single field value from YAML frontmatter block.
# Usage: get_field <field> <file>
get_field() {
  local field="$1" file="$2"
  awk -v f="$field" '
    /^---$/ { fm++; next }
    fm == 1 && $0 ~ "^" f ": " { sub("^" f ": ", ""); print; exit }
  ' "$file"
}

# Strip the leading frontmatter block and return only the body.
# Usage: get_body <file>
get_body() {
  awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$1"
}

# Convert a human-readable agent name to a lowercase kebab-case slug.
# "Frontend Developer" → "frontend-developer"
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//'
}

# --- Per-tool converters ---

convert_antigravity() {
  local file="$1"
  local name description slug outdir outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="agency-$(slugify "$name")"
  body="$(get_body "$file")"

  outdir="$OUT_DIR/antigravity/$slug"
  outfile="$outdir/SKILL.md"
  mkdir -p "$outdir"

  # Antigravity SKILL.md format mirrors community skills in ~/.gemini/antigravity/skills/
  cat > "$outfile" <<HEREDOC
---
name: ${slug}
description: ${description}
risk: low
source: community
date_added: '${TODAY}'
---
${body}
HEREDOC
}

convert_gemini_cli() {
  local file="$1"
  local name description slug outdir outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outdir="$OUT_DIR/gemini-cli/skills/$slug"
  outfile="$outdir/SKILL.md"
  mkdir -p "$outdir"

  # Gemini CLI skill format: minimal frontmatter (name + description only)
  cat > "$outfile" <<HEREDOC
---
name: ${slug}
description: ${description}
---
${body}
HEREDOC
}

# Map known color names and normalize to OpenCode-safe #RRGGBB values.
resolve_opencode_color() {
  local c="$1"
  local mapped

  c="$(printf '%s' "$c" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr '[:upper:]' '[:lower:]')"

  case "$c" in
    cyan)           mapped="#00FFFF" ;;
    blue)           mapped="#3498DB" ;;
    green)          mapped="#2ECC71" ;;
    red)            mapped="#E74C3C" ;;
    purple)         mapped="#9B59B6" ;;
    orange)         mapped="#F39C12" ;;
    teal)           mapped="#008080" ;;
    indigo)         mapped="#6366F1" ;;
    pink)           mapped="#E84393" ;;
    gold)           mapped="#EAB308" ;;
    amber)          mapped="#F59E0B" ;;
    neon-green)     mapped="#10B981" ;;
    neon-cyan)      mapped="#06B6D4" ;;
    metallic-blue)  mapped="#3B82F6" ;;
    yellow)         mapped="#EAB308" ;;
    violet)         mapped="#8B5CF6" ;;
    rose)           mapped="#F43F5E" ;;
    lime)           mapped="#84CC16" ;;
    gray)           mapped="#6B7280" ;;
    fuchsia)        mapped="#D946EF" ;;
    *)              mapped="$c" ;;
  esac

  if [[ "$mapped" =~ ^#[0-9a-fA-F]{6}$ ]]; then
    printf '#%s\n' "$(printf '%s' "${mapped#\#}" | tr '[:lower:]' '[:upper:]')"
    return
  fi

  if [[ "$mapped" =~ ^[0-9a-fA-F]{6}$ ]]; then
    printf '#%s\n' "$(printf '%s' "$mapped" | tr '[:lower:]' '[:upper:]')"
    return
  fi

  printf '#6B7280\n'
}

convert_opencode() {
  local file="$1"
  local name description color slug outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  color="$(resolve_opencode_color "$(get_field "color" "$file")")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outfile="$OUT_DIR/opencode/agents/${slug}.md"
  mkdir -p "$OUT_DIR/opencode/agents"

  # OpenCode agent format: .md with YAML frontmatter in .opencode/agents/.
  # Named colors are resolved to hex via resolve_opencode_color().
  cat > "$outfile" <<HEREDOC
---
name: ${name}
description: ${description}
mode: subagent
color: '${color}'
---
${body}
HEREDOC
}

convert_cursor() {
  local file="$1"
  local name description slug outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outfile="$OUT_DIR/cursor/rules/${slug}.mdc"
  mkdir -p "$OUT_DIR/cursor/rules"

  # Cursor .mdc format: description + globs + alwaysApply frontmatter
  cat > "$outfile" <<HEREDOC
---
description: ${description}
globs: ""
alwaysApply: false
---
${body}
HEREDOC
}

convert_openclaw() {
  local file="$1"
  local name description slug outdir body
  local soul_content="" agents_content=""

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outdir="$OUT_DIR/openclaw/$slug"
  mkdir -p "$outdir"

  # Split body sections into SOUL.md (persona) vs AGENTS.md (operations)
  # by matching ## header keywords. Unmatched sections go to AGENTS.md.
  #
  # SOUL keywords: identity, learning & memory, communication, style,
  #   critical rules, rules you must follow
  # AGENTS keywords: everything else (mission, deliverables, workflow, etc.)

  local current_target="agents"  # default bucket
  local current_section=""

  while IFS= read -r line; do
    # Detect ## headers (with or without emoji prefixes)
    if [[ "$line" =~ ^##[[:space:]] ]]; then
      # Flush previous section
      if [[ -n "$current_section" ]]; then
        if [[ "$current_target" == "soul" ]]; then
          soul_content+="$current_section"
        else
          agents_content+="$current_section"
        fi
      fi
      current_section=""

      # Classify this header by keyword (case-insensitive)
      local header_lower
      header_lower="$(echo "$line" | tr '[:upper:]' '[:lower:]')"

      if [[ "$header_lower" =~ identity ]] ||
         [[ "$header_lower" =~ learning.*memory ]] ||
         [[ "$header_lower" =~ communication ]] ||
         [[ "$header_lower" =~ style ]] ||
         [[ "$header_lower" =~ critical.rule ]] ||
         [[ "$header_lower" =~ rules.you.must.follow ]]; then
        current_target="soul"
      else
        current_target="agents"
      fi
    fi

    current_section+="$line"$'\n'
  done <<< "$body"

  # Flush final section
  if [[ -n "$current_section" ]]; then
    if [[ "$current_target" == "soul" ]]; then
      soul_content+="$current_section"
    else
      agents_content+="$current_section"
    fi
  fi

  # Write SOUL.md — persona, tone, boundaries
  cat > "$outdir/SOUL.md" <<HEREDOC
${soul_content}
HEREDOC

  # Write AGENTS.md — mission, deliverables, workflow
  cat > "$outdir/AGENTS.md" <<HEREDOC
${agents_content}
HEREDOC

  # Write IDENTITY.md — emoji + name + vibe from frontmatter, fallback to description
  local emoji vibe
  emoji="$(get_field "emoji" "$file")"
  vibe="$(get_field "vibe" "$file")"

  if [[ -n "$emoji" && -n "$vibe" ]]; then
    cat > "$outdir/IDENTITY.md" <<HEREDOC
# ${emoji} ${name}
${vibe}
HEREDOC
  else
    cat > "$outdir/IDENTITY.md" <<HEREDOC
# ${name}
${description}
HEREDOC
  fi
}

convert_qwen() {
  local file="$1"
  local name description tools slug outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  tools="$(get_field "tools" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outfile="$OUT_DIR/qwen/agents/${slug}.md"
  mkdir -p "$(dirname "$outfile")"

  # Qwen Code SubAgent format: .md with YAML frontmatter in ~/.qwen/agents/
  # name and description required; tools optional (only if present in source)
  if [[ -n "$tools" ]]; then
    cat > "$outfile" <<HEREDOC
---
name: ${slug}
description: ${description}
tools: ${tools}
---
${body}
HEREDOC
  else
    cat > "$outfile" <<HEREDOC
---
name: ${slug}
description: ${description}
---
${body}
HEREDOC
  fi
}

convert_kimi() {
  local file="$1"
  local name description slug outdir agent_file body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outdir="$OUT_DIR/kimi/$slug"
  agent_file="$outdir/agent.yaml"
  mkdir -p "$outdir"

  # Kimi Code CLI agent format: YAML with separate system prompt file
  # Uses extend: default to inherit Kimi's default toolset
  cat > "$agent_file" <<HEREDOC
version: 1
agent:
  name: ${slug}
  extend: default
  system_prompt_path: ./system.md
HEREDOC

  # Write system prompt to separate file
  cat > "$outdir/system.md" <<HEREDOC
# ${name}

${description}

${body}
HEREDOC
}

# Aider and Windsurf are single-file formats — accumulate into temp files
# then write at the end.
AIDER_TMP="$(mktemp)"
WINDSURF_TMP="$(mktemp)"
trap 'rm -f "$AIDER_TMP" "$WINDSURF_TMP"' EXIT

# Write Aider/Windsurf headers once
cat > "$AIDER_TMP" <<'HEREDOC'
# The Agency — AI Agent Conventions
#
# This file provides Aider with the full roster of specialized AI agents from
# The Agency (https://github.com/msitarzewski/agency-agents).
#
# To activate an agent, reference it by name in your Aider session prompt, e.g.:
#   "Use the Frontend Developer agent to review this component."
#
# Generated by scripts/convert.sh — do not edit manually.

HEREDOC

cat > "$WINDSURF_TMP" <<'HEREDOC'
# The Agency — AI Agent Rules for Windsurf
#
# Full roster of specialized AI agents from The Agency.
# To activate an agent, reference it by name in your Windsurf conversation.
#
# Generated by scripts/convert.sh — do not edit manually.

HEREDOC

accumulate_aider() {
  local file="$1"
  local name description body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  body="$(get_body "$file")"

  cat >> "$AIDER_TMP" <<HEREDOC

---

## ${name}

> ${description}

${body}
HEREDOC
}

accumulate_windsurf() {
  local file="$1"
  local name description body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  body="$(get_body "$file")"

  cat >> "$WINDSURF_TMP" <<HEREDOC

================================================================================
## ${name}
${description}
================================================================================

${body}

HEREDOC
}

# --- Main loop ---

run_conversions() {
  local tool="$1"
  local count=0

  for dir in "${AGENT_DIRS[@]}"; do
    local dirpath="$REPO_ROOT/$dir"
    [[ -d "$dirpath" ]] || continue

    while IFS= read -r -d '' file; do
      # Skip files without frontmatter (non-agent docs like QUICKSTART.md)
      local first_line
      first_line="$(head -1 "$file")"
      [[ "$first_line" == "---" ]] || continue

      local name
      name="$(get_field "name" "$file")"
      [[ -n "$name" ]] || continue

      case "$tool" in
        antigravity) convert_antigravity "$file" ;;
        gemini-cli)  convert_gemini_cli  "$file" ;;
        opencode)    convert_opencode    "$file" ;;
        cursor)      convert_cursor      "$file" ;;
        openclaw)    convert_openclaw    "$file" ;;
        qwen)        convert_qwen        "$file" ;;
        kimi)        convert_kimi        "$file" ;;
        aider)       accumulate_aider    "$file" ;;
        windsurf)    accumulate_windsurf "$file" ;;
      esac

      (( count++ )) || true
    done < <(find "$dirpath" -name "*.md" -type f -print0 | sort -z)
  done

  echo "$count"
}

# --- Entry point ---

main() {
  local tool="all"
  local use_parallel=false
  local parallel_jobs
  parallel_jobs="$(parallel_jobs_default)"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool)     tool="${2:?'--tool requires a value'}"; shift 2 ;;
      --out)      OUT_DIR="${2:?'--out requires a value'}"; shift 2 ;;
      --parallel) use_parallel=true; shift ;;
      --jobs)     parallel_jobs="${2:?'--jobs requires a value'}"; shift 2 ;;
      --help|-h)  usage ;;
      *)          error "Unknown option: $1"; usage ;;
    esac
  done

  local valid_tools=("antigravity" "gemini-cli" "opencode" "cursor" "aider" "windsurf" "openclaw" "qwen" "kimi" "all")
  local valid=false
  for t in "${valid_tools[@]}"; do [[ "$t" == "$tool" ]] && valid=true && break; done
  if ! $valid; then
    error "Unknown tool '$tool'. Valid: ${valid_tools[*]}"
    exit 1
  fi

  header "The Agency -- Converting agents to tool-specific formats"
  echo "  Repo:   $REPO_ROOT"
  echo "  Output: $OUT_DIR"
  echo "  Tool:   $tool"
  echo "  Date:   $TODAY"
  if $use_parallel && [[ "$tool" == "all" ]]; then
    info "Parallel mode: output buffered so each tool's output stays together."
  fi

  local tools_to_run=()
  if [[ "$tool" == "all" ]]; then
    tools_to_run=("antigravity" "gemini-cli" "opencode" "cursor" "aider" "windsurf" "openclaw" "qwen" "kimi")
  else
    tools_to_run=("$tool")
  fi

  local total=0

  local n_tools=${#tools_to_run[@]}

  if $use_parallel && [[ "$tool" == "all" ]]; then
    # Tools that write to separate dirs can run in parallel; buffer output so each tool's output stays together
    local parallel_tools=(antigravity gemini-cli opencode cursor openclaw qwen)
    local parallel_out_dir
    parallel_out_dir="$(mktemp -d)"
    info "Converting: ${#parallel_tools[@]}/${n_tools} tools in parallel (output buffered per tool)..."
    export AGENCY_CONVERT_OUT_DIR="$parallel_out_dir"
    export AGENCY_CONVERT_SCRIPT="$SCRIPT_DIR/convert.sh"
    export AGENCY_CONVERT_OUT="$OUT_DIR"
    printf '%s\n' "${parallel_tools[@]}" | xargs -P "$parallel_jobs" -I {} sh -c '"$AGENCY_CONVERT_SCRIPT" --tool "{}" --out "$AGENCY_CONVERT_OUT" > "$AGENCY_CONVERT_OUT_DIR/{}" 2>&1'
    for t in "${parallel_tools[@]}"; do
      [[ -f "$parallel_out_dir/$t" ]] && cat "$parallel_out_dir/$t"
    done
    rm -rf "$parallel_out_dir"
    local idx=7
    for t in aider windsurf; do
      progress_bar "$idx" "$n_tools"
      printf "\n"
      header "Converting: $t ($idx/$n_tools)"
      local count
      count="$(run_conversions "$t")"
      total=$(( total + count ))
      info "Converted $count agents for $t"
      (( idx++ )) || true
    done
  else
    local i=0
    for t in "${tools_to_run[@]}"; do
      (( i++ )) || true
      progress_bar "$i" "$n_tools"
      printf "\n"
      header "Converting: $t ($i/$n_tools)"
      local count
      count="$(run_conversions "$t")"
      total=$(( total + count ))

      # Gemini CLI also needs the extension manifest (written by this process when --tool gemini-cli)
      if [[ "$t" == "gemini-cli" ]]; then
        mkdir -p "$OUT_DIR/gemini-cli"
        cat > "$OUT_DIR/gemini-cli/gemini-extension.json" <<'HEREDOC'
{
  "name": "agency-agents",
  "version": "1.0.0"
}
HEREDOC
        info "Wrote gemini-extension.json"
      fi

      info "Converted $count agents for $t"
    done
  fi

  # Write single-file outputs after accumulation
  if [[ "$tool" == "all" || "$tool" == "aider" ]]; then
    mkdir -p "$OUT_DIR/aider"
    cp "$AIDER_TMP" "$OUT_DIR/aider/CONVENTIONS.md"
    info "Wrote integrations/aider/CONVENTIONS.md"
  fi
  if [[ "$tool" == "all" || "$tool" == "windsurf" ]]; then
    mkdir -p "$OUT_DIR/windsurf"
    cp "$WINDSURF_TMP" "$OUT_DIR/windsurf/.windsurfrules"
    info "Wrote integrations/windsurf/.windsurfrules"
  fi

  echo ""
  if $use_parallel && [[ "$tool" == "all" ]]; then
    info "Done. $n_tools tools (parallel; total conversions not aggregated)."
  else
    info "Done. Total conversions: $total"
  fi
}

main "$@"
