"""Shadow Account — font handling for PDF rendering.

Tries to guarantee that Chinese characters render; falls back to DejaVu Sans
(English-only, logs a warning) when CJK resources are unavailable. Matplotlib
and weasyprint both consume ``cjk_font_path()`` or at least see the family
name via ``apply_matplotlib_cjk_font``.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_NOTO_URL = (
    "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/"
    "NotoSansCJKsc-Regular.otf"
)
_FONT_NAME = "NotoSansCJKsc-Regular.otf"
_FALLBACK_FAMILY = "DejaVu Sans"


def fonts_dir() -> Path:
    """Return the Shadow Account fonts cache dir (auto-created)."""
    d = Path.home() / ".vibe-trading" / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _system_cjk_candidates() -> list[Path]:
    """Enumerate locally-installed CJK fonts we can reuse without downloading."""
    candidates: list[Path] = []
    env = os.environ
    windir = env.get("WINDIR") or env.get("SystemRoot")
    if windir:
        win_fonts = Path(windir) / "Fonts"
        for name in (
            "msyh.ttc", "msyh.ttf", "msyhbd.ttc",
            "simhei.ttf", "simsun.ttc", "simkai.ttf",
            "NotoSansCJK-Regular.ttc",
        ):
            candidates.append(win_fonts / name)
    for p in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ):
        candidates.append(Path(p))
    return candidates


def cjk_font_path(*, allow_download: bool = True, timeout: float = 10.0) -> Optional[Path]:
    """Resolve a CJK font file path.

    Resolution order:
        1. Cached copy in ``fonts_dir()``.
        2. First available system font from ``_system_cjk_candidates``.
        3. Download Noto CJK (optional).

    Returns ``None`` when every option fails — callers should then fall
    back to the DejaVu family.
    """
    cached = fonts_dir() / _FONT_NAME
    if cached.exists() and cached.stat().st_size > 0:
        return cached

    for candidate in _system_cjk_candidates():
        if candidate.exists():
            try:
                shutil.copy(candidate, cached)
                return cached
            except OSError as exc:
                logger.debug("Failed to cache system font %s: %s", candidate, exc)

    if not allow_download:
        return None

    try:
        import urllib.request
        req = urllib.request.Request(_NOTO_URL, headers={"User-Agent": "vibe-trading"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            cached.write_bytes(resp.read())
        if cached.stat().st_size > 0:
            return cached
    except Exception as exc:  # pragma: no cover — network-dependent
        logger.warning("CJK font download failed (%s); falling back to DejaVu.", exc)

    return None


def apply_matplotlib_cjk_font() -> str:
    """Configure matplotlib's default font family.

    Returns the family name actually installed (``"sans-serif"`` meaning the
    CJK face is resolved, or ``_FALLBACK_FAMILY`` when we gave up).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # safe for headless rendering
        from matplotlib import font_manager as fm
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover — matplotlib optional
        logger.warning("matplotlib unavailable: %s", exc)
        return _FALLBACK_FAMILY

    path = cjk_font_path()
    if path is None:
        plt.rcParams["font.family"] = _FALLBACK_FAMILY
        return _FALLBACK_FAMILY

    try:
        fm.fontManager.addfont(str(path))
        prop = fm.FontProperties(fname=str(path))
        family = prop.get_name()
        plt.rcParams["font.family"] = family
        plt.rcParams["axes.unicode_minus"] = False
        return family
    except Exception as exc:
        logger.warning("Failed to register %s with matplotlib: %s", path, exc)
        plt.rcParams["font.family"] = _FALLBACK_FAMILY
        return _FALLBACK_FAMILY


def cjk_css_font_face() -> str:
    """Emit an ``@font-face`` CSS block weasyprint can bundle.

    Returns an empty string if no CJK font is resolvable.
    """
    path = cjk_font_path()
    if path is None:
        return ""
    uri = path.resolve().as_uri()
    return (
        "@font-face {\n"
        "  font-family: 'Shadow CJK';\n"
        f"  src: url('{uri}');\n"
        "}\n"
    )
