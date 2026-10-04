#!/usr/bin/env bash
# Code fences that GitHub renders differently from what the author meant must
# fail lint, and the fix the error message suggests must pass it.
#
# Markdown has no nesting at equal fence length. Inside a ```markdown template,
# a ```bash line is text, and the example's closing ``` ends the template, so
# the rest of it renders as headings and prose. Seven roster agents shipped
# that way, three of them with the last block left open to the end of the file.
#
# A closing fence is allowed up to three spaces of indentation regardless of how
# far the opener was indented (CommonMark; GitHub renders it that way). The
# helper used to also require the closer's indent to be <= the opener's, which
# read GitHub-valid documents as still-open: lint reported a false "does not
# nest" and the OpenClaw split kept the following "##" heading inside the block.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURE="$(mktemp -d "${TMPDIR:-/tmp}/agency-lint-fences.XXXXXX")"
trap 'rm -rf "$FIXTURE"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

frontmatter() {
  cat <<'EOF'
---
name: Fence Fixture
description: Fixture agent for the code-fence lint rules
color: blue
---
## Identity
Enough words to clear the short-body warning, repeated so the linter has a
body to read: this fixture exists to check how fenced code blocks are parsed.
## Core Mission
Show a template that contains a code example.
## Critical Rules
Keep fences balanced.
EOF
}

# 1. ```bash inside ```markdown: the inner fence does not nest.
{ frontmatter; cat <<'EOF'
### Template
```markdown
# Report
```bash
npm test
```
## Findings
```
EOF
} > "$FIXTURE/nested.md"
if bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/nested.md" > "$FIXTURE/nested.log" 2>&1; then
  fail "linter accepted a \`\`\`bash fence nested in a \`\`\`markdown block of the same length"
fi
grep -Fq "nested.md:16: '\`\`\`bash' inside the block opened at line 14 does not nest" "$FIXTURE/nested.log" \
  || { cat "$FIXTURE/nested.log" >&2; fail "nested-fence error is missing or names the wrong lines"; }

# 2. A block left open to the end of the file.
{ frontmatter; printf '%s\n' '### Layout' '```' 'css/' 'js/'; } > "$FIXTURE/unclosed.md"
if bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/unclosed.md" > "$FIXTURE/unclosed.log" 2>&1; then
  fail "linter accepted a code block that is never closed"
fi
grep -Fq "unclosed.md:14: code block is never closed" "$FIXTURE/unclosed.log" \
  || { cat "$FIXTURE/unclosed.log" >&2; fail "unclosed-fence error is missing or names the wrong line"; }

# 3. The fix the message suggests — a longer outer fence — passes, and so do
#    tilde fences and a shorter run inside a longer block.
{ frontmatter; cat <<'EOF'
### Template
````markdown
# Report
```bash
npm test
```
## Findings
````
~~~text
```python is just text in here
~~~
EOF
} > "$FIXTURE/valid.md"
bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/valid.md" > "$FIXTURE/valid.log" 2>&1 \
  || { cat "$FIXTURE/valid.log" >&2; fail "linter rejected correctly nested fences"; }

# 4. The helper itself, which the OpenClaw split in convert.sh shares: only a
#    bare run of the same character, at least as long, closes a block.
. "$SCRIPT_DIR/lib.sh"
fence_closes_p '```python' '`' 3 0 && fail "fence_closes_p treated '\`\`\`python' as a closing fence"
fence_closes_p '```' '`' 3 0       || fail "fence_closes_p rejected a bare closing fence"
fence_closes_p '````  ' '`' 3 0    || fail "fence_closes_p rejected a longer closing fence with trailing spaces"
fence_closes_p '```' '`' 4 0       && fail "fence_closes_p let a shorter run close a longer fence"

# 5. A closing fence's indent is its own rule: up to three spaces, whatever the
#    opener's indent. These used to be read as nestable openers, not closers.
fence_closes_p '  ```' '`' 3 0   || fail "fence_closes_p rejected a bare closer indented 2 spaces under an unindented opener"
fence_closes_p '   ```' '`' 3 0  || fail "fence_closes_p rejected a bare closer indented 3 spaces under an unindented opener"
fence_closes_p '   ~~~' '~' 3 0  || fail "fence_closes_p rejected an indented tilde closer"
fence_closes_p '  ```' '`' 4 0   && fail "fence_closes_p let an indented shorter run close a longer fence"
fence_closes_p '    ```' '`' 3 0 && fail "fence_closes_p treated a 4-space-indented line as a closing fence"

# 6. The linter must accept the GitHub-valid document and read '## Findings' as
#    a heading, not as text inside the block.
{ frontmatter; cat <<'EOF'
### Template
```text
code
  ```
## Findings
EOF
} > "$FIXTURE/indented-closer.md"
if ! bash "$SCRIPT_DIR/lint-agents.sh" "$FIXTURE/indented-closer.md" > "$FIXTURE/indented-closer.log" 2>&1; then
  cat "$FIXTURE/indented-closer.log" >&2
  fail "linter rejected a GitHub-valid indented closing fence"
fi

# 7. convert_openclaw shares the helper, so the section after an indented closer
#    belongs in AGENTS.md; on the old helper it stayed inside the open SOUL
#    section and AGENTS.md lost it.
mkdir -p "$FIXTURE/repo/scripts" "$FIXTURE/repo/engineering" "$FIXTURE/output"
cp "$SCRIPT_DIR/convert.sh" "$SCRIPT_DIR/lib.sh" "$FIXTURE/repo/scripts/"
cat > "$FIXTURE/repo/engineering/fence-fixture.md" <<'EOF'
---
name: Fence Fixture
description: Fixture agent for indented closing fences
color: blue
---
## Identity
```text
code
  ```
## Core Mission
mission text
EOF
if ! bash "$FIXTURE/repo/scripts/convert.sh" --tool openclaw --out "$FIXTURE/output" > "$FIXTURE/convert.log" 2>&1; then
  cat "$FIXTURE/convert.log" >&2
  fail "openclaw conversion failed on the indented-closer fixture"
fi
grep -q '^## Core Mission' "$FIXTURE/output/openclaw/fence-fixture/AGENTS.md" \
  || fail "openclaw kept the section after an indented closer in SOUL.md"
grep -q '^## Core Mission' "$FIXTURE/output/openclaw/fence-fixture/SOUL.md" \
  && fail "openclaw wrote the section after an indented closer to both outputs"

echo "PASS: nested and unclosed fences are rejected; correctly nested fences and indented closers pass"
