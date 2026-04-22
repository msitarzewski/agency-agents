#!/usr/bin/env bash
#
# utils.sh -- Shared utility functions for install.sh and convert.sh
#
# This file contains common functions, color definitions, and helper utilities
# used by both installation and conversion scripts. Source this file first in
# convert.sh and install.sh.
#
# Prevent duplicate sourcing
if [[ -n "${AGENCY_UTILS_LOADED:-}" ]]; then
  return
fi
readonly AGENCY_UTILS_LOADED=1

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

# ---------------------------------------------------------------------------
# Output functions
# ---------------------------------------------------------------------------
ok()     { printf "${C_GREEN}[OK]${C_RESET}  %s\n" "$*"; }
warn()   { printf "${C_YELLOW}[!!]${C_RESET}  %s\n" "$*"; }
err()    { printf "${C_RED}[ERR]${C_RESET} %s\n" "$*" >&2; }
header() { printf "\n${C_BOLD}%s${C_RESET}\n" "$*"; }
dim()    { printf "${C_DIM}%s${C_RESET}\n" "$*"; }

# ---------------------------------------------------------------------------
# Progress bar: [=======>    ] 3/8 (tqdm-style)
# ---------------------------------------------------------------------------
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
# Paths and constants
# ---------------------------------------------------------------------------

# Standard agent category directories (keep sorted, sync with convert.sh / install.sh / lint-agents.sh)
AGENT_DIRS=(
  academic design engineering finance game-development marketing paid-media product project-management
  sales spatial-computing specialized strategy support testing
)

# Agents filter list (populated by load_agents_filter)
AGENTS_FILTER=()

# ---------------------------------------------------------------------------
# Default parallel job count (nproc on Linux; sysctl on macOS when nproc missing)
# ---------------------------------------------------------------------------
parallel_jobs_default() {
  local n
  n=$(nproc 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  n=$(sysctl -n hw.ncpu 2>/dev/null) && [[ -n "$n" ]] && echo "$n" && return
  echo 4
}

# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

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

# Extract the 'name' field from an agent file's frontmatter.
# Usage: get_agent_name <file>
get_agent_name() {
  get_field "name" "$1"
}

# Convert a human-readable agent name to a lowercase kebab-case slug.
# "Frontend Developer" → "frontend-developer"
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//'
}

# ---------------------------------------------------------------------------
# Agents filter functions
# ---------------------------------------------------------------------------

# Load agents filter list from a file.
# Each line should contain an agent name (frontmatter 'name' field value).
# Ignores empty lines and lines starting with '#'.
# If file doesn't exist, warns and returns (doesn't filter).
# Usage: load_agents_filter <path>
load_agents_filter() {
  local file="$1"

  # Clear any previous filter
  AGENTS_FILTER=()

  # If no file specified, no filtering
  [[ -z "$file" ]] && return 0

  # If file doesn't exist, warn and continue (no filtering)
  if [[ ! -f "$file" ]]; then
    warn "agents-file '$file' not found, installing all agents."
    return 0
  fi

  # Read file line by line
  local line
  while IFS= read -r line; do
    # Trim leading/trailing whitespace
    line="$(echo "$line" | xargs)"
    # Skip empty lines and comments
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    # Add to filter array
    AGENTS_FILTER+=("$line")
  done < "$file"

  ok "Loaded ${#AGENTS_FILTER[@]} agent names from filter list."
}

# Check if an agent name is in the filter list.
# If filter is empty, returns true (0) — allows all agents.
# Usage: name_in_filter <name>
name_in_filter() {
  local name="$1"

  # If no filter is set, allow everything
  [[ ${#AGENTS_FILTER[@]} -eq 0 ]] && return 0

  # Check if name matches any entry in filter
  local entry
  for entry in "${AGENTS_FILTER[@]}"; do
    if [[ "$entry" == "$name" ]]; then
      return 0
    fi
  done

  return 1
}

# Check if a slug is in the filter list (by comparing against slugified agent names).
# If filter is empty, returns true (0) — allows all agents.
# Usage: slug_in_filter <slug>
slug_in_filter() {
  local slug="$1"

  # If no filter is set, allow everything
  [[ ${#AGENTS_FILTER[@]} -eq 0 ]] && return 0

  # Check if slug matches any slugified entry in filter
  local entry slugified
  for entry in "${AGENTS_FILTER[@]}"; do
    slugified="$(slugify "$entry")"
    if [[ "$slugified" == "$slug" ]]; then
      return 0
    fi
  done

  return 1
}
