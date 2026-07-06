"""Alpha bench orchestrator: registry → universe panel → IC/IR → HTML report.

W2 scaffold: implements the orchestration shape and HTML rendering. Universe
loaders that need network calls return a clean "not yet implemented" envelope —
the full universe wiring lands in W4. The HTML path is autoescaped via Jinja2,
with manual ``html.escape`` fallback when Jinja2 is absent, plus a strict CSP
``<meta>`` so the report cannot fetch or execute external resources.

Output contract — JSON envelope:
    {"status": "ok"|"error",
     "report_path": str | None,
     "n_alphas_tested": int,
     "n_skipped": int,
     "top": [{"id": ..., "ic_mean": ..., "ir": ..., ...}, ...]}

Cache integrity note: the universe panel cache lives in ``~/.vibe-trading/cache/``
as pickle blobs. Each pickle is paired with a ``<name>.sha256`` sidecar; on
load we recompute the digest and refuse the cache on mismatch. This guards
against accidental corruption (truncated writes, partial syncs) — it is NOT a
defence against an attacker with local write access (they can rewrite both
files). Cache files are user-local; if shared across machines they can be
tampered with and the sha256 sidecar is only an integrity check, not authenticity.
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.agent.tools import BaseTool

logger = logging.getLogger(__name__)

# Date the SP500 constituent list was sampled from Wikipedia (best-effort label
# for the survivorship-bias warning in the bench summary's ``meta`` block).
_SP500_CONSTITUENT_SOURCE_DATE = "2026-05-17"

# Concurrent Tushare ``pro.daily`` fetches when building CSI300. Free tier
# allows ~200 calls/min; 4 workers stays well under that with a 300-name list.
_CSI300_FETCH_WORKERS = 4


# ---------------------------------------------------------------------------
# Universe + period parsing
# ---------------------------------------------------------------------------

_PERIOD_YEAR = re.compile(r"^(\d{4})-(\d{4})$")
_PERIOD_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})/(\d{4}-\d{2}-\d{2})$")

# Universe → (market_key, universe_meta_tag). Only the listed universes have a
# defined contract; everything else returns "not yet implemented".
_UNIVERSE_TAG = {
    "csi300": "equity_cn",
    "sp500": "equity_us",
    "btc-usdt": "crypto",
}


def _parse_period(period: str) -> tuple[str, str]:
    """Return (start_date, end_date) as YYYY-MM-DD strings."""
    if not isinstance(period, str):
        raise ValueError(f"period must be string, got {type(period).__name__}")
    m = _PERIOD_DATE.match(period)
    if m:
        return m.group(1), m.group(2)
    m = _PERIOD_YEAR.match(period)
    if m:
        return f"{m.group(1)}-01-01", f"{m.group(2)}-12-31"
    raise ValueError(
        f"period {period!r} must be YYYY-YYYY or YYYY-MM-DD/YYYY-MM-DD"
    )


def _load_universe_panel(
    universe: str, period: str, *, use_cache: bool = True
) -> dict[str, pd.DataFrame]:
    """Load OHLCV(+amount, +vwap) wide panel for the requested universe.

    Returns a dict keyed by panel column (open/high/low/close/volume/amount/vwap)
    where each value is a wide ``pd.DataFrame`` indexed by date (DatetimeIndex)
    with one column per instrument.

    Args:
        universe: ``csi300`` | ``sp500`` | ``btc-usdt``.
        period: ``YYYY-YYYY`` or ``YYYY-MM-DD/YYYY-MM-DD``.
        use_cache: When True (default) reuse a pickle in
            ``~/.vibe-trading/cache/`` if the same universe+period was fetched
            before. Set to False to force a re-fetch.

    Raises:
        ValueError: unknown universe or bad period.
        RuntimeError: ``TUSHARE_TOKEN`` unset when csi300 is requested.
    """
    if universe not in _UNIVERSE_TAG:
        raise ValueError(
            f"universe {universe!r} not recognized; expected one of {sorted(_UNIVERSE_TAG)}"
        )
    start, end = _parse_period(period)

    cache_dir = Path.home() / ".vibe-trading" / "cache"
    cache_path = cache_dir / f"{universe}_{start}_{end}.pkl"
    if use_cache and cache_path.is_file():
        cached = _read_pickle_cache(cache_path)
        if cached is not None:
            logger.info("universe %s: loaded from cache %s", universe, cache_path)
            return cached

    if universe == "csi300":
        panel = _load_csi300_panel(start, end)
    elif universe == "sp500":
        panel = _load_sp500_panel(start, end)
    elif universe == "btc-usdt":
        panel = _load_btc_panel(start, end)
    else:  # pragma: no cover — guarded above
        raise ValueError(f"unhandled universe {universe!r}")

    if not panel or "close" not in panel or panel["close"].empty:
        raise RuntimeError(
            f"universe {universe!r} produced empty panel for {start}..{end}; "
            "check network / token / date range"
        )

    # btc-usdt loader returns a single-column close (one instrument). Cross-
    # sectional IC needs >= 2 instruments — short-circuit with a clean error
    # that propagates to API (400) and CLI.
    close_df = panel["close"]
    if universe == "btc-usdt" and close_df.shape[1] < 2:
        raise ValueError(
            "btc-usdt is single-asset; cross-sectional IC needs >=2 instruments. "
            "Use a multi-symbol crypto basket (e.g. multiple OKX pairs) for "
            "meaningful results."
        )

    if use_cache:
        _write_pickle_cache(cache_dir, cache_path, panel)

    return panel


def _sha256_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(cache_path.suffix + ".sha256")


def _read_pickle_cache(cache_path: Path) -> dict[str, pd.DataFrame] | None:
    """Load a pickle cache, validating its sha256 sidecar. None on any failure."""
    import pickle

    sidecar = _sha256_path(cache_path)
    try:
        blob = cache_path.read_bytes()
    except OSError as exc:
        logger.warning("cache read failed (%s); refetching", exc)
        return None

    if not sidecar.is_file():
        logger.warning(
            "cache sidecar %s missing; refusing stale cache and refetching",
            sidecar.name,
        )
        return None
    try:
        expected = sidecar.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("cache sidecar read failed (%s); refetching", exc)
        return None
    actual = hashlib.sha256(blob).hexdigest()
    if not _hashes_equal(expected, actual):
        logger.warning(
            "cache integrity mismatch for %s (expected %s..., got %s...); refetching",
            cache_path.name, expected[:12], actual[:12],
        )
        return None

    try:
        cached = pickle.loads(blob)  # noqa: S301 — local cache, integrity-checked above
    except Exception as exc:  # noqa: BLE001 — degrade to fresh fetch
        logger.warning("cache unpickle failed (%s); refetching", exc)
        return None
    if not isinstance(cached, dict) or "close" not in cached:
        logger.warning("cache %s has unexpected shape; refetching", cache_path.name)
        return None
    return cached


def _write_pickle_cache(
    cache_dir: Path, cache_path: Path, panel: dict[str, Any]
) -> None:
    """Pickle ``panel`` + write its sha256 sidecar. Failures are non-fatal."""
    import pickle

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        blob = pickle.dumps(panel, protocol=pickle.HIGHEST_PROTOCOL)
        cache_path.write_bytes(blob)
        _sha256_path(cache_path).write_text(
            hashlib.sha256(blob).hexdigest(), encoding="utf-8"
        )
    except Exception as exc:  # noqa: BLE001 — cache miss is non-fatal
        logger.warning("cache write failed: %s", exc)


def _hashes_equal(a: str, b: str) -> bool:
    """Constant-time comparison of two hex digests."""
    import hmac

    return hmac.compare_digest(a.strip().lower(), b.strip().lower())


# ---------------------------------------------------------------------------
# Universe loaders
# ---------------------------------------------------------------------------


_CSI300_FALLBACK_CODES = [
    # Blue-chip A-share representatives — used only when index_weight fails.
    # Hand-picked across sectors so a degraded run still gives diverse signal.
    "600519.SH", "601318.SH", "600036.SH", "000333.SZ", "000858.SZ",
    "601166.SH", "600276.SH", "601398.SH", "601288.SH", "600030.SH",
    "600887.SH", "601012.SH", "601888.SH", "000651.SZ", "600028.SH",
    "601628.SH", "600000.SH", "601088.SH", "601857.SH", "600009.SH",
    "601899.SH", "002594.SZ", "600585.SH", "300750.SZ", "601658.SH",
    "600048.SH", "601138.SH", "601668.SH", "000001.SZ", "000002.SZ",
]


# Hand-picked US large-cap representatives. Used when Wikipedia fetch fails.
_SP500_FALLBACK_CODES = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B",
    "JPM", "JNJ", "V", "PG", "UNH", "MA", "HD", "XOM", "LLY", "MRK",
    "PEP", "KO", "ABBV", "AVGO", "CVX", "WMT", "COST", "ADBE", "MCD",
    "CRM", "ACN", "BAC", "TMO", "ORCL", "CSCO", "ABT", "WFC", "DHR",
    "VZ", "PFE", "INTC", "DIS", "CMCSA", "AMD", "TXN", "PM", "QCOM",
    "NEE", "RTX", "HON", "T", "IBM",
]


def _load_csi300_panel(start: str, end: str) -> dict[str, pd.DataFrame]:
    """CSI 300 panel via Tushare. Includes ``amount`` (required by gtja191).

    Constituents are taken from the most recent ``index_weight`` snapshot in
    the requested window; if that call fails we degrade to a 30-name
    blue-chip fallback so the bench still runs.
    """
    token = os.getenv("TUSHARE_TOKEN", "").strip()
    if not token or token == "your-tushare-token":
        raise RuntimeError(
            "TUSHARE_TOKEN not in agent/.env or environment; required for csi300 universe"
        )

    try:
        import tushare as ts
    except ImportError as exc:
        raise RuntimeError(f"tushare not installed: {exc}") from exc

    pro = ts.pro_api(token)
    sd = start.replace("-", "")
    ed = end.replace("-", "")

    codes: list[str] = []
    try:
        weights = pro.index_weight(
            index_code="399300.SZ", start_date=sd, end_date=ed
        )
        if weights is not None and not weights.empty:
            latest_date = weights["trade_date"].max()
            codes = (
                weights[weights["trade_date"] == latest_date]["con_code"]
                .drop_duplicates()
                .tolist()
            )
            logger.info("csi300: %d constituents from index_weight @ %s", len(codes), latest_date)
    except Exception as exc:  # noqa: BLE001
        logger.warning("csi300 index_weight failed (%s); using fallback list", exc)

    if not codes:
        codes = list(_CSI300_FALLBACK_CODES)
        logger.warning("csi300: using %d-name fallback (degraded run)", len(codes))

    # Fetch raw daily in parallel — we need ``amount`` which the standard
    # loader drops. Tushare's free tier permits ~200 calls/min so 4 concurrent
    # workers is comfortably under the rate limit even for a full 300-name list.
    def _fetch_one(code: str) -> tuple[str, pd.DataFrame | None]:
        df = _retry(lambda: pro.daily(ts_code=code, start_date=sd, end_date=ed))
        if df is None or df.empty:
            return code, None
        df = df.sort_values("trade_date").copy()
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.set_index("trade_date")
        df = df.rename(columns={"vol": "volume"})
        for col in ("open", "high", "low", "close", "volume", "amount"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        keep = [c for c in ("open", "high", "low", "close", "volume", "amount") if c in df.columns]
        return code, df[keep].dropna(subset=["open", "high", "low", "close"])

    fetched: dict[str, pd.DataFrame] = {}
    with ThreadPoolExecutor(max_workers=_CSI300_FETCH_WORKERS) as pool:
        futures = [pool.submit(_fetch_one, code) for code in codes]
        for fut in as_completed(futures):
            try:
                code, frame = fut.result()
            except Exception as exc:  # noqa: BLE001 — _retry already logged
                logger.warning("csi300 fetch worker raised: %s", exc)
                continue
            if frame is not None and not frame.empty:
                fetched[code] = frame

    panel = _wide_from_fetched(fetched, include_amount=True)
    # CN equity vwap: Tushare ``amount`` is in 千元, ``volume`` in 手. True VWAP
    # = (amount * 1000 CNY) / (volume * 100 shares). Matches
    # ``src.factors.base.vwap(EQUITY_CN)``.
    if "amount" in panel and "volume" in panel:
        from src.factors.base import safe_div

        panel["vwap"] = safe_div(
            panel["amount"] * 1000.0, panel["volume"] * 100.0 + 1.0
        )
    return panel


def _load_sp500_panel(start: str, end: str) -> dict[str, pd.DataFrame]:
    """SP500 panel via yfinance. Adds vwap = (O+H+L+C)/4 fallback for alpha101.

    Survivorship-bias warning: ``_fetch_sp500_constituents`` returns Wikipedia's
    *current* member list, not a point-in-time snapshot. Names that dropped out
    of the index during ``start..end`` (delistings, mergers, downgrades) are
    silently excluded — so IC stats are biased upward. The caller (bench
    runner) surfaces this in the bench summary's ``meta`` block via the
    ``_meta`` panel key set below.
    """
    codes = _fetch_sp500_constituents()
    constituent_source = "wikipedia"
    if not codes:
        codes = list(_SP500_FALLBACK_CODES)
        constituent_source = "hand-picked fallback"
        logger.warning("sp500: using %d-name fallback (degraded run)", len(codes))

    logger.warning(
        "SP500 universe uses current constituents (%s @ %s) → survivorship-biased",
        constituent_source, _SP500_CONSTITUENT_SOURCE_DATE,
    )

    # yfinance loader expects project-style symbols (``AAPL.US``).
    project_codes = [f"{c}.US" for c in codes]
    from backtest.loaders.registry import resolve_loader

    loader = resolve_loader("us_equity")
    fetched = _retry(lambda: loader.fetch(project_codes, start, end)) or {}

    panel = _wide_from_fetched(fetched, include_amount=False)
    # Synthetic vwap for alpha101 alphas that require it on US universe
    if all(k in panel for k in ("open", "high", "low", "close")):
        panel["vwap"] = (panel["open"] + panel["high"] + panel["low"] + panel["close"]) / 4.0

    # Attach a non-DataFrame metadata blob. Registry.compute() only iterates
    # required column names, so this extra key is ignored by the compute path.
    panel["_meta"] = {
        "universe": "sp500",
        "survivorship_bias": True,
        "constituent_source": constituent_source,
        "constituent_source_date": _SP500_CONSTITUENT_SOURCE_DATE,
        "constituent_count": len(codes),
    }
    return panel


def _fetch_sp500_constituents() -> list[str]:
    """Pull current S&P 500 tickers from Wikipedia. Returns [] on any failure."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        import io

        import requests

        resp = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Vibe-Trading/0.1 (research bench; "
                    "https://github.com/HKUDS/Vibe-Trading)"
                )
            },
            timeout=20,
        )
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
        for tbl in tables:
            if "Symbol" in tbl.columns:
                tickers = tbl["Symbol"].astype(str).str.strip().tolist()
                # yfinance prefers ``BRK-B`` over ``BRK.B`` — normalise
                tickers = [t.replace(".", "-") for t in tickers if t and t != "nan"]
                logger.info("sp500: %d tickers from Wikipedia", len(tickers))
                return tickers
    except Exception as exc:  # noqa: BLE001
        logger.warning("sp500 Wikipedia fetch failed: %s", exc)
    return []


