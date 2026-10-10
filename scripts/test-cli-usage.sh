#!/usr/bin/env bash
# convert.sh and install.sh: --help documents every option and exits 0; an
# unknown option exits non-zero with the usage text on stderr.
#
# Both scripts used to call usage() after "Unknown option", and usage() always
# exited 0, so `convert.sh --tol codex` in CI or a wrapper read as success.
# convert.sh's --help also printed a hard-coded line range that stopped above
# --parallel, --jobs and --out.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/agency-cli-usage.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

for script in convert.sh install.sh; do
  status=0
  bash "$SCRIPT_DIR/$script" --no-such-flag > "$tmp/out" 2> "$tmp/err" || status=$?
  [[ "$status" -ne 0 ]] || fail "$script --no-such-flag exited 0"
  grep -q 'Unknown option: --no-such-flag' "$tmp/err" || fail "$script did not name the unknown option on stderr"
  grep -q 'Usage:' "$tmp/err" || fail "$script did not print usage on stderr for an unknown option"
  [[ ! -s "$tmp/out" ]] || fail "$script wrote to stdout for an unknown option"

  bash "$SCRIPT_DIR/$script" --help > "$tmp/help" 2>&1 || fail "$script --help exited non-zero"
  grep -q 'Usage:' "$tmp/help" || fail "$script --help printed no usage"
  ! grep -q 'USAGE-START\|USAGE-END' "$tmp/help" || fail "$script --help printed its sentinel lines"
done

python3 - "$SCRIPT_DIR" "$tmp" <<'PY'
import os
from pathlib import Path
import shutil
import subprocess
import sys

source, temporary = map(Path, sys.argv[1:])
scripts = temporary / 'fixture' / 'scripts'
scripts.mkdir(parents=True)
for name in ('install.sh', 'lib.sh'):
    shutil.copy2(source / name, scripts / name)
shutil.copy2(source.parent / 'divisions.json', scripts.parent / 'divisions.json')
(scripts.parent / 'integrations').mkdir()
home = temporary / 'home'
home.mkdir()
env = {**os.environ, 'HOME': str(home), 'AGENCY_TUI_FORCE': '1'}
for keys in ('', '/', '/x'):
    try:
        result = subprocess.run(
            ['bash', str(scripts / 'install.sh'), '--interactive', '--no-convert'],
            input=keys, text=True,
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(f'installer stayed running after EOF for keys {keys!r}')
    assert result.returncode == 0, (keys, result.returncode, result.stderr)
assert not list(home.iterdir()), 'cancelled wizard installed files'
print('PASS: EOF cancels the wizard, including active searches')
PY

for opt in --tool --out --parallel --jobs; do
  grep -q -- "^  $opt " <(bash "$SCRIPT_DIR/convert.sh" --help) \
    || fail "convert.sh --help does not describe $opt"
done

echo "PASS: unknown options exit non-zero with usage on stderr; --help documents every convert.sh option"
