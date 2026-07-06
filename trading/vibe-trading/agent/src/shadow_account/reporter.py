"""Shadow Account — 8-section report rendering (HTML + optional PDF).

The pipeline:
    ShadowProfile + ShadowBacktestResult (+ optional today signals)
      → `_build_sections`        build a strict dict for the template
      → `_render_charts`         matplotlib PNG files on disk
      → Jinja2 render HTML
      → weasyprint → PDF (or HTML-only if weasyprint unusable)

Design:
    * No hard dependency on weasyprint at import time — if importing or
      rendering fails, we keep the HTML artifact and return its path.
    * Charts are optional — any matplotlib failure downgrades gracefully
      (that section just omits its `<img>`).
    * Layout/style live in `templates/shadow_report.{html,css}`; this module
      only decides *what* data to feed them.
"""

from __future__ import annotations

import logging
from base64 import b64encode
from dataclasses import asdict
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.shadow_account.fonts import apply_matplotlib_cjk_font, cjk_css_font_face
from src.shadow_account.models import ShadowBacktestResult, ShadowProfile
from src.shadow_account.storage import reports_dir

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_HTML_TEMPLATE = "shadow_report.html"
_CSS_TEMPLATE = "shadow_report.css"

_MARKET_LABELS = {
    "china_a": "China A-share",
    "us": "US equity",
    "hk": "HK equity",
    "crypto": "Crypto",
    "other": "Other",
}

_REASON_LABELS = {
    "rule_violation": "Outside any shadow rule",
    "early_exit": "Exited winner too early",
    "late_exit": "Held loser too long",
}


# ---------------- Public API ----------------

