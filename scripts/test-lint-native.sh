#!/usr/bin/env bash
#
# test-lint-native.sh — the optional Rust helper must print the same lint
# report, and exit the same way, as the Bash checks in lint-agents.sh.
#
# lint-agents.sh is the reference. scripts/agency-convert runs its per-file
# checks in one process when it has been built. This test lints one fixture per
# check both ways and compares the full report, so a rule changed on one side
# and not the other fails here.
#
# Usage:
#   ./scripts/test-lint-native.sh          # one fixture per rule + a sample of real agents
#   ./scripts/test-lint-native.sh --full   # ...plus the whole roster (slow in Bash on Windows)
#
# Skips (exit 0) when cargo is not installed: the native path is optional.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FULL=false
[[ "${1:-}" == "--full" ]] && FULL=true

command -v cargo >/dev/null 2>&1 || { echo "SKIP: cargo not installed; native lint not tested"; exit 0; }

cargo build --release --quiet --manifest-path "$SCRIPT_DIR/agency-convert/Cargo.toml"
BIN="$SCRIPT_DIR/agency-convert/target/release/agency-convert"
[[ -x "$BIN" ]] || BIN="$BIN.exe"
[[ -x "$BIN" ]] || { echo "FAIL: built binary not found at $BIN" >&2; exit 1; }

scratch="$(mktemp -d "${TMPDIR:-/tmp}/agency-lint-native.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
fx="$scratch/fx"
mkdir -p "$fx"

body50="$(printf 'word %.0s' $(seq 1 60))"

# agent <file> <frontmatter> <body>
agent() { printf -- '---\n%s\n---\n%s\n' "$2" "$3" > "$fx/$1"; }

good_fm=$'name: Good Agent\ndescription: Does good things\ncolor: teal'
good_body=$'## Identity\n'"$body50"$'\n\n## Core Mission\nwork\n\n## Critical Rules\nrules'

agent good.md "$good_fm" "$good_body"
agent hex-color.md $'name: Hex\ndescription: d\ncolor: "#A1B2C3"' "$good_body"
agent unknown-color.md $'name: Mauve\ndescription: d\ncolor: Mauve' "$good_body"
agent missing-fields.md $'name: Only Name\nvibe: x' "$good_body"
agent empty-fields.md $'name:\ndescription:   \ncolor: ""' "$good_body"
agent folded.md $'name: Folded\ndescription: >-\n  folded text\ncolor: blue' "$good_body"
agent folded-comment.md $'name: Folded\ndescription: >2+ # why\n  folded text\ncolor: blue' "$good_body"
agent not-folded.md $'name: Arrow\ndescription: a > b\ncolor: blue' "$good_body"
agent short.md "$good_fm" $'## Identity\nshort'
agent no-sections.md "$good_fm" "$body50"
agent qwen.md "$good_fm" "$good_body"$'\nUse ${task_prompt} here.'
agent qwen-ok.md "$good_fm" "$good_body"$'\nUse ${other_name} here.'
agent nested-fence.md "$good_fm" "$good_body"$'\n\n```markdown\n## Template\n```bash\necho hi\n```\n```'
agent unclosed-fence.md "$good_fm" "$good_body"$'\n\n~~~\n## inside\n'
agent indented-closer.md "$good_fm" "$good_body"$'\n\n```\ncode\n  ```\n## Workflow\nsteps'
agent longer-fence.md "$good_fm" "$good_body"$'\n\n````markdown\n```bash\necho hi\n```\n````\n## Workflow\nsteps'
agent only-agents.md "$good_fm" $'## Workflow\n'"$body50"$'\nidentity core mission critical rules'
agent thematic-break.md "$good_fm" "$good_body"$'\n\n---\n\n## Communication Style\nmore'
agent empty-frontmatter.md "" "$good_body"
printf -- '---\nname: No Close\ndescription: d\ncolor: red\n' > "$fx/no-closing.md"
printf '# Title\n\n---\nname: x\n---\n' > "$fx/no-opening.md"
printf -- '---\r\nname: CRLF\r\ndescription: d\r\ncolor: red\r\n---\r\nbody\r\n' > "$scratch/crlf.md"
printf -- '---\nname: No Newline\ndescription: d\ncolor: red\n---\n## Identity\n```\ncode\n```' > "$fx/no-final-newline.md"
: > "$fx/empty.md"
mkdir "$fx/a-directory.md"

