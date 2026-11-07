#!/usr/bin/env bash
# CLI integration contracts using a one-agent fixture, never a real user home.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/agency-reasonix-tests.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
repo="$TMP/repo"
mkdir -p "$repo/scripts" "$repo/engineering" "$TMP/home"
cp "$REPO_ROOT"/scripts/{convert,install,lib}.sh "$repo/scripts/"
cp "$REPO_ROOT"/{divisions,tools}.json "$repo/"
export HOME="$TMP/home"
export REASONIX_HOME="" REASONIX_SKILLS_DIR=""
INSTALL="$repo/scripts/install.sh"
CONVERT="$repo/scripts/convert.sh"
write_agent() {
  cat > "$repo/engineering/engineering-example.md" <<EOF
---
name: '$1'
description: 'An agent: keep # marks, apostrophes like don''t, and Unicode café.'
color: blue
---

# Full persona

Keep this Markdown divider:

---

The complete final paragraph.
EOF
}
write_agent 'Reasonix Example'
"$CONVERT" --tool reasonix >/dev/null
profile=reasonix-agency-reasonix-example
python3 - "$repo/integrations/reasonix/$profile/SKILL.md" <<'PY'
import pathlib, sys, yaml
text = pathlib.Path(sys.argv[1]).read_text()
fm, body = text[4:].split("\n---\n", 1)
data = yaml.safe_load(fm)
assert data == {"name": "reasonix-agency-reasonix-example",
                "description": "An agent: keep # marks, apostrophes like don't, and Unicode café.",
                "invocation": "manual", "runAs": "subagent"}, data
assert "\n---\n" in body and body.endswith("The complete final paragraph.\n")
PY
"$INSTALL" --tool reasonix --no-interactive --agent reasonix-example >/dev/null
[[ -f "$HOME/.reasonix/skills/$profile/SKILL.md" ]]
# Tilde expansion and both environment layers; --path must bypass even invalid env.
REASONIX_HOME='~/alternate home' "$INSTALL" --tool reasonix --no-interactive >/dev/null
[[ -f "$HOME/alternate home/skills/$profile/SKILL.md" ]]
REASONIX_HOME="$HOME/unused" REASONIX_SKILLS_DIR="$HOME/skills override" "$INSTALL" --tool reasonix --no-interactive >/dev/null
[[ -f "$HOME/skills override/$profile/SKILL.md" && ! -e "$HOME/unused" ]]
REASONIX_HOME=relative REASONIX_SKILLS_DIR=relative "$INSTALL" --tool reasonix --no-interactive --path "$HOME/flag wins" >/dev/null
[[ -f "$HOME/flag wins/$profile/SKILL.md" ]]
if REASONIX_HOME=relative "$INSTALL" --tool reasonix --no-interactive >"$TMP/relative.log" 2>&1; then
  echo 'Relative REASONIX_HOME was silently accepted' >&2; exit 1
fi
grep -q -- '--path' "$TMP/relative.log"
if REASONIX_SKILLS_DIR=relative "$INSTALL" --tool reasonix --no-interactive >"$TMP/relative-skills.log" 2>&1; then
  echo 'Relative REASONIX_SKILLS_DIR was silently accepted' >&2; exit 1
