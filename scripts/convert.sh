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
#   antigravity  — Antigravity skill files (~/.gemini/config/skills/)
#   gemini-cli   — Gemini CLI subagent files (~/.gemini/agents/*.md)
#   opencode     — OpenCode agent files (.opencode/agents/*.md)
#   cursor       — Cursor rule files (.cursor/rules/*.mdc)
#   aider        — Single CONVENTIONS.md for Aider
#   windsurf     — Windsurf workspace rules, one per agent (.windsurf/rules/*.md)
#   openclaw     — OpenClaw workspaces (integrations/openclaw/<agent>/SOUL.md)
#   qwen         — Qwen Code SubAgent files (~/.qwen/agents/*.md)
#   zcode        — ZCode agent files (.zcode/agents/*.md · ~/.config/zcode/agents/*.md)
#   kimi         — Kimi Code CLI agent files (~/.config/kimi/agents/)
#   codex        — Codex custom agent TOML files (~/.codex/agents/*.toml)
#   osaurus      — Osaurus skill files (~/.osaurus/skills/<name>/SKILL.md)
#   hermes       — Hermes lazy-router plugin (one plugin + on-disk agent index)
#   vibe         — Mistral Vibe agent TOML + prompt files (~/.vibe/agents/*.toml + ~/.vibe/prompts/*.md)
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

# Shared helpers (get_field, get_body, slugify, ...)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

AGENT_DIRS=(
  academic design engineering finance game-development gis healthcare marketing paid-media product project-management
  research sales security spatial-computing specialized support testing
)

