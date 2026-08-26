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
#   cursor       — Cursor full config pack (agents + thin router + optional skills/commands/catalog)
#   aider        — Single CONVENTIONS.md for Aider
#   windsurf     — Single .windsurfrules for Windsurf
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
  sales security spatial-computing specialized support testing
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
name: ${slug}
description: ${description}
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
name: ${slug}
description: ${description}
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

# ---------------------------------------------------------------------------
# Cursor pack converters (subagent-first)
#
# Sources: division Claude agent *.md only (AGENT_DIRS). NEVER convert from
# .mdc or integrations/cursor/rules/. Deterministic heading trim (no LLM).
# Subagent emit: name, description (WHAT+WHEN), model: inherit. Drop color.
# Optional vibe → Identity bullet. Skills when oversized / template-heavy.
# Only always-on rule: agency-router.mdc (written in cursor_finalize).
# Size targets: subagent ≤150 preferred (warn >150); skill SKILL.md ≤200;
# router ≤60; AGENTS Agency section ≤80.
# ---------------------------------------------------------------------------

# cursor_classify_header <## line> — bucket: identity|mission|rules|workflow|deliverables|cut|default
cursor_classify_header() {
  local header_lower
  header_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  # Strip common emoji / non-ascii noise for keyword match
  header_lower="$(printf '%s' "$header_lower" | sed 's/[^a-z0-9 &/\-]//g')"

  # Only ## headers are classified; # titles are handled as preamble.
  if [[ "$header_lower" =~ learning ]]; then
    printf 'cut'
  elif [[ "$header_lower" =~ identity ]] ||
       [[ "$header_lower" =~ personality ]] ||
       [[ "$header_lower" =~ memory ]] ||
       [[ "$header_lower" =~ communication ]] ||
       [[ "$header_lower" =~ style ]]; then
    printf 'identity'
  elif [[ "$header_lower" =~ core[[:space:]]*mission ]] ||
       [[ "$header_lower" =~ mission ]]; then
    printf 'mission'
  elif [[ "$header_lower" =~ critical[[:space:]]*rule ]] ||
       [[ "$header_lower" =~ rules[[:space:]]*you[[:space:]]*must[[:space:]]*follow ]] ||
       [[ "$header_lower" =~ critical[[:space:]]*rules ]]; then
    printf 'rules'
  elif [[ "$header_lower" =~ workflow ]] ||
       [[ "$header_lower" =~ process ]]; then
    printf 'workflow'
  elif [[ "$header_lower" =~ technical[[:space:]]*deliverable ]] ||
       [[ "$header_lower" =~ deliverable ]] ||
       [[ "$header_lower" =~ example ]]; then
    printf 'deliverables'
  elif [[ "$header_lower" =~ success[[:space:]]*metric ]] ||
       [[ "$header_lower" =~ advanced ]] ||
       [[ "$header_lower" =~ instructions[[:space:]]*reference ]]; then
    printf 'cut'
  else
    printf 'default'
  fi
}

# cursor_enrich_description <desc> <name> — append Use when… if missing (deterministic).
cursor_enrich_description() {
  local desc="$1" name="$2" lower
  lower="$(printf '%s' "$desc" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower" =~ use[[:space:]]+when ]]; then
    printf '%s' "$desc"
  else
    printf '%s Use when the user needs %s expertise or related tasks.' "$desc" "$name"
  fi
}

# cursor_yaml_escape <string> — single-line YAML double-quoted value.
cursor_yaml_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/ /g' | tr '\n' ' ' | sed 's/  */ /g; s/^ //; s/ $//'
}

# cursor_division_of <file> — basename of parent dir under REPO_ROOT.
cursor_division_of() {
  local file="$1" rel parent
  rel="${file#$REPO_ROOT/}"
  parent="${rel%%/*}"
  printf '%s' "$parent"
}

