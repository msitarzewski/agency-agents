#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib.sh"
fail() { echo "FAIL: $*" >&2; exit 1; }
LANG=en_US.UTF-8 LC_ALL=C LC_CTYPE= supports_unicode \
  && fail 'LC_ALL=C must override a UTF-8 LANG'
LANG=en_US.UTF-8 LC_ALL= LC_CTYPE=C supports_unicode \
  && fail 'LC_CTYPE=C must override a UTF-8 LANG'
LANG=C LC_ALL=en_US.UTF-8 LC_CTYPE=C supports_unicode \
  || fail 'UTF-8 LC_ALL must override C in lower-priority variables'
LANG=C LC_ALL= LC_CTYPE=en_US.UTF-8 supports_unicode \
  || fail 'UTF-8 LC_CTYPE must override C LANG'
LANG=en_US.UTF-8 LC_ALL= LC_CTYPE= supports_unicode \
  || fail 'LANG must supply the fallback when category overrides are empty'
LANG=C LC_ALL= LC_CTYPE= supports_unicode && fail 'C fallback must use ASCII'
LANG= LC_ALL= LC_CTYPE= supports_unicode && fail 'unset/empty locales must use ASCII'
LANG=en_US.UTF-8 LC_ALL=C LC_CTYPE= init_ansi
[[ "$BX_TL" == '+' && "$GLYPH_ON" == 'x' ]] \
  || fail 'ASCII locale must select ASCII frame and checkbox glyphs'
LANG=C LC_ALL=en_US.UTF-8 LC_CTYPE= init_ansi
[[ "$BX_TL" == '╭' && "$GLYPH_ON" == '✓' ]] \
  || fail 'UTF-8 override must retain Unicode frame and checkbox glyphs'
echo 'PASS: locale precedence and actual ASCII/Unicode glyph selection'