def render_shadow_report(
    profile: ShadowProfile,
    backtest_result: ShadowBacktestResult,
    *,
    today_signals: list[dict[str, Any]] | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Render the full Shadow Account report.

    Returns:
        Dict with keys:
            ``html_path``  : rendered HTML (always present)
            ``pdf_path``   : PDF path (present iff weasyprint succeeded)
            ``sections``   : structured payload (for frontend preview)
            ``engine``     : "weasyprint" | "html-only"
    """
    output_dir = Path(output_dir) if output_dir else reports_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Matplotlib setup must happen before any chart renders.
    apply_matplotlib_cjk_font()

    assets_dir = output_dir / f"{profile.shadow_id}_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    charts = _render_charts(profile, backtest_result, assets_dir)

    sections = _build_sections(profile, backtest_result, today_signals or [])
    css = _load_css()

    html = _env().get_template(_HTML_TEMPLATE).render(
        css=css,
        charts=charts,
        market_labels=_MARKET_LABELS,
        reason_labels=_REASON_LABELS,
        **sections,
    )
    html_path = output_dir / f"{profile.shadow_id}.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path, engine = _try_render_pdf(html, output_dir, profile.shadow_id)

    return {
        "html_path": str(html_path),
        "pdf_path": str(pdf_path) if pdf_path else None,
        "sections": sections,
        "engine": engine,
    }


# ---------------- Section data ----------------

def _build_sections(
    profile: ShadowProfile,
    result: ShadowBacktestResult,
    today_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble the strict payload the Jinja template consumes.

    The template expects numeric values for any metrics it formats with
    ``%f`` — so we strip out non-numeric leak-throughs (e.g. ``error``
    strings inserted when the backtest runner failed). The error is
    preserved separately under ``combined_error`` so the template can
    surface it explicitly.
    """
    combined_numeric, combined_error = _split_metrics(result.combined or {})
    per_market_numeric = {
        market: _split_metrics(metrics or {})[0]
        for market, metrics in (result.per_market or {}).items()
    }
    return {
        "profile": profile,
        "combined_metrics": combined_numeric,
        "combined_error": combined_error,
        "per_market_metrics": per_market_numeric,
        "attribution": result.attribution,
        "shadow_pnl": result.shadow_total_pnl,
        "real_pnl": result.real_total_pnl,
        "delta_pnl": result.delta_pnl,
        "today_signals": today_signals,
    }


def _split_metrics(metrics: dict[str, Any]) -> tuple[dict[str, float], str]:
    """Partition a metrics dict into (numeric, error_message)."""
    numeric: dict[str, float] = {}
    error_parts: list[str] = []
    for key, value in metrics.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            numeric[key] = float(value)
        elif isinstance(value, str):
            error_parts.append(f"{key}: {value}")
    return numeric, " | ".join(error_parts)


# ---------------- Charts ----------------

def _render_charts(
    profile: ShadowProfile,
    result: ShadowBacktestResult,
    assets_dir: Path,
) -> dict[str, str]:
    """Render all charts and return a map section → file URI.

    Any failure is logged and the affected chart is dropped from the map.
    """
    charts: dict[str, str] = {}
    for name, renderer in (
        ("equity_curve", lambda p: _render_equity_curve(result, p)),
        ("per_market_bar", lambda p: _render_per_market_bar(result, p)),
        ("attribution_waterfall", lambda p: _render_attribution_waterfall(result, p)),
    ):
        path = assets_dir / f"{name}.png"
        try:
            renderer(path)
        except Exception as exc:
            logger.warning("Chart %s failed to render: %s", name, exc)
            continue
        if path.exists() and path.stat().st_size > 0:
            charts[name] = path.resolve().as_uri()
    return charts


def _render_equity_curve(result: ShadowBacktestResult, path: Path) -> None:
    curve = result.equity_curves.get("combined") or []
    if not curve:
        return
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 3), dpi=150)
    dates = [pt[0] for pt in curve]
    values = [pt[1] for pt in curve]
    ax.plot(dates, values, color="#1f7a3a", linewidth=1.3)
    ax.fill_between(dates, values, color="#1f7a3a", alpha=0.08)
    ax.set_title("Shadow — Portfolio Equity Curve")
    ax.set_xlabel("")
    ax.set_ylabel("Equity")
    ax.grid(True, linestyle=":", alpha=0.4)
    # Too many x-ticks looks cluttered; sample down.
    if len(dates) > 8:
        step = max(1, len(dates) // 8)
        ax.set_xticks([dates[i] for i in range(0, len(dates), step)])
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _render_per_market_bar(result: ShadowBacktestResult, path: Path) -> None:
    if not result.per_market:
        return
    import matplotlib.pyplot as plt

    markets = list(result.per_market.keys())
    sharpes = [result.per_market[m].get("sharpe", 0.0) for m in markets]
    labels = [_MARKET_LABELS.get(m, m) for m in markets]

    fig, ax = plt.subplots(figsize=(8, 3), dpi=150)
    bars = ax.bar(labels, sharpes, color="#4a5fb0")
    ax.axhline(0, color="#8a8f99", linewidth=0.8)
    ax.set_title("Sharpe by Market")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    for bar, value in zip(bars, sharpes):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _render_attribution_waterfall(result: ShadowBacktestResult, path: Path) -> None:
    attr = result.attribution
    components = [
        ("Real PnL", result.real_total_pnl),
        ("Noise Trades", attr.noise_trades_pnl),
        ("Early Exit", attr.early_exit_pnl),
        ("Late Exit", attr.late_exit_pnl),
        ("Overtrading", attr.overtrading_pnl),
        ("Missed Signals", attr.missed_signals_pnl),
        ("Shadow PnL", result.shadow_total_pnl),
    ]
    if all(value == 0.0 for _, value in components):
        return
    import matplotlib.pyplot as plt

    labels = [c[0] for c in components]
    values = [c[1] for c in components]
    # Waterfall bases: cumulative start for the intermediate bars.
    bases = [0.0]
    running = values[0]
    for v in values[1:-1]:
        bases.append(running)
        running += v
    bases.append(0.0)

    accent = "#4a5fb0"
    pos = "#1f7a3a"
    neg = "#c1392b"
    grid = "#8a8f99"
    bg = "#ffffff"

    colors = []
    for idx, v in enumerate(values):
        if idx in (0, len(values) - 1):
            colors.append(accent)
        else:
            colors.append(pos if v > 0 else neg)

    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=150, facecolor=bg)
    ax.bar(labels, values, bottom=bases, color=colors, edgecolor="none", width=0.55)
    ax.axhline(0, color=grid, linewidth=0.8)
    ax.set_title("Delta Attribution (positive = shadow would outperform)")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)
    plt.setp(ax.get_xticklabels(), rotation=18, ha="right")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=bg)
    plt.close(fig)


# ---------------- Templating ----------------

def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _load_css() -> str:
    """Load CSS, prepending a CJK ``@font-face`` if we have a font."""
    css = (_TEMPLATES_DIR / _CSS_TEMPLATE).read_text(encoding="utf-8")
    font_face = cjk_css_font_face()
    return font_face + "\n" + css


def _try_render_pdf(
    html: str, output_dir: Path, shadow_id: str,
) -> tuple[Path | None, str]:
    """Render PDF via weasyprint, returning (path|None, engine_name)."""
    try:
        from weasyprint import HTML  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover — import-level failure
        logger.warning("weasyprint unavailable (%s); HTML-only output.", exc)
        return None, "html-only"

    pdf_path = output_dir / f"{shadow_id}.pdf"
    try:
        HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf(str(pdf_path))
    except Exception as exc:
        logger.warning("weasyprint render failed (%s); HTML-only output.", exc)
        if pdf_path.exists():
            try:
                pdf_path.unlink()
            except OSError:
                pass
        return None, "html-only"
    return pdf_path, "weasyprint"


# ---------------- Convenience ----------------

def embed_image_as_data_uri(path: Path) -> str:
    """Inline an image as a data URI (useful when file URIs are rejected)."""
    blob = Path(path).read_bytes()
    encoded = b64encode(blob).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# Keep this helper exported to simplify downstream inspection.
def result_as_dict(result: ShadowBacktestResult) -> dict[str, Any]:
    """Dict-serialize a backtest result (handy for frontend debugging)."""
    return asdict(result)