# cursor_trim_body <body_file> <agent_out> <skill_out> <ref_out> <need_out>
# Single-pass awk trim (fast on Git Bash / Windows). Same classifier as
# cursor_classify_header. Writes agent/skill/ref files; need_out is 0|1.
cursor_trim_body() {
  local body_file="$1" agent_out="$2" skill_out="$3" ref_out="$4" need_out="$5"
  local meta agent_lines need=0
  meta="$(awk -v agent_out="$agent_out" -v skill_out="$skill_out" -v ref_out="$ref_out" '
    function classify(h,   x) {
      x = tolower(h)
      gsub(/[^a-z0-9 &\/-]/, "", x)
      if (x ~ /learning/) return "cut"
      if (x ~ /identity/ || x ~ /personality/ || x ~ /memory/ || x ~ /communication/ || x ~ /style/) return "identity"
      if (x ~ /mission/) return "mission"
      if (x ~ /critical[[:space:]]*rule/ || x ~ /rules[[:space:]]*you[[:space:]]*must[[:space:]]*follow/) return "rules"
      if (x ~ /workflow/ || x ~ /process/) return "workflow"
      if (x ~ /deliverable/ || x ~ /example/) return "deliverables"
      if (x ~ /success[[:space:]]*metric/ || x ~ /advanced/ || x ~ /instructions[[:space:]]*reference/) return "cut"
      return "default"
    }
    function is_bullet(l) { return l ~ /^[[:space:]]*[-*][[:space:]]/ }
    function is_step(l) {
      return (l ~ /^###/ || is_bullet(l) || l ~ /^[[:space:]]*[0-9]+\.[[:space:]]/)
    }
    function flush(    i, n, steps, bullets, line) {
      n = sec_n
      if (n < 1) return
      if (bucket == "preamble") {
        for (i = 1; i <= n; i++) {
          line = sec[i]
          if (line ~ /^#/ || line ~ /^[[:space:]]*$/) continue
          print line >> agent_out
          preamble_kept++
          if (preamble_kept >= 4) break
        }
        if (preamble_kept > 0) print "" >> agent_out
        return
      }
      if (bucket == "identity") {
        print sec[1] >> agent_out
        bullets = 0
        for (i = 2; i <= n; i++) if (is_bullet(sec[i])) {
          print sec[i] >> agent_out
          bullets++
          if (bullets >= 6) break
        }
        if (bullets == 0) {
          for (i = 2; i <= n && i <= 8; i++) print sec[i] >> agent_out
        }
        print "" >> agent_out
        return
      }
      if (bucket == "mission") {
        for (i = 1; i <= n && i <= 40; i++) print sec[i] >> agent_out
        print "" >> agent_out
        return
      }
      if (bucket == "rules") {
        for (i = 1; i <= n; i++) print sec[i] >> agent_out
        return
      }
      if (bucket == "workflow") {
        has_workflow = 1
        steps = 0
        for (i = 1; i <= n; i++) if (is_step(sec[i])) steps++
        if (steps > 8) {
          workflow_long = 1
          print sec[1] >> agent_out
          steps = 0
          for (i = 2; i <= n; i++) if (is_step(sec[i])) {
            print sec[i] >> agent_out
            steps++
            if (steps >= 8) break
          }
          print "" >> agent_out
          for (i = 1; i <= n; i++) print sec[i] >> skill_out
          has_skill = 1
        } else {
          for (i = 1; i <= n; i++) print sec[i] >> agent_out
        }
        return
      }
      if (bucket == "deliverables") {
        has_deliverables = 1
        has_skill = 1
        want_ref = 0
        for (i = 1; i <= n; i++) print sec[i] >> skill_out
        if (n > 40) want_ref = 1
        else {
          for (i = 1; i <= n; i++) if (sec[i] ~ /```/) { want_ref = 1; break }
        }
        if (want_ref) {
          for (i = 1; i <= n; i++) print sec[i] >> ref_out
        }
        return
      }
      if (bucket == "cut") {
        bullets = 0
        for (i = 2; i <= n; i++) if (is_bullet(sec[i])) {
          if (bullets == 0) print sec[1] >> agent_out
          print sec[i] >> agent_out
          bullets++
          if (bullets >= 2) break
        }
        if (bullets > 0) print "" >> agent_out
        return
      }
      # default
      if (n > 25) {
        for (i = 1; i <= n; i++) print sec[i] >> skill_out
        has_skill = 1
      } else {
        for (i = 1; i <= n; i++) print sec[i] >> agent_out
      }
    }
    BEGIN {
      bucket = "preamble"; sec_n = 0; preamble_kept = 0
      has_workflow = 0; has_deliverables = 0; workflow_long = 0
      has_skill = 0; has_ref = 0
    }
    /^##[[:space:]]/ {
      flush()
      split("", sec); sec_n = 0
      bucket = classify($0)
    }
    {
      sec[++sec_n] = $0
    }
    END {
      flush()
      printf "%d %d %d %d\n", has_workflow, has_deliverables, workflow_long, has_skill
    }
  ' "$body_file")"

  # shellcheck disable=SC2086
  set -- $meta
  local has_workflow="${1:-0}" has_deliverables="${2:-0}" workflow_long="${3:-0}" has_skill="${4:-0}"

  agent_lines=0
  [[ -f "$agent_out" ]] && agent_lines="$(wc -l < "$agent_out" | tr -d ' ')"
  if [[ "$agent_lines" -gt 150 ]]; then need=1; fi
  if [[ "$has_workflow" -eq 1 && "$has_deliverables" -eq 1 ]]; then need=1; fi
  if [[ "$has_skill" -eq 1 || -s "$skill_out" ]]; then need=1; fi
  if [[ "$agent_lines" -gt 150 && ! -s "$skill_out" ]]; then
    printf '%s\n' "## Extended reference" "" \
      "See the source agent for full deliverable templates and advanced guidance." >> "$skill_out" || true
    need=1
  fi
  mkdir -p "$(dirname "$need_out")"
  printf '%s' "$need" > "$need_out" || printf '0' > "$need_out"
}

# cursor_guard_source <file> — fail closed on .mdc / cursor rules paths.
cursor_guard_source() {
  local file="$1"
  case "$file" in
    *.mdc)
      error "cursor convert refuses .mdc input (sources must be division Claude *.md): $file"
      return 1
      ;;
  esac
  case "$file" in
    */integrations/cursor/*|integrations/cursor/*|*/integrations/cursor|integrations/cursor|\
    */.cursor/rules/*|.cursor/rules/*|*/.cursor/rules|.cursor/rules)
      error "cursor convert refuses integrations/cursor or .cursor/rules paths: $file"
      return 1
      ;;
  esac
  return 0
}

convert_cursor() {
  local file="$1"
  local name description slug division emoji vibe enriched
  local need_skill
  local tmpdir body_tmp agent_tmp skill_tmp ref_tmp need_tmp outfile skill_dir
  local identity_extra="" title skill_link="" desc_escaped agent_lines

  cursor_guard_source "$file" || return 1

  # One awk pass for common frontmatter fields (faster on Git Bash)
  local fm_line
  fm_line="$(awk '
    /^---$/ { fm++; next }
    fm == 1 && /^name: / { sub(/^name: /, ""); name=$0 }
    fm == 1 && /^description: / { sub(/^description: /, ""); desc=$0 }
    fm == 1 && /^emoji: / { sub(/^emoji: /, ""); emoji=$0 }
    fm == 1 && /^vibe: / { sub(/^vibe: /, ""); vibe=$0 }
    fm >= 2 { exit }
    END { printf "%s\t%s\t%s\t%s", name, desc, emoji, vibe }
  ' "$file")"
  IFS=$'\t' read -r name description emoji vibe <<< "$fm_line"
  slug="$(slugify "$name")"
  division="$(cursor_division_of "$file")"
  enriched="$(cursor_enrich_description "$description" "$name")"

  # Collision warn: same slug already staged under another division
  if [[ -n "${CURSOR_SLUG_INDEX:-}" ]]; then
    local prev
    prev="$(grep -E "^${slug}[[:space:]]" "$CURSOR_SLUG_INDEX" 2>/dev/null | head -1 || true)"
    if [[ -n "$prev" ]]; then
      warn "cursor: duplicate slug '$slug' (also in ${prev#* }) — install flatten last-writer-wins"
    fi
    printf '%s %s\n' "$slug" "$division" >> "$CURSOR_SLUG_INDEX"
  fi

  # Reuse per-run work dir (avoid fragile per-agent /tmp on Git Bash / Windows)
  if [[ -z "${CURSOR_WORK_DIR:-}" || ! -d "${CURSOR_WORK_DIR:-}" ]]; then
    CURSOR_WORK_DIR="$OUT_DIR/cursor/.work-$$"
    mkdir -p "$CURSOR_WORK_DIR"
  fi
  body_tmp="$CURSOR_WORK_DIR/body.md"
  agent_tmp="$CURSOR_WORK_DIR/agent.md"
  skill_tmp="$CURSOR_WORK_DIR/skill.md"
  ref_tmp="$CURSOR_WORK_DIR/ref.md"
  need_tmp="$CURSOR_WORK_DIR/need.txt"
  get_body "$file" > "$body_tmp"
  : > "$agent_tmp"; : > "$skill_tmp"; : > "$ref_tmp"
  cursor_trim_body "$body_tmp" "$agent_tmp" "$skill_tmp" "$ref_tmp" "$need_tmp"
  need_skill="$(cat "$need_tmp" 2>/dev/null || echo 0)"

  if [[ -n "$vibe" ]]; then
    identity_extra="## Identity"$'\n'"- **Vibe**: ${vibe}"$'\n\n'
  fi

  title="# ${name}"
  [[ -n "$emoji" ]] && title="# ${emoji} ${name}"

  if [[ "$need_skill" == "1" && -s "$skill_tmp" ]]; then
    skill_link=$'\n'"## Skill pack"$'\n'"- Detailed workflows and deliverable templates: see skill \`${slug}\` (SKILL.md)."$'\n'
  fi

  outfile="$OUT_DIR/cursor/agents/${division}/${slug}.md"
  mkdir -p "$(dirname "$outfile")"

  desc_escaped="$(cursor_yaml_escape "$enriched")"

  {
    cat <<HEREDOC
---
name: ${slug}
description: "${desc_escaped}"
model: inherit
---

${title}

HEREDOC
    [[ -n "$identity_extra" ]] && printf '%s' "$identity_extra"
    cat "$agent_tmp"
    [[ -n "$skill_link" ]] && printf '%s' "$skill_link"
  } > "$outfile"

  agent_lines="$(wc -l < "$outfile" | tr -d ' ')"
  if [[ "$agent_lines" -gt 150 ]]; then
    warn "cursor: ${division}/${slug} subagent is ${agent_lines} lines (prefer ≤150)"
  fi

  # Hard cap: keep ≤200 lines in subagent; overflow goes to skill
  if [[ "$agent_lines" -gt 200 ]]; then
    local keep=180 overflow_tmp
    overflow_tmp="$CURSOR_WORK_DIR/overflow.md"
    : > "$overflow_tmp"
    awk -v keep="$keep" -v overflow="$overflow_tmp" '
      BEGIN { n=0; fm=0 }
      /^---$/ { fm++; print; next }
      fm < 2 { print; next }
      {
        n++
        if (n <= keep) print
        else print >> overflow
      }
    ' "$outfile" > "$outfile.tmp"
    mv "$outfile.tmp" "$outfile"
    if [[ -s "$overflow_tmp" ]]; then
      printf '\n## Overflow (trimmed from subagent)\n\n' >> "$skill_tmp"
      cat "$overflow_tmp" >> "$skill_tmp"
      need_skill=1
      printf '\n## Skill pack\n- Additional detail moved to skill `%s` (SKILL.md).\n' "$slug" >> "$outfile"
    fi
    agent_lines="$(wc -l < "$outfile" | tr -d ' ')"
    warn "cursor: ${division}/${slug} truncated to ${agent_lines} lines (hard cap 200)"
  fi

  local has_skill=0
  if [[ "$need_skill" == "1" && -s "$skill_tmp" ]]; then
    has_skill=1
    skill_dir="$OUT_DIR/cursor/skills/${division}/${slug}"
    mkdir -p "$skill_dir"
    {
      cat <<HEREDOC
---
name: ${slug}
description: "${desc_escaped}"
disable-model-invocation: true
---

# ${name} Skill

HEREDOC
      cat "$skill_tmp"
    } > "$skill_dir/SKILL.md"
    if [[ -s "$ref_tmp" ]]; then
      {
        printf '# %s Reference\n\n' "$name"
        cat "$ref_tmp"
      } > "$skill_dir/reference.md"
    fi
  fi

  # Catalog row for cursor_finalize (TSV: slug, name, division, desc, has_skill)
  if [[ -n "${CURSOR_CATALOG_TSV:-}" ]]; then
    printf '%s\t%s\t%s\t%s\t%s\n' "$slug" "$name" "$division" "$desc_escaped" "$has_skill" \
      >> "$CURSOR_CATALOG_TSV"
  fi
}

# cursor_finalize — once per cursor convert run: router, catalog, command, AGENTS template.
# Never writes persona rules/*.mdc.
cursor_finalize() {
  local cursor_root="$OUT_DIR/cursor"
  local agents_root="$cursor_root/agents"
  [[ -d "$agents_root" ]] || { warn "cursor_finalize: no agents/ to catalog"; return 0; }

  mkdir -p "$cursor_root/rules" "$cursor_root/commands" "$cursor_root/catalog/by-division"

  # Thin always-on router only
  cat > "$cursor_root/rules/agency-router.mdc" <<'HEREDOC'
---
description: Agency Agents router — activate project subagents; do not inline persona bodies.
alwaysApply: true
---

# Agency Agents Router

This project has Agency Agents installed as Cursor **subagents** under `.cursor/agents/`.

## How to delegate

1. Prefer the Task / subagent tool with the matching agent `name` (slug) from `.cursor/agents/`.
2. Use `/agency` (`.cursor/commands/agency.md`) or `.cursor/catalog/roster.json` to pick by division.
3. Do **not** paste full persona rule bodies into the chat. Subagents already carry trimmed instructions.
4. Keep this router thin — it only routes; expertise lives in subagents (and optional skills).

If unsure which agent to use, open `AGENTS.md` (Agency section) or `catalog/by-division/`.
HEREDOC

  # Catalog from TSV accumulated during convert_cursor (no per-file re-scan)
  local roster_file="$cursor_root/catalog/roster.json"
  local slug name division desc has_skill artifacts first=1
  printf '[\n' > "$roster_file"
  if [[ -n "${CURSOR_CATALOG_TSV:-}" && -f "${CURSOR_CATALOG_TSV:-}" ]]; then
    while IFS=$'\t' read -r slug name division desc has_skill; do
      [[ -n "$slug" ]] || continue
      artifacts='["agent"]'
      [[ "$has_skill" == "1" ]] && artifacts='["agent","skill"]'
      if [[ "$first" -eq 1 ]]; then first=0; else printf ',\n' >> "$roster_file"; fi
      printf '  {"slug":"%s","name":"%s","division":"%s","description":"%s","artifacts":%s}' \
        "$slug" "$name" "$division" "$desc" "$artifacts" >> "$roster_file"
      # Append to by-division page (create header once via sentinel files)
      if [[ ! -f "$cursor_root/catalog/by-division/${division}.md" ]]; then
        printf '# %s\n\n| Slug | Name |\n|------|------|\n' "$division" \
          > "$cursor_root/catalog/by-division/${division}.md"
      fi
      printf '| `%s` | %s |\n' "$slug" "$name" >> "$cursor_root/catalog/by-division/${division}.md"
    done < "$CURSOR_CATALOG_TSV"
  fi
  printf '\n]\n' >> "$roster_file"

  cat > "$cursor_root/commands/agency.md" <<'HEREDOC'
# Agency — list or activate an Agency agent

Read `.cursor/catalog/roster.json` (or `catalog/by-division/<division>.md`) and help the user pick a subagent.

## Behavior

1. If the user names a slug or role, activate that Cursor subagent (Task / subagent with `name` = slug).
2. If the user names a division, list matching slugs from the catalog.
3. If unclear, ask one clarifying question, then recommend 1–3 agents.
4. Do not dump full agent bodies into the chat; delegate to the subagent instead.

Installed agents live in `.cursor/agents/<slug>.md`.
HEREDOC

  cat > "$cursor_root/AGENTS.md.template" <<'HEREDOC'
<!-- agency-agents:start -->
## Agency Agents

This project uses [Agency Agents](https://github.com/msitarzewski/agency-agents) as Cursor subagents.

- **Activate:** Task / subagent by slug under `.cursor/agents/`, or run `/agency`.
- **Router:** `.cursor/rules/agency-router.mdc` (always on, thin — no persona bodies).
- **Catalog:** `.cursor/catalog/roster.json` and `catalog/by-division/`.
- **Selective install:** prefer `--division` / `--agent` (large full-roster installs add delegation noise).

Do not convert or reinstall from `.mdc` persona rules; sources are division Claude `*.md` agents.
<!-- agency-agents:end -->
HEREDOC

  info "cursor: wrote router, catalog, /agency command, AGENTS.md.template"
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

# Remove a tool's previously-generated output before regenerating, so renamed or
# deleted agents don't leave orphan files behind (convert.sh overwrites in place
# but never pruned stale output). Preserves the committed README.md — the only
# tracked file under integrations/<tool>/ for conversion targets.
clean_tool_output() {
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

  # Cursor slug collision index + catalog TSV + stable work dir (Claude sources only)
  if [[ "$tool" == "cursor" ]]; then
    CURSOR_SLUG_INDEX="$OUT_DIR/cursor/.slug-index-$$"
    CURSOR_CATALOG_TSV="$OUT_DIR/cursor/.catalog-$$.tsv"
    CURSOR_WORK_DIR="$OUT_DIR/cursor/.work-$$"
    mkdir -p "$OUT_DIR/cursor" "$CURSOR_WORK_DIR"
    : > "$CURSOR_SLUG_INDEX"
    : > "$CURSOR_CATALOG_TSV"
  fi

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
        windsurf)    accumulate_windsurf "$file" ;;
      esac

      (( count++ )) || true
    done < <(find "$dirpath" -name "*.md" -type f -print0 | sort -z)
  done

  if [[ "$tool" == "cursor" ]]; then
    cursor_finalize
    rm -f "${CURSOR_SLUG_INDEX:-}" "${CURSOR_CATALOG_TSV:-}"
    rm -rf "${CURSOR_WORK_DIR:-}"
    unset CURSOR_SLUG_INDEX CURSOR_CATALOG_TSV CURSOR_WORK_DIR
  fi

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
    local parallel_tools=(antigravity gemini-cli opencode cursor openclaw qwen zcode codex osaurus hermes vibe)
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
    local idx=8
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