cd "$scratch"
files=()
while IFS= read -r f; do files+=("$f"); done < <(find fx -name '*.md' | sort)
files+=("fx/does-not-exist.md" "$fx/good.md")   # a missing file, and an absolute path

if $FULL; then
  while IFS= read -r f; do files+=("$f"); done \
    < <(cd "$REPO_ROOT" && git ls-files '*.md' | grep '/' | sed "s|^|$REPO_ROOT/|")
else
  n=0
  while IFS= read -r f; do
    files+=("$f"); n=$((n + 1)); (( n < 8 )) || break
  done < <(find "$REPO_ROOT/engineering" -maxdepth 1 -name '*.md' -type f | sort)
fi

bash_status=0; native_status=0
AGENCY_CONVERT_NATIVE=0 bash "$SCRIPT_DIR/lint-agents.sh" "${files[@]}" > "$scratch/bash.log" 2>&1 || bash_status=$?
AGENCY_CONVERT_BIN="$BIN" bash "$SCRIPT_DIR/lint-agents.sh" "${files[@]}" > "$scratch/native.log" 2>&1 || native_status=$?

if ! diff "$scratch/bash.log" "$scratch/native.log" > "$scratch/diff.log" 2>&1; then
  echo "FAIL: native lint report differs from the Bash report" >&2
  head -40 "$scratch/diff.log" >&2
  exit 1
fi
[[ "$bash_status" == "$native_status" ]] \
  || { echo "FAIL: exit status differs (bash $bash_status, native $native_status)" >&2; exit 1; }
[[ "$bash_status" == 1 ]] || { echo "FAIL: the fixtures should fail lint, got exit $bash_status" >&2; exit 1; }
grep -q 'does not nest' "$scratch/bash.log" && grep -q 'never closed' "$scratch/bash.log" \
  || { echo "FAIL: the fixtures did not reach the rules they target" >&2; exit 1; }

# CRLF is checked apart from the rest: Git Bash's grep reads text files with
# the carriage returns stripped, so the Bash check cannot see them there. The
# native check must reject CRLF everywhere, and must agree with Bash wherever
# Bash sees it.
crlf_status=0
AGENCY_CONVERT_BIN="$BIN" bash "$SCRIPT_DIR/lint-agents.sh" crlf.md > "$scratch/crlf-native.log" 2>&1 || crlf_status=$?
[[ "$crlf_status" == 1 ]] && grep -q 'ERROR crlf.md: CRLF line endings detected' "$scratch/crlf-native.log" \
  || { echo "FAIL: native lint accepted a CRLF file" >&2; cat "$scratch/crlf-native.log" >&2; exit 1; }
if [[ "${OSTYPE:-}" != msys* && "${OSTYPE:-}" != cygwin* ]]; then
  AGENCY_CONVERT_NATIVE=0 bash "$SCRIPT_DIR/lint-agents.sh" crlf.md > "$scratch/crlf-bash.log" 2>&1 || true
  diff "$scratch/crlf-bash.log" "$scratch/crlf-native.log" > "$scratch/crlf-diff.log" 2>&1 \
    || { echo "FAIL: CRLF report differs" >&2; cat "$scratch/crlf-diff.log" >&2; exit 1; }
fi

# A clean file passes both ways too.
for native in 0 1; do
  AGENCY_CONVERT_NATIVE="$native" AGENCY_CONVERT_BIN="$BIN" \
    bash "$SCRIPT_DIR/lint-agents.sh" fx/good.md > "$scratch/good-$native.log" 2>&1 \
    || { echo "FAIL: a clean agent failed lint (native=$native)" >&2; cat "$scratch/good-$native.log" >&2; exit 1; }
done
diff "$scratch/good-0.log" "$scratch/good-1.log" >/dev/null \
  || { echo "FAIL: clean-file report differs" >&2; exit 1; }

echo "PASS: native lint matches Bash line for line (${#files[@]} files, $(wc -l < "$scratch/bash.log" | tr -d ' ') report lines)"
