#!/usr/bin/env bash
#
# test-convert-native.sh — the optional Rust converter must write the same
# bytes as the Bash converters in convert.sh.
#
# convert.sh is the reference. scripts/agency-convert is an accelerator for its
# per-agent loop, used only when it has been built. This test runs both paths
# over the same roster and compares every generated file, so a converter change
# made on one side and not the other fails here.
#
# Usage:
#   ./scripts/test-convert-native.sh          # edge-case fixture + a sample of real agents
#   ./scripts/test-convert-native.sh --full   # the whole roster (slow in Bash on Windows)
#
# Skips (exit 0) when cargo is not installed: the native path is optional.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FULL=false
[[ "${1:-}" == "--full" ]] && FULL=true

command -v cargo >/dev/null 2>&1 || { echo "SKIP: cargo not installed; native converter not tested"; exit 0; }

cargo build --release --quiet --manifest-path "$SCRIPT_DIR/agency-convert/Cargo.toml"
BIN="$SCRIPT_DIR/agency-convert/target/release/agency-convert"
[[ -x "$BIN" ]] || BIN="$BIN.exe"
[[ -x "$BIN" ]] || { echo "FAIL: built binary not found at $BIN" >&2; exit 1; }

scratch="$(mktemp -d "${TMPDIR:-/tmp}/agency-convert-native.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT

repo="$scratch/repo"
mkdir -p "$repo/scripts" "$repo/engineering" "$repo/design"
cp "$SCRIPT_DIR/convert.sh" "$SCRIPT_DIR/lib.sh" "$repo/scripts/"

if $FULL; then
  while IFS= read -r f; do
    mkdir -p "$repo/$(dirname "$f")"
    cp "$REPO_ROOT/$f" "$repo/$f"
  done < <(cd "$REPO_ROOT" && git ls-files '*.md' | grep '/')
else
  # A sample of real agents...
  n=0
  while IFS= read -r f; do
    cp "$f" "$repo/engineering/"
    n=$((n + 1)); (( n < 6 )) || break
  done < <(find "$REPO_ROOT/engineering" -maxdepth 1 -name '*.md' -type f | sort)
fi

# ...plus every edge the converters special-case.
cat > "$repo/design/edge-quotes.md" <<'EOF'
---
name: "Edge \"Quoted\" Agent"
description: 'It''s a folded
  description: with a colon # and a hash'
color: "#a1b2c3"
emoji: 🧪
vibe: Breaks converters for a living.
tools: Read, Write, MultiEdit, Edit, Bash, Custom Tool ,
---

# Edge Agent

## 🧠 Your Identity & Memory
Persona text with a backslash \ and a "quote" and a tab	here.

```markdown
## Not a heading: inside a fence
  ```bash
  echo "still inside"
  ```
```

## Core Mission
Do the work.

## Critical Rules
- Never guess.

~~~
## Also not a heading
~~~~

### Sub heading stays with its section
EOF

cat > "$repo/design/edge-plain.md" <<'EOF'
---
name: UI & UX — Lead/Reviewer
description:   padded value
color: Teal
---
Body starts immediately.

## Learning and long-term Memory
Remember things.

## Rules You Must Follow
1. One.


EOF

printf -- '---\nname: Control Chars\ndescription: has controls\ncolor: mauve\n---\nbell\x07 form\x0c del\x7f end' \
  > "$repo/design/edge-control.md"
printf -- '---\ndescription: no name, skipped\n---\nbody\n' > "$repo/design/edge-nameless.md"
printf '# Not an agent\n\n---\nname: nope\n---\n' > "$repo/design/README.md"
printf -- '---\nname: Empty Body\ndescription: nothing follows\n---\n' > "$repo/design/edge-empty.md"

TOOLS="antigravity gemini-cli opencode cursor aider windsurf openclaw qwen zcode kimi codex osaurus vibe dsh"

for t in $TOOLS; do
  AGENCY_CONVERT_NATIVE=0 bash "$repo/scripts/convert.sh" --tool "$t" --out "$scratch/bash" >/dev/null 2>&1 \
    || { echo "FAIL: bash convert --tool $t" >&2; exit 1; }
  AGENCY_CONVERT_BIN="$BIN" bash "$repo/scripts/convert.sh" --tool "$t" --out "$scratch/native" > "$scratch/native.log" 2>&1 \
    || { echo "FAIL: native convert --tool $t" >&2; cat "$scratch/native.log" >&2; exit 1; }
done

files="$(find "$scratch/bash" -type f | wc -l | tr -d ' ')"
[[ "$files" -gt 0 ]] || { echo "FAIL: the Bash converter wrote no files" >&2; exit 1; }
if ! diff -r "$scratch/bash" "$scratch/native" > "$scratch/diff.log" 2>&1; then
  echo "FAIL: native output differs from the Bash converters" >&2
  head -40 "$scratch/diff.log" >&2
  exit 1
fi

# A duplicate slug is refused on the native path too, naming both files.
cp "$repo/design/edge-empty.md" "$repo/design/edge-empty-twin.md"
if AGENCY_CONVERT_BIN="$BIN" bash "$repo/scripts/convert.sh" --tool cursor --out "$scratch/dup" > "$scratch/dup.log" 2>&1; then
  echo "FAIL: native path accepted a duplicate slug" >&2; exit 1
fi
grep -q "duplicate agent slug 'empty-body'" "$scratch/dup.log" \
  && grep -q 'design/edge-empty.md' "$scratch/dup.log" \
  && grep -q 'design/edge-empty-twin.md' "$scratch/dup.log" \
  || { echo "FAIL: duplicate slug message missing on the native path" >&2; cat "$scratch/dup.log" >&2; exit 1; }

echo "PASS: native converter matches Bash byte for byte ($files files, 14 tools)"
