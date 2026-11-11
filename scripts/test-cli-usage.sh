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
logs = temporary / 'logs'
logs.mkdir()
env = {**os.environ, 'HOME': str(home), 'TMPDIR': str(logs), 'AGENCY_TUI_FORCE': '1'}
for keys in ('q', '\nq', '\n\nq', 'n \n\n\n'):
    result = subprocess.run(
        ['bash', str(scripts / 'install.sh'), '--interactive', '--no-convert'],
        input=keys, text=True, env=env, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, timeout=20 if keys.startswith('n ') else 5,
    )
    assert result.returncode == 0, (keys, result.returncode, result.stderr)
    assert not list(logs.iterdir()), f'closed wizard leaked temporary files for {keys!r}'
print('PASS: cancelling each screen and completing the wizard clean its temporary log')
PY

# A signal handler is deferred while Bash waits for the key-reading child;
# one harmless key releases that wait before checking cleanup.
python3 - "$SCRIPT_DIR" <<'PY'
import os,pathlib,pty,select,shutil,signal,subprocess,sys,tempfile,termios,time
source=pathlib.Path(sys.argv[1])
with tempfile.TemporaryDirectory() as directory:
 root=pathlib.Path(directory);scripts=root/'fixture/scripts';scripts.mkdir(parents=True)
 for name in ('install.sh','lib.sh'):shutil.copy2(source/name,scripts/name)
 shutil.copy2(source.parent/'divisions.json',scripts.parent/'divisions.json');(scripts.parent/'integrations').mkdir()
 home=root/'home';home.mkdir();logs=root/'logs';logs.mkdir()
 for signum,expected in ((signal.SIGINT,130),(signal.SIGTERM,143)):
  master,slave=pty.openpty();saved=termios.tcgetattr(slave)
  env={k:v for k,v in os.environ.items() if k!='AGENCY_TUI_FORCE'};env.update(HOME=str(home),TMPDIR=str(logs),TERM='xterm')
  def reset_signals():
   signal.signal(signal.SIGINT,signal.SIG_DFL);signal.signal(signal.SIGTERM,signal.SIG_DFL)
  child=subprocess.Popen(['bash',str(scripts/'install.sh')],stdin=slave,stdout=slave,stderr=slave,env=env,preexec_fn=reset_signals)
  try:
   output=b'';deadline=time.monotonic()+20
   while b'q quit' not in output and time.monotonic()<deadline:
    if select.select([master],[],[],.1)[0]:output+=os.read(master,65536)
   assert b'q quit' in output,('Wizard did not reach input',output[-500:])
   assert list(logs.iterdir()),'Expected active wizard log'
   os.kill(child.pid,signum);os.write(master,b' ');status=child.wait(timeout=5)
   assert status==expected,(signum,status)
   assert not list(logs.iterdir()),f'Signal {signum} leaked wizard temporary log'
   restored=termios.tcgetattr(slave);mask=termios.ECHO|termios.ICANON
   assert restored[3]&mask==saved[3]&mask
  finally:
   if child.poll() is None:child.kill();child.wait()
   termios.tcsetattr(slave,termios.TCSANOW,saved);os.close(master);os.close(slave)
print('PASS: actual wizard SIGINT/SIGTERM restore terminal, exit 130/143 and remove temporary logs')
PY

for opt in --tool --out --parallel --jobs; do
  grep -q -- "^  $opt " <(bash "$SCRIPT_DIR/convert.sh" --help) \
    || fail "convert.sh --help does not describe $opt"
done

echo "PASS: unknown options exit non-zero with usage on stderr; --help documents every convert.sh option"
