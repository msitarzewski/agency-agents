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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

# Keep in sync with AGENT_DIRS in scripts/convert.sh
AGENT_DIRS=(
  academic
  design
  engineering
  finance
  game-development
  gis
  healthcare
  marketing
  paid-media
  product
  project-management
  research
  sales
  security
  spatial-computing
  specialized
  support
  testing
)

REQUIRED_FRONTMATTER=("name" "description" "color")
RECOMMENDED_SECTIONS=("Identity" "Core Mission" "Critical Rules")

# The color names convert.sh's resolve_opencode_color() knows, read out of the
# converter rather than copied, so this can never drift from the map that does
# the work. A name that is not in it falls through to grey in the OpenCode
# integration, which reads as a deliberate grey instead of a miss: `slate` and
# `navy` sat there unnoticed across four agents.
KNOWN_COLORS="$(
  awk '/^resolve_opencode_color\(\)/{f=1; next} f && /^}/{exit} f' "$SCRIPT_DIR/convert.sh" 2>/dev/null \
    | grep -oE '^ +[a-z-]+\)' | tr -d ' )'
)"
# If the map could not be read, check hex values only rather than rejecting
# every named color on the strength of an empty list.
[[ -n "$KNOWN_COLORS" ]] || echo "WARN  could not read resolve_opencode_color() from $SCRIPT_DIR/convert.sh — skipping the color-name check"

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

  # 0. Reject CRLF line endings (repo standard is LF — see .gitattributes).
  # A trailing \r otherwise makes the frontmatter check below fail with a
  # confusing "missing frontmatter ---" even when the file clearly starts ---.
  if LC_ALL=C grep -q $'\r' "$file"; then
    echo "ERROR $file: CRLF line endings detected — convert to LF (e.g. 'perl -i -pe \"s/\\r\$//\" $file'); repo uses LF per .gitattributes"
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
  if ! awk 'NR > 1 && $0 == "---" {found = 1; exit} END {exit !found}' "$file"; then
    echo "ERROR $file: missing frontmatter closing ---"
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

  # The lightweight converters read plain or quoted scalar fields. A folded
  # block otherwise passes presence checks but leaks its YAML indicator into
  # the generated value.
  if grep -qE '^[[:space:]]*[[:alnum:]_-]+:[[:space:]]*>([-+][1-9]?|[1-9][-+]?)?([[:space:]]+#.*)?[[:space:]]*$' <<<"$frontmatter"; then
    echo "ERROR $file: folded YAML frontmatter is unsupported — use a single-line scalar"
    errors=$((errors + 1))
    return
  fi

  # 2. Check required frontmatter fields
  for field in "${REQUIRED_FRONTMATTER[@]}"; do
    if ! grep -qE -- "^${field}:" <<<"$frontmatter"; then
      echo "ERROR $file: missing frontmatter field '${field}'"
      errors=$((errors + 1))
    elif [[ ! "$(get_field "$field" "$file")" =~ [^[:space:]] ]]; then
      echo "ERROR $file: frontmatter field '${field}' must not be empty"
      errors=$((errors + 1))
    fi
  done

  local name
  name="$(get_field name "$file")"
  if [[ -n "$name" && -z "$(slugify "$name")" ]]; then
    echo "ERROR $file: name '$name' produces an empty agent slug; include an ASCII alias"
    errors=$((errors + 1))
  fi

  # 2b. The color has to be one the converters can resolve. Checking only that
  # the field exists let four agents ship a name nothing maps, and they render
  # grey in OpenCode with no warning anywhere.
  local color
  color="$(get_field color "$file" | tr '[:upper:]' '[:lower:]')"
  if [[ -n "$color" && -n "$KNOWN_COLORS" ]] \
     && [[ ! "$color" =~ ^#?[0-9a-f]{6}$ ]] \
     && ! grep -qxF "$color" <<<"$KNOWN_COLORS"; then
    echo "ERROR $file: color '${color}' is not a #RRGGBB value or a name the converters know"
    echo "      known names: $(tr '\n' ' ' <<<"$KNOWN_COLORS")"
    echo "      use a hex value, or add '${color}' to resolve_opencode_color() in scripts/convert.sh"
    errors=$((errors + 1))
  fi

  # 3. Check recommended sections (warn only)
  local body
  body=$(awk 'BEGIN{n=0} /^---$/{n++; next} n>=2{print}' "$file")

  # Feed grep from a herestring, not a pipe: `grep -q` exits at the first match
  # without draining its input, which kills a piping `echo` with SIGPIPE. Under
  # `set -o pipefail` that 141 becomes the pipeline's status and is indistinguishable
  # from "no match", so a large body raced its way to a spurious WARN.
  for section in "${RECOMMENDED_SECTIONS[@]}"; do
    if ! grep -qi -- "$section" <<<"$body"; then
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
  local fence_marker="" fence_len=0 fence_indent=0 fence_line=0
  # Walk the body from the file itself rather than from $body, so fence
  # errors can name a real line number. ($body drops every "---" line.)
  local lineno
  lineno=$(awk 'NR > 1 && $0 == "---" {print NR; exit}' "$file")
  # "|| [[ -n $line ]]" keeps a last line that has no trailing newline; several
  # agents end on a closing fence with none, and dropping it reads as unclosed.
  while IFS= read -r line || [[ -n "$line" ]]; do
    lineno=$((lineno + 1))
    # Skip fenced code blocks so ## doc-comment lines (e.g. GDScript `##`)
    # and in-fence markdown headers aren't miscounted (issue #849).
    if [[ -n "$fence_marker" ]]; then
      if fence_closes_p "$line" "$fence_marker" "$fence_len" "$fence_indent"; then
        fence_marker=""
        fence_len=0
        fence_indent=0
      elif fence_open_p "$line" \
           && [[ "${BASH_REMATCH[2]:0:1}" == "$fence_marker" ]] \
           && (( ${#BASH_REMATCH[2]} >= fence_len )); then
        # A fence line long enough to close this block that did not close it
        # can only be one with an info string: someone nesting ```bash inside
        # a ```markdown template. Markdown has no nesting at equal length —
        # GitHub shows that line as text and ends the outer block at the next
        # bare ```, so the rest of the template renders as a document.
        echo "ERROR $file:$lineno: '${line}' inside the block opened at line $fence_line does not nest — the next bare ${fence_marker}${fence_marker}${fence_marker} closes the outer block instead"
        echo "      fence the outer block with a longer run (e.g. ${fence_marker}${fence_marker}${fence_marker}${fence_marker}markdown ... ${fence_marker}${fence_marker}${fence_marker}${fence_marker}) so the inner ones stay inside it"
        errors=$((errors + 1))
      fi
      continue
    fi
    if fence_open_p "$line"; then
      fence_marker="${BASH_REMATCH[2]:0:1}"
      fence_len=${#BASH_REMATCH[2]}
      fence_indent=${#BASH_REMATCH[1]}
      fence_line=$lineno
      continue
    fi
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
  done < <(tail -n +"$((lineno + 1))" "$file")

  # An unclosed block runs to the end of the file: on GitHub, and in every
  # tool the converters feed, everything after the opener renders as code.
  if [[ -n "$fence_marker" ]]; then
    echo "ERROR $file:$fence_line: code block is never closed — everything after line $fence_line renders as code"
    errors=$((errors + 1))
  fi

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