fi
# These names never overwrite the inline profile, including a reasonix-prefixed agent.
"$CONVERT" --tool antigravity >/dev/null
"$INSTALL" --tool antigravity,reasonix --no-interactive --agent reasonix-example --path "$HOME/shared" >/dev/null
[[ -f "$HOME/shared/agency-reasonix-example/SKILL.md" && -f "$HOME/shared/$profile/SKILL.md" ]]
if grep -q '^runAs:' "$HOME/shared/agency-reasonix-example/SKILL.md"; then echo 'Inline skill gained runAs' >&2; exit 1; fi
grep -q '^runAs: subagent$' "$HOME/shared/$profile/SKILL.md"
"$INSTALL" --tool reasonix --no-interactive --dry-run --path "$HOME/dry" >/dev/null
[[ ! -e "$HOME/dry" ]]
"$INSTALL" --tool reasonix --no-interactive --link --path "$HOME/linked" >/dev/null
[[ -L "$HOME/linked/$profile/SKILL.md" ]]
printf 'foreign content\n' > "$HOME/foreign.md"
mkdir -p "$HOME/foreign-dest/$profile"
ln -s "$HOME/foreign.md" "$HOME/foreign-dest/$profile/SKILL.md"
"$INSTALL" --tool reasonix --no-interactive --path "$HOME/foreign-dest" >/dev/null
[[ -L "$HOME/foreign-dest/$profile/SKILL.md" && "$(cat "$HOME/foreign.md")" == 'foreign content' ]]
mkdir -p "$HOME/foreign-dir" "$HOME/dir-dest"
ln -s "$HOME/foreign-dir" "$HOME/dir-dest/$profile"
"$INSTALL" --tool reasonix --no-interactive --path "$HOME/dir-dest" >/dev/null
[[ ! -e "$HOME/foreign-dir/SKILL.md" ]]
# The helper branches are deterministic fixtures, not native Windows validation.
mkdir -p "$TMP/bin"
cat > "$TMP/bin/uname" <<'EOF'
#!/bin/sh
printf 'MINGW64_NT\n'
EOF
cat > "$TMP/bin/cygpath" <<'EOF'
#!/bin/sh
[ "$1" = '-u' ] && [ "$2" = '--' ] || exit 1
printf '%s\n' "$3" >> "$REASONIX_TEST_PATH_LOG"
printf '%s/reasonix\n' "$REASONIX_TEST_ROAMING"
EOF
chmod +x "$TMP/bin/uname" "$TMP/bin/cygpath"
PATH="$TMP/bin:$PATH" APPDATA='C:\Users\Example\AppData\Roaming' REASONIX_TEST_PATH_LOG="$TMP/path.log" REASONIX_TEST_ROAMING="$HOME/windows" "$INSTALL" --tool reasonix --no-interactive >/dev/null
[[ -f "$HOME/windows/reasonix/skills/$profile/SKILL.md" ]]
grep -Fq 'C:\Users\Example\AppData\Roaming/reasonix' "$TMP/path.log"
# With Windows detection but no converter, fail clearly instead of guessing HOME.
rm "$TMP/bin/cygpath"
if ! command -v cygpath >/dev/null 2>&1; then
  if PATH="$TMP/bin:$PATH" APPDATA='C:\Users\Example\AppData\Roaming' "$INSTALL" --tool reasonix --no-interactive >"$TMP/no-cygpath.log" 2>&1; then
    echo 'Windows home guessed without cygpath' >&2; exit 1
  fi
  grep -q -- '--path' "$TMP/no-cygpath.log"
fi
printf '#!/bin/sh\nprintf "Linux\\n"\n' > "$TMP/bin/uname"
HOME="$TMP/wsl-home" PATH="$TMP/bin:$PATH" APPDATA='C:\Users\Example\AppData\Roaming' "$INSTALL" --tool reasonix --no-interactive >/dev/null
[[ -f "$TMP/wsl-home/.reasonix/skills/$profile/SKILL.md" ]]
# Name limits are checked before removing prior valid generated products.
name48="$(printf '%048d' 0 | tr 0 a)"
write_agent "$name48"
"$CONVERT" --tool reasonix >/dev/null
previous="$repo/integrations/reasonix/reasonix-agency-$name48/SKILL.md"
[[ -f "$previous" ]]
previous_sum="$(cksum < "$previous")"
write_agent "${name48}a"
if "$CONVERT" --tool reasonix >"$TMP/long-name.log" 2>&1; then
  echo 'A 65-character profile name was accepted' >&2; exit 1
fi
[[ -f "$previous" && "$(cksum < "$previous")" == "$previous_sum" ]]
write_agent 'Reasonix Example'
rm -rf "$repo/integrations/reasonix"
if "$INSTALL" --tool reasonix --no-interactive --no-convert --path "$HOME/no-convert" >"$TMP/no-convert.log" 2>&1; then
  echo '--no-convert accepted missing generated profiles' >&2; exit 1
fi
"$INSTALL" --tool reasonix --no-interactive --path "$HOME/auto" >/dev/null
[[ -f "$HOME/auto/$profile/SKILL.md" ]]
echo 'PASSED: Reasonix format, namespace, destinations, selection and ownership'