# --- Usage ---
usage() {
  sed -n '3,27p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# Default parallel job count (nproc on Linux; sysctl on macOS when nproc missing)
parallel_jobs_default() {
  local n
  n=$(nproc 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  n=$(sysctl -n hw.ncpu 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  echo 4
}

# --- Frontmatter helpers: get_field / get_body / slugify now live in lib.sh ---

# Escape a value for a TOML basic string, including control characters that
# cannot appear raw in TOML source.
toml_escape_string() {
  printf '%s' "$1" | perl -0pe '
    s/\\/\\\\/g;
    s/"/\\"/g;
    s/\n/\\n/g;
    s/\r/\\r/g;
    s/\t/\\t/g;
    s/\f/\\f/g;
    s/\x08/\\b/g;
    s/([\x00-\x07\x0B\x0E-\x1F\x7F])/sprintf("\\u%04X", ord($1))/ge;
  '
}

# Quote a single-line value for a YAML frontmatter scalar. Single-quoted YAML
# strings keep colons, hashes, backslashes, and Unicode literal, while doubling
# an apostrophe is the only escaping rule required here.
yaml_quote() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/''/g")"
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

  # Antigravity Agent-Skills SKILL.md — name + description frontmatter and the
  # persona as the body, installed into ~/.gemini/config/skills/ (global) or
  # <project>/.agents/skills/ (project). Standard fields only, so it stays a
  # valid Agent-Skills skill for any host (and deterministic — no date stamp).
  cat > "$outfile" <<HEREDOC
---
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
---
${body}
HEREDOC
}

convert_osaurus() {
  local file="$1"
  local name description slug outdir outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="agency-$(slugify "$name")"
  body="$(get_body "$file")"

  # Stage one dir per skill (install.sh copies into ~/.osaurus/skills/<name>/).
  outdir="$OUT_DIR/osaurus/$slug"
  outfile="$outdir/SKILL.md"
  mkdir -p "$outdir"

  # Osaurus skill format: the Anthropic "Agent Skills" SKILL.md — a directory
  # named for the skill containing a SKILL.md with name + description frontmatter
  # and the persona as the instruction body. Installs into ~/.osaurus/skills/.
  # Kept to the standard fields so it stays compatible with any Agent-Skills host.
  cat > "$outfile" <<HEREDOC
---
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
---
${body}
HEREDOC
}

convert_codex() {
  local file="$1"
  local name description slug outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outfile="$OUT_DIR/codex/agents/${slug}.toml"
  mkdir -p "$(dirname "$outfile")"

  # Codex custom agent format: one TOML file per agent with minimal required
  # fields only. Use a TOML basic string so control characters in the source
  # body are encoded safely instead of producing invalid TOML.
  cat > "$outfile" <<HEREDOC
name = "$(toml_escape_string "$name")"
description = "$(toml_escape_string "$description")"
developer_instructions = "$(toml_escape_string "$body")"
HEREDOC
}

convert_gemini_cli() {
  local file="$1"
  local name description slug outdir outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  # Gemini CLI subagent format: .md file in ~/.gemini/agents/
  outdir="$OUT_DIR/gemini-cli/agents"
  outfile="$outdir/${slug}.md"
  mkdir -p "$outdir"

  cat > "$outfile" <<HEREDOC
---
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
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
name: $(yaml_quote "$name")
description: $(yaml_quote "$description")
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
description: $(yaml_quote "$description")
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
  # While fence_marker is set, ## lines are code content, not section
  # boundaries (issue #849). See lib.sh fence_open_p / fence_closes_p.
  local fence_marker="" fence_len=0 fence_indent=0

  while IFS= read -r line; do
    if [[ -n "$fence_marker" ]]; then
      current_section+="$line"$'\n'
      if fence_closes_p "$line" "$fence_marker" "$fence_len" "$fence_indent"; then
        fence_marker=""
        fence_len=0
        fence_indent=0
      fi
      continue
    fi

    if fence_open_p "$line"; then
      fence_marker="${BASH_REMATCH[2]:0:1}"
      fence_len=${#BASH_REMATCH[2]}
      fence_indent=${#BASH_REMATCH[1]}
      current_section+="$line"$'\n'
      continue
    fi

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
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
tools: $(yaml_quote "$tools")
---
${body}
HEREDOC
  else
    cat > "$outfile" <<HEREDOC
---
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
---
${body}
HEREDOC
  fi
}

convert_zcode() {
  local file="$1"
  local name description tools slug outfile body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  tools="$(get_field "tools" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  outfile="$OUT_DIR/zcode/agents/${slug}.md"
  mkdir -p "$(dirname "$outfile")"

  # ZCode agent format (Z.ai GLM harness): .md with YAML frontmatter in
  # .zcode/agents/ (project) or ~/.config/zcode/agents/ (global). name and
  # description required; tools optional (only if present in source). Byte-
  # identical to the qwen-md shape, which the Agency Agents app renders natively.
  if [[ -n "$tools" ]]; then
    cat > "$outfile" <<HEREDOC
---
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
tools: $(yaml_quote "$tools")
---
${body}
HEREDOC
  else
    cat > "$outfile" <<HEREDOC
---
name: $(yaml_quote "$slug")
description: $(yaml_quote "$description")
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

convert_vibe() {
  local file="$1"
  local name description slug outdir agent_file prompt_file body

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"

  # Mistral Vibe uses two files per agent:
  # 1. A TOML configuration file in ~/.vibe/agents/<slug>.toml
  # 2. A markdown prompt file in ~/.vibe/prompts/<slug>.md

  outdir="$OUT_DIR/vibe"
  agent_file="$outdir/agents/${slug}.toml"
  prompt_file="$outdir/prompts/${slug}.md"
  mkdir -p "$outdir/agents" "$outdir/prompts"

  # Write the TOML agent configuration
  cat > "$agent_file" <<HEREDOC
agent_type = "agent"
system_prompt_id = "${slug}"
HEREDOC

  # Write the markdown prompt file
  cat > "$prompt_file" <<HEREDOC
# ${name}

${description}

${body}
HEREDOC
}

# Windsurf reads workspace rules from .windsurf/rules/*.md, one file per rule,
# and caps each at 12,000 characters. 58% of agent bodies are longer than that,
# so a body that does not fit is cut at a "## " boundary and the file says where
# the rest lives. The old single .windsurfrules held every agent end to end —
# 3.9 million characters, of which Windsurf read the first few thousand.
WINDSURF_RULE_LIMIT=12000

# windsurf_trim_body <body> <budget> — the longest prefix of <body> that fits
# <budget>, ending on a clean break rather than mid-sentence.
#
# Breaks are tried coarsest first: a "## " section, then "### ", then a blank
# line. The coarsest one wins as long as it still uses most of the budget —
# some agents put 8000 characters under one heading, and stopping at the
# previous "## " there would throw away three quarters of what fits. If no
# break is good enough, it keeps the most content any of them allows, and
# falls back to the last whole line outside a fence.
#
# Fences are tracked the way the OpenClaw split tracks them (#849): a break
# inside a fenced block is not a break, and cutting there would leave the rule
# holding a dangling ``` that renders as broken markdown.
windsurf_trim_body() {
  printf '%s' "$1" | awk -v budget="$2" '
    { lines[NR] = $0 }
    END {
      total = 0; line_cut = 0; h2 = 0; h3 = 0; para = 0
      fence = ""; flen = 0
      for (i = 1; i <= NR; i++) {
        total += length(lines[i]) + 1
        if (total > budget) break
        used[i] = total
        if (match(lines[i], /^ {0,3}(`{3,}|~{3,})/)) {
          run = substr(lines[i], RSTART, RLENGTH); sub(/^ +/, "", run)
          if (fence == "") { fence = substr(run, 1, 1); flen = length(run) }
          else if (substr(run, 1, 1) == fence && length(run) >= flen) { fence = ""; flen = 0 }
        }
        if (fence != "") continue            # inside a block: no break here
        line_cut = i
        if (lines[i] ~ /^## /)  h2 = i - 1
        if (lines[i] ~ /^### /) h3 = i - 1
        if (lines[i] == "")     para = i - 1
      }
      if (i > NR) { cut = NR }                         # whole body fits
      else {
        floor = budget * 0.7
        cut = 0
        if      (h2   > 0 && used[h2]   >= floor) cut = h2
        else if (h3   > 0 && used[h3]   >= floor) cut = h3
        else if (para > 0 && used[para] >= floor) cut = para
        if (cut == 0) {                                # nothing clean is close
          if (used[para] >= used[h3] && used[para] >= used[h2]) cut = para
          else if (used[h3] >= used[h2])                        cut = h3
          else                                                  cut = h2
        }
        if (cut < 1) cut = line_cut
      }
      for (j = 1; j <= cut; j++) print lines[j]
    }
  '
}

convert_windsurf() {
  local file="$1"
  local name description slug outfile body header footer trimmed source

  name="$(get_field "name" "$file")"
  description="$(get_field "description" "$file")"
  slug="$(slugify "$name")"
  body="$(get_body "$file")"
  source="${file#"$REPO_ROOT"/}"

  outfile="$OUT_DIR/windsurf/rules/${slug}.md"
  mkdir -p "$OUT_DIR/windsurf/rules"

  # trigger: model_decision puts only the description in Cascade's system
  # prompt; it opens the file when the description looks relevant. That is the
  # activation mode a 279-agent roster needs — always_on would mean every
  # specialist in every prompt.
  # Every agent body opens with its own "# <Name>" heading, so the rule file
  # does not add a second one.
  header="---
trigger: model_decision
description: $(yaml_quote "$description")
---
"
  footer="
---
Trimmed to fit Windsurf's ${WINDSURF_RULE_LIMIT}-character rule limit.
Full agent: ${source}"

  trimmed="$(windsurf_trim_body "$body" \
    "$(( WINDSURF_RULE_LIMIT - ${#header} - ${#footer} - 1 ))")"

  if [[ "$trimmed" == "$body" ]]; then
    printf '%s%s\n' "$header" "$body" > "$outfile"
  else
    printf '%s%s%s\n' "$header" "$trimmed" "$footer" > "$outfile"
  fi
}

# Aider is a single-file format — accumulate into a temp file, write at the end.
AIDER_TMP="$(mktemp)"
trap 'rm -f "$AIDER_TMP"' EXIT

# Write the Aider header once
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

# --- Main loop ---

# Remove a tool's previously-generated output before regenerating, so renamed or
# deleted agents don't leave orphan files behind (convert.sh overwrites in place
# but never pruned stale output). Preserves the committed README.md — the only
# tracked file under integrations/<tool>/ for conversion targets.
clean_tool_output() {
  # Defensive: tool names are plain slugs; refuse anything else so a future
  # caller can never steer this rm -rf outside $OUT_DIR via "../" or "/".
  [[ "$1" =~ ^[a-z0-9-]+$ ]] || { echo "ERROR: clean_tool_output: refusing non-slug tool name '$1'" >&2; return 1; }
  local dir="$OUT_DIR/$1"
  [[ -d "$dir" ]] || return 0
  find "$dir" -mindepth 1 -maxdepth 1 ! -name 'README.md' -exec rm -rf {} +
}

run_conversions() {
  local tool="$1"
  local count=0

  if [[ "$tool" == "hermes" ]]; then
    clean_tool_output "$tool"
    python3 "$SCRIPT_DIR/build-hermes-plugin.py" --repo-root "$REPO_ROOT" --out "$OUT_DIR/hermes"
    return
  fi

  clean_tool_output "$tool"

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
        codex)       convert_codex       "$file" ;;
        gemini-cli)  convert_gemini_cli  "$file" ;;
        opencode)    convert_opencode    "$file" ;;
        cursor)      convert_cursor      "$file" ;;
        openclaw)    convert_openclaw    "$file" ;;
        qwen)        convert_qwen        "$file" ;;
        zcode)       convert_zcode       "$file" ;;
        kimi)        convert_kimi        "$file" ;;
        osaurus)     convert_osaurus     "$file" ;;
        vibe)        convert_vibe        "$file" ;;
        aider)       accumulate_aider    "$file" ;;
        windsurf)    convert_windsurf    "$file" ;;
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

  local valid_tools=("antigravity" "gemini-cli" "opencode" "cursor" "aider" "windsurf" "openclaw" "qwen" "zcode" "kimi" "codex" "osaurus" "hermes" "vibe" "all")
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
    tools_to_run=("antigravity" "gemini-cli" "opencode" "cursor" "aider" "windsurf" "openclaw" "qwen" "zcode" "kimi" "codex" "osaurus" "hermes" "vibe")
  else
    tools_to_run=("$tool")
  fi

  local total=0

  local n_tools=${#tools_to_run[@]}

  if $use_parallel && [[ "$tool" == "all" ]]; then
    # Tools that write to separate dirs can run in parallel; buffer output so each tool's output stays together
    local parallel_tools=(antigravity gemini-cli opencode cursor openclaw qwen zcode kimi codex osaurus hermes vibe windsurf)
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
    local idx=$(( ${#parallel_tools[@]} + 1 ))
    for t in aider; do
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
      info "Converted $count agents for $t"
    done
  fi

  # Write the single-file output after accumulation
  if [[ "$tool" == "all" || "$tool" == "aider" ]]; then
    mkdir -p "$OUT_DIR/aider"
    cp "$AIDER_TMP" "$OUT_DIR/aider/CONVENTIONS.md"
    info "Wrote integrations/aider/CONVENTIONS.md"
  fi

  echo ""
  if $use_parallel && [[ "$tool" == "all" ]]; then
    info "Done. $n_tools tools (parallel; total conversions not aggregated)."
  else
    info "Done. Total conversions: $total"
  fi
}

main "$@"
