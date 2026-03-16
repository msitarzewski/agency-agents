#!/usr/bin/env bash
#
# Validates agent markdown files:
#   1. YAML frontmatter must exist with name, description, color (ERROR)
#   2. Recommended sections checked but only warned (WARN)
#   3. File must have meaningful content
#
# Usage: ./scripts/lint-agents.sh [file ...]
#   If no files given, scans all agent directories.

set -euo pipefail

# Keep in sync with AGENT_DIRS in scripts/convert.sh
AGENT_DIRS=(
  academic
  design
  engineering
  finance
  game-development
  marketing
  paid-media
  product
  project-management
  sales
  spatial-computing
  specialized
  strategy
  support
  testing
)

REQUIRED_FRONTMATTER=("name" "description" "color")
RECOMMENDED_SECTIONS=("Identity" "Core Mission" "Critical Rules")

errors=0
warnings=0

classify_header_target() {
  local header_lower="$1"

  if [[ "$header_lower" =~ identity ]] ||
     [[ "$header_lower" =~ learning.*memory ]] ||
     [[ "$header_lower" =~ communication ]] ||
     [[ "$header_lower" =~ style ]] ||
     [[ "$header_lower" =~ critical.rule ]] ||
     [[ "$header_lower" =~ rules.you.must.follow ]]; then
    printf 'soul'
  else
    printf 'agents'
  fi
}

lint_file() {
  local file="$1"

  if [[ ! -f "$file" ]]; then
    echo "ERROR $file: not a file or does not exist"
    errors=$((errors + 1))
    return
  fi

  # 1. Check frontmatter delimiters
  local first_line
  first_line=$(head -1 "$file")
  if [[ "$first_line" != "---" ]]; then
    echo "ERROR $file: missing frontmatter opening ---"
    errors=$((errors + 1))
    return
  fi

  # Extract frontmatter (between first and second ---)
  local frontmatter
  frontmatter=$(awk 'NR==1{next} /^---$/{exit} {print}' "$file")

  if [[ -z "$frontmatter" ]]; then
    echo "ERROR $file: empty or malformed frontmatter"
    errors=$((errors + 1))
    return
  fi

  # 2. Check required frontmatter fields
  for field in "${REQUIRED_FRONTMATTER[@]}"; do
    if ! echo "$frontmatter" | grep -qE "^${field}:"; then
      echo "ERROR $file: missing frontmatter field '${field}'"
      errors=$((errors + 1))
    fi
  done

  # 3. Check recommended sections (warn only)
  local body
  body=$(awk 'BEGIN{n=0} /^---$/{n++; next} n>=2{print}' "$file")

  for section in "${RECOMMENDED_SECTIONS[@]}"; do
    if ! echo "$body" | grep -qi "$section"; then
      echo "WARN  $file: missing recommended section '${section}'"
      warnings=$((warnings + 1))
    fi
  done

  # 4. Check file has meaningful content (awk strips wc's leading whitespace on macOS/BSD)
  local word_count
  word_count=$(echo "$body" | wc -w | awk '{print $1}')
  if [[ "${word_count:-0}" -lt 50 ]]; then
    echo "WARN  $file: body seems very short (< 50 words)"
    warnings=$((warnings + 1))
  fi

  local soul_headers=0
  local agents_headers=0
  while IFS= read -r line; do
    if [[ "$line" =~ ^##[[:space:]] ]]; then
      local header_lower
      header_lower=$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')
      local target
      target=$(classify_header_target "$header_lower")
      if [[ "$target" == "soul" ]]; then
        soul_headers=$((soul_headers + 1))
      else
        agents_headers=$((agents_headers + 1))
      fi
    fi
  done <<< "$body"

  if [[ $soul_headers -eq 0 ]]; then
    echo "WARN  $file: no section headers map to SOUL.md in convert.sh"
    warnings=$((warnings + 1))
  fi

  if [[ $agents_headers -eq 0 ]]; then
    echo "WARN  $file: no section headers map to AGENTS.md in convert.sh"
    warnings=$((warnings + 1))
  fi
}

# Collect files to lint
files=()
if [[ $# -gt 0 ]]; then
  files=("$@")
else
  for dir in "${AGENT_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
      while IFS= read -r f; do
        files+=("$f")
      done < <(find "$dir" -name "*.md" -type f | sort)
    fi
  done
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No agent files found."
  exit 1
fi

echo "Linting ${#files[@]} agent files..."
echo ""

for file in "${files[@]}"; do
  lint_file "$file"
done

echo ""
echo "Results: ${errors} error(s), ${warnings} warning(s) in ${#files[@]} files."

if [[ $errors -gt 0 ]]; then
  echo "FAILED: fix the errors above before merging."
  exit 1
else
  echo "PASSED"
  exit 0
fi
