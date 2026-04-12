#!/usr/bin/env bash
#
# Generates the "Agent Index" section in README.md from agent markdown files.
# Usage:
#   ./scripts/generate-readme-agent-index.sh          # update README in-place
#   ./scripts/generate-readme-agent-index.sh --check   # exit non-zero if out of date

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
README="$REPO_ROOT/README.md"

BEGIN_MARKER="<!-- BEGIN GENERATED AGENT INDEX -->"
END_MARKER="<!-- END GENERATED AGENT INDEX -->"

# Directories in display order
CATEGORIES=(
  engineering
  design
  paid-media
  sales
  marketing
  product
  project-management
  testing
  support
  spatial-computing
  specialized
  game-development
  academic
)

# Map directory name to human-readable heading (Bash 3.2 compatible)
category_heading() {
  case "$1" in
    engineering)        echo "Engineering" ;;
    design)             echo "Design" ;;
    paid-media)         echo "Paid Media" ;;
    sales)              echo "Sales" ;;
    marketing)          echo "Marketing" ;;
    product)            echo "Product" ;;
    project-management) echo "Project Management" ;;
    testing)            echo "Testing" ;;
    support)            echo "Support" ;;
    spatial-computing)  echo "Spatial Computing" ;;
    specialized)        echo "Specialized" ;;
    game-development)   echo "Game Development" ;;
    academic)           echo "Academic" ;;
    *)                  echo "$1" ;;
  esac
}

generate_index() {
  local output=""

  for category in "${CATEGORIES[@]}"; do
    local dir="$REPO_ROOT/$category"
    [[ -d "$dir" ]] || continue

    local heading
    heading="$(category_heading "$category")"
    local entries=""

    while IFS= read -r filepath; do
      local basename
      basename="$(basename "$filepath")"
      [[ "$basename" == "README.md" ]] && continue

      # Only include files that start with YAML frontmatter
      local first_line
      first_line="$(head -1 "$filepath")"
      [[ "$first_line" == "---" ]] || continue

      # Extract name from frontmatter
      local name
      name="$(awk 'NR==1{next} /^---$/{exit} /^name:/{sub(/^name:[[:space:]]*/, ""); print}' "$filepath")"
      [[ -z "$name" ]] && continue

      local relpath="${filepath#"$REPO_ROOT/"}"
      entries+="- [${name}](${relpath})"$'\n'
    done < <(find "$dir" -name '*.md' -type f | sort)

    if [[ -n "$entries" ]]; then
      output+=$'\n'"### ${heading}"$'\n'
      output+=$'\n'"${entries}"
    fi
  done

  printf '%s' "$output"
}

# Build the new generated block
new_block="$(generate_index)"

if [[ "$*" == *"--check"* ]]; then
  # Extract existing block from README
  existing="$(awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
    index($0, begin) { found=1; next }
    index($0, end)   { found=0; next }
    found            { print }
  ' "$README")"

  if [[ "$existing" == "$new_block" ]]; then
    echo "Agent index is up to date."
    exit 0
  else
    echo "ERROR: Agent index in README.md is out of date."
    echo "Run ./scripts/generate-readme-agent-index.sh to regenerate."
    diff <(echo "$existing") <(echo "$new_block") || true
    exit 1
  fi
fi

# Replace content between markers in-place using temp files so multiline
# generated content works on Bash 3.2 and malformed existing blocks can be
# overwritten cleanly.
tmp_readme="$(mktemp)"
tmp_block="$(mktemp)"

printf '%s\n' "$new_block" > "$tmp_block"

awk -v begin="$BEGIN_MARKER" '
  { print }
  index($0, begin) { exit }
' "$README" > "$tmp_readme"

cat "$tmp_block" >> "$tmp_readme"
printf '%s\n' "$END_MARKER" >> "$tmp_readme"

awk -v end="$END_MARKER" '
  index($0, end) { found=1; next }
  found          { print }
' "$README" >> "$tmp_readme"

mv "$tmp_readme" "$README"
rm -f "$tmp_block"

echo "Agent index in README.md updated."