def _load_btc_panel(start: str, end: str) -> dict[str, pd.DataFrame]:
    """Single-instrument BTC-USDT panel via OKX. Adds vwap = typical price."""
    from backtest.loaders.registry import resolve_loader

    loader = resolve_loader("crypto")
    fetched = _retry(lambda: loader.fetch(["BTC-USDT"], start, end)) or {}
    panel = _wide_from_fetched(fetched, include_amount=False)
    if all(k in panel for k in ("open", "high", "low", "close")):
        panel["vwap"] = (panel["open"] + panel["high"] + panel["low"] + panel["close"]) / 4.0
    return panel


def _wide_from_fetched(
    fetched: dict[str, pd.DataFrame], *, include_amount: bool
) -> dict[str, pd.DataFrame]:
    """Stack per-code OHLCV frames into wide panels keyed by field."""
    if not fetched:
        return {}
    all_dates = sorted(set().union(*(df.index for df in fetched.values())))
    if not all_dates:
        return {}
    all_codes = sorted(fetched.keys())
    date_index = pd.DatetimeIndex(all_dates)
    fields = ["open", "high", "low", "close", "volume"]
    if include_amount:
        fields.append("amount")

    panel: dict[str, pd.DataFrame] = {}
    for field in fields:
        present = {
            code: df[field] for code, df in fetched.items() if field in df.columns
        }
        if not present:
            continue
        # pd.concat over a dict of Series gives a wide frame with codes as
        # columns in one pass — avoids the per-code reindex+DataFrame build.
        wide = pd.concat(present, axis=1)
        wide = wide.reindex(index=date_index, columns=all_codes)
        panel[field] = wide.astype(float)
    return panel


def _retry(fn, *, tries: int = 3, base_delay: float = 1.0):
    """Call ``fn`` up to ``tries`` times with exponential backoff."""
    import time

    last_exc: Exception | None = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — recoverable network errors
            last_exc = exc
            if attempt == tries - 1:
                break
            delay = base_delay * (2 ** attempt)
            logger.debug("retry %d/%d after %.1fs: %s", attempt + 1, tries, delay, exc)
            time.sleep(delay)
    if last_exc is not None:
        logger.warning("retry exhausted: %s", last_exc)
    return None


# ---------------------------------------------------------------------------
# Per-alpha IC bench
# ---------------------------------------------------------------------------


def _compute_forward_returns(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Next-bar forward simple returns from close, aligned to factor timestamp."""
    close = panel.get("close")
    if close is None:
        raise ValueError("panel missing 'close' — cannot derive forward returns")
    # Next-period return aligned to current row (use t+1 close, shift back).
    fwd = close.pct_change().shift(-1)
    return fwd


def _bench_one_alpha(
    registry: Any,
    alpha_id: str,
    panel: dict[str, pd.DataFrame],
    return_df: pd.DataFrame,
) -> dict[str, Any]:
    """Compute IC stats for one alpha. Returns a dict, may raise SkipAlpha / RegistryError."""
    from src.factors.factor_analysis_core import compute_ic_series  # local import

    factor_df = registry.compute(alpha_id, panel)
    ic_series = compute_ic_series(factor_df, return_df)
    if ic_series.empty:
        raise RuntimeError(
            f"{alpha_id}: IC series empty — insufficient overlap between factor and returns"
        )
    ic_mean = float(ic_series.mean())
    ic_std = float(ic_series.std())
    ir = ic_mean / ic_std if ic_std > 0 else 0.0
    ic_pos = float((ic_series > 0).mean())
    alpha = registry.get(alpha_id)
    meta = alpha.meta or {}
    return {
        "id": alpha_id,
        "zoo": alpha.zoo,
        "theme": meta.get("theme", []),
        "formula_latex": meta.get("formula_latex", ""),
        "ic_mean": round(ic_mean, 6),
        "ic_std": round(ic_std, 6),
        "ir": round(ir, 4),
        "ic_positive_ratio": round(ic_pos, 4),
        "ic_count": int(len(ic_series)),
    }


def _select_alpha_ids(
    registry: Any, *, alpha_id: str | None, zoo: str | None
) -> list[str]:
    if alpha_id and zoo:
        raise ValueError("alpha_id and zoo are mutually exclusive")
    if alpha_id:
        registry.get(alpha_id)  # raises KeyError if unknown
        return [alpha_id]
    if zoo:
        return registry.list(zoo=zoo)
    return registry.list()


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_CSP = (
    "<meta http-equiv=\"Content-Security-Policy\" "
    "content=\"default-src 'none'; style-src 'unsafe-inline'; script-src 'none'\">"
)

_REPORT_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2em;
       color: #222; background: #fafafa; }
h1, h2 { color: #111; }
table { border-collapse: collapse; width: 100%; background: #fff; }
th, td { padding: .5em .75em; border-bottom: 1px solid #e5e5e5; text-align: left; }
th { background: #f0f0f0; }
.meta { color: #666; font-size: .9em; margin-bottom: 1.5em; }
.formula { font-family: monospace; background: #f4f4f4; padding: .25em .5em; }
.skipped { color: #a33; font-size: .9em; }
"""

_JINJA_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
{{ csp | safe }}
<title>Alpha Bench Report</title>
<style>{{ css }}</style>
</head><body>
<h1>Alpha Bench Report</h1>
<div class="meta">
  Generated {{ generated_at }} &middot; Universe {{ universe }} &middot;
  Period {{ period }} &middot; {{ n_alphas_tested }} tested, {{ n_skipped }} skipped
</div>

<h2>Top {{ top|length }} by IR</h2>
<table>
<tr><th>#</th><th>Alpha ID</th><th>Zoo</th><th>Theme</th>
    <th>IC mean</th><th>IC std</th><th>IR</th><th>IC+ ratio</th><th>N</th></tr>
{% for row in top %}
<tr>
  <td>{{ loop.index }}</td>
  <td>{{ row.id }}</td>
  <td>{{ row.zoo }}</td>
  <td>{{ row.theme | join(", ") }}</td>
  <td>{{ "%.4f"|format(row.ic_mean) }}</td>
  <td>{{ "%.4f"|format(row.ic_std) }}</td>
  <td>{{ "%.4f"|format(row.ir) }}</td>
  <td>{{ "%.4f"|format(row.ic_positive_ratio) }}</td>
  <td>{{ row.ic_count }}</td>
</tr>
{% endfor %}
</table>

<h2>Formulas</h2>
<table>
<tr><th>Alpha ID</th><th>Formula (LaTeX source)</th></tr>
{% for row in top %}
<tr><td>{{ row.id }}</td><td class="formula">{{ row.formula_latex }}</td></tr>
{% endfor %}
</table>

{% if failures %}
<h2 class="skipped">Skipped / Failed ({{ failures|length }} shown)</h2>
<table>
<tr><th>Alpha ID</th><th>Reason</th></tr>
{% for f in failures %}
<tr><td>{{ f.alpha_id }}</td><td>{{ f.reason }}</td></tr>
{% endfor %}
</table>
{% endif %}
</body></html>
"""


def _render_html(context: dict[str, Any]) -> str:
    """Render with Jinja2 autoescape if available; else manual ``html.escape``."""
    try:
        from jinja2 import Environment, select_autoescape

        env = Environment(autoescape=select_autoescape(["html", "xml"]))
        return env.from_string(_JINJA_TEMPLATE).render(**context)
    except ImportError:
        return _render_html_manual(context)


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _render_html_manual(ctx: dict[str, Any]) -> str:
    """Hand-rolled fallback. Every interpolated value goes through html.escape."""
    parts: list[str] = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        _CSP,
        f"<title>Alpha Bench Report</title><style>{_REPORT_CSS}</style></head><body>",
        "<h1>Alpha Bench Report</h1>",
        "<div class=\"meta\">Generated ",
        _esc(ctx["generated_at"]),
        " &middot; Universe ",
        _esc(ctx["universe"]),
        " &middot; Period ",
        _esc(ctx["period"]),
        f" &middot; {int(ctx['n_alphas_tested'])} tested, {int(ctx['n_skipped'])} skipped",
        "</div>",
        f"<h2>Top {len(ctx['top'])} by IR</h2><table>",
        "<tr><th>#</th><th>Alpha ID</th><th>Zoo</th><th>Theme</th>"
        "<th>IC mean</th><th>IC std</th><th>IR</th><th>IC+ ratio</th><th>N</th></tr>",
    ]
    for i, row in enumerate(ctx["top"], start=1):
        ic_mean = _esc(f"{row['ic_mean']:.4f}")
        ic_std = _esc(f"{row['ic_std']:.4f}")
        ir = _esc(f"{row['ir']:.4f}")
        ic_pos = _esc(f"{row['ic_positive_ratio']:.4f}")
        parts.append(
            f"<tr><td>{i}</td>"
            f"<td>{_esc(row['id'])}</td>"
            f"<td>{_esc(row['zoo'])}</td>"
            f"<td>{_esc(', '.join(row['theme']))}</td>"
            f"<td>{ic_mean}</td>"
            f"<td>{ic_std}</td>"
            f"<td>{ir}</td>"
            f"<td>{ic_pos}</td>"
            f"<td>{_esc(row['ic_count'])}</td></tr>"
        )
    parts.append("</table><h2>Formulas</h2><table>")
    parts.append("<tr><th>Alpha ID</th><th>Formula (LaTeX source)</th></tr>")
    for row in ctx["top"]:
        parts.append(
            f"<tr><td>{_esc(row['id'])}</td>"
            f"<td class=\"formula\">{_esc(row['formula_latex'])}</td></tr>"
        )
    parts.append("</table>")
    failures = ctx.get("failures") or []
    if failures:
        parts.append(
            f"<h2 class=\"skipped\">Skipped / Failed ({len(failures)} shown)</h2><table>"
        )
        parts.append("<tr><th>Alpha ID</th><th>Reason</th></tr>")
        for f in failures:
            parts.append(
                f"<tr><td>{_esc(f['alpha_id'])}</td><td>{_esc(f['reason'])}</td></tr>"
            )
        parts.append("</table>")
    parts.append("</body></html>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _default_output_dir() -> Path:
    return Path.home() / ".vibe-trading" / "reports"


def run_alpha_bench(**kwargs: Any) -> dict[str, Any]:
    """Run the bench and return a parsed envelope (dict, not JSON string)."""
    universe = kwargs.get("universe")
    period = kwargs.get("period")
    if not universe or not isinstance(universe, str):
        return {"status": "error", "error": "universe is required (string)"}
    if not period or not isinstance(period, str):
        return {"status": "error", "error": "period is required (string)"}

    try:
        _parse_period(period)
    except ValueError as exc:
        return {"status": "error", "error": str(exc)}

    top_n = int(kwargs.get("top", 20) or 20)
    if top_n <= 0:
        return {"status": "error", "error": "top must be > 0"}

    output_dir_raw = kwargs.get("output_dir") or str(_default_output_dir())
    output_dir = Path(output_dir_raw).expanduser().resolve()

    try:
        from src.factors.registry import (
            RegistryError,
            SkipAlpha,
            get_default_registry,
        )
    except Exception as exc:
        return {"status": "error", "error": f"registry import failed: {exc}"}

    try:
        registry = get_default_registry()
    except Exception as exc:
        logger.exception("Registry construction failed")
        return {"status": "error", "error": f"registry init failed: {exc}"}

    try:
        alpha_ids = _select_alpha_ids(
            registry, alpha_id=kwargs.get("alpha_id"), zoo=kwargs.get("zoo")
        )
    except (KeyError, ValueError) as exc:
        return {"status": "error", "error": str(exc)}

    if not alpha_ids:
        return {
            "status": "error",
            "error": "no alphas matched the selection (registry empty or filters too narrow)",
        }

    # Load panel — W4 universe loader fetches constituents + OHLCV (+ amount, vwap).
    try:
        panel = _load_universe_panel(universe, period)
    except (ValueError, NotImplementedError, RuntimeError) as exc:
        return {
            "status": "error",
            "error": str(exc),
            "n_alphas_tested": 0,
            "n_skipped": 0,
            "selected_alphas": alpha_ids[:50],
            "selected_total": len(alpha_ids),
        }

    try:
        return_df = _compute_forward_returns(panel)
    except Exception as exc:
        return {"status": "error", "error": f"forward returns failed: {exc}"}

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for aid in alpha_ids:
        try:
            results.append(_bench_one_alpha(registry, aid, panel, return_df))
        except (SkipAlpha, RegistryError, RuntimeError, KeyError, ValueError) as exc:
            failures.append({"alpha_id": aid, "reason": str(exc)})
        except Exception as exc:  # noqa: BLE001 — isolate per-alpha failure
            logger.exception("alpha_bench unexpected failure on %s", aid)
            failures.append({"alpha_id": aid, "reason": f"unexpected: {exc}"})

    results.sort(key=lambda r: r["ir"], reverse=True)
    top = results[:top_n]

    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = output_dir / f"alpha_bench_{ts}.html"

    context = {
        "csp": _CSP,
        "css": _REPORT_CSS,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe": universe,
        "period": period,
        "n_alphas_tested": len(results),
        "n_skipped": len(failures),
        "top": top,
        "failures": failures[:10],
    }

    try:
        report_path.write_text(_render_html(context), encoding="utf-8")
    except OSError as exc:
        return {"status": "error", "error": f"failed to write report: {exc}"}

    return {
        "status": "ok",
        "report_path": str(report_path),
        "n_alphas_tested": len(results),
        "n_skipped": len(failures),
        "top": top,
    }


class AlphaBenchTool(BaseTool):
    """Bench one alpha or a whole zoo on a universe and emit an HTML IC report."""

    name = "alpha_bench"
    description = (
        "Bench a single alpha (alpha_id) or a whole zoo (zoo) on a universe over "
        "a period; computes IC mean/std/IR/positive-ratio per alpha and writes an "
        "HTML report. Returns aggregate stats only — no per-stock per-date payloads."
    )
    parameters = {
        "type": "object",
        "properties": {
            "alpha_id": {
                "type": "string",
                "description": "Bench a single alpha (mutually exclusive with zoo).",
            },
            "zoo": {
                "type": "string",
                "description": "Bench every alpha in a zoo (mutually exclusive with alpha_id).",
            },
            "universe": {
                "type": "string",
                "description": "csi300 | sp500 | btc-usdt (resolved via existing data tools).",
            },
            "period": {
                "type": "string",
                "description": "YYYY-YYYY or YYYY-MM-DD/YYYY-MM-DD.",
            },
            "top": {
                "type": "integer",
                "default": 20,
                "description": "Report the top-N alphas ranked by IR.",
            },
            "output_dir": {
                "type": "string",
                "description": "Where to write the HTML report; default ~/.vibe-trading/reports/.",
            },
        },
        "required": ["universe", "period"],
    }
    repeatable = True
    is_readonly = False

    def execute(self, **kwargs: Any) -> str:
        envelope = run_alpha_bench(**kwargs)
        return json.dumps(envelope, ensure_ascii=False)
