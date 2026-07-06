"""Pre-fetch market data for symbols mentioned in a swarm's user_vars.

Why this exists
---------------
Swarm workers are LLMs. Without explicit grounding they cheerfully quote
prices from their training data — which is wrong by definition for any
asset that has traded since the model's cutoff. The fix can only be
structural: feed the worker the real recent prices before it starts
reasoning, and tell it those are the only prices it may cite.

What this module does
---------------------
* Scans every value in ``user_vars`` for tokens that match one of the
  data-source-suffixed symbol shapes the loaders already understand
  (``NVDA.US``, ``700.HK``, ``600519.SH``, ``BTC-USDT``, etc.).
* Pulls the last ``DEFAULT_WINDOW_DAYS`` of OHLCV for each detected
  symbol via ``backtest.loaders.registry.resolve_loader`` with
  ``source="auto"``. Failures (delisted ticker, network blip) are
  swallowed per-symbol so they do not poison the whole run.
* Renders a compact markdown block the worker prompt can splice in.

Bare US tickers
---------------
Suffixed symbols are matched verbatim. Bare all-caps tokens (``NVDA``
without ``.US``) are *promoted* to ``<TOKEN>.US`` under guards, because
auto-built swarm variables routinely carry the user's raw prompt and
real prompts say "long or short on NVDA", not "NVDA.US" (#198):

* only 2–5 uppercase letters on word boundaries (never lowercase,
  never single letters — too collision-prone);
* a stopword list drops common finance/English acronyms (``ETF``,
  ``CEO``, ``GDP``, ``USD``, bare crypto symbols, …);
* text already matched by a suffixed pattern is blanked first, so
  ``BTC-USDT`` never leaks a bogus ``BTC.US``;
* promotions sort *after* explicit symbols, so explicit symbols win
  the ``DEFAULT_MAX_SYMBOLS`` cap;
* the per-symbol fetch remains the final validator — a promoted token
  that is not a real Yahoo ticker returns no data and is dropped.

A residual risk stays by design: an all-caps non-ticker word that
collides with a real listed product (e.g. ``MOAT``) grounds an
irrelevant table. That costs prompt budget, not correctness — workers
are told to cite only symbols they analyze.
* It does not refresh data mid-run. The block is a snapshot taken once
  when the background run starts; long-running swarms will see stale data after
  many minutes, but that is still strictly better than training-data
  prices from a year ago.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, timedelta
from typing import Iterable

logger = logging.getLogger(__name__)


# Window of OHLCV bars to fetch per symbol. 30 calendar days yields
# roughly 21 US trading days — enough for a "recent" view without
# bloating the worker prompt.
DEFAULT_WINDOW_DAYS = 30
DEFAULT_MAX_SYMBOLS = 8
MAX_SYMBOLS_ENV = "SWARM_GROUNDING_MAX_SYMBOLS"

# How many of the most-recent rows to render in the worker prompt.
# The full window is still used to compute the min/max line; the table
# is truncated for readability.
PROMPT_TABLE_TAIL = 5

# Symbol patterns understood by the bundled loaders. Anchored on word
# boundaries so substrings of longer text don't trigger.
_SYMBOL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b[A-Z]{1,5}\.US\b"),
    re.compile(r"\b\d{3,5}\.HK\b"),
    re.compile(r"\b\d{6}\.(?:SZ|SH|BJ)\b"),
    re.compile(r"\b[A-Z]{2,6}-USDT\b"),
)

# Bare-ticker promotion: 2–5 uppercase letters. Single letters (A, F, T …)
# collide with ordinary prose far too often to be worth grounding. The
# lookarounds reject dotted compounds on either side (FOO.USDA promotes
# neither FOO nor USDA) while still matching a sentence-ending "NVDA.".
_BARE_US_TICKER_PATTERN = re.compile(r"(?<![\w.])[A-Z]{2,5}(?!\w)(?!\.\w)")

# All-caps tokens that show up in finance prompts but must never be promoted
# to a .US symbol — either not tickers at all, or colliding with unrelated
# listed products (CEO and MSCI are both real Yahoo symbols).
_BARE_TICKER_STOPWORDS = frozenset({
    # geography / venues / index & data providers
    "US", "USA", "UK", "EU", "HK", "CN", "JP", "NYSE", "AMEX", "SSE", "SZSE",
    "HKEX", "SPX", "NDX", "DJI", "DJIA", "HSI", "CSI", "FTSE", "MSCI", "VIX",
    # instruments / structures
    "ETF", "ETN", "ADR", "IPO", "REIT", "BOND", "SWAP", "PERP",
    # macro / institutions
    "FED", "FOMC", "SEC", "IMF", "GDP", "CPI", "PPI", "PMI", "PCE", "OPEC",
    "YOY", "QOQ", "MOM", "YTD", "EOD",
    # metrics / indicators
    "PE", "PB", "PS", "EPS", "ROE", "ROA", "ROI", "EBIT", "EV", "DCF",
    "CAGR", "IRR", "NAV", "AUM", "ATH", "ATL", "RSI", "MACD", "EMA", "SMA",
    "KDJ", "BOLL", "OHLC", "ADV", "PNL",
    # currencies / crypto traded under other loaders
    "USD", "EUR", "JPY", "GBP", "CNY", "CNH", "RMB", "KRW", "INR", "AUD",
    "CAD", "CHF", "FX", "BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE",
    "USDT", "USDC", "DEFI", "NFT", "DAO",
    # trading verbs / order words
    "BUY", "SELL", "HOLD", "LONG", "SHORT", "CALL", "PUT", "STOP", "LIMIT",
    "TP", "SL", "DCA",
    # tech / prose acronyms
    "AI", "ML", "LLM", "API", "JSON", "CSV", "PDF", "URL", "HTML", "CEO",
    "CFO", "CTO", "COO", "CIO", "VP", "OK", "FAQ", "ASAP", "AM", "PM",
    "EST", "PST", "UTC", "GMT",
})


def extract_symbols_from_user_vars(user_vars: dict[str, str]) -> list[str]:
    """Return the deduplicated list of symbols mentioned anywhere in *user_vars*.

    Explicit suffixed symbols come first (in first-occurrence order),
    followed by guarded bare-ticker promotions (``NVDA`` → ``NVDA.US``),
    so explicit symbols always win the grounding cap. See the module
    docstring for the promotion guards.
    """
    explicit: dict[str, None] = {}  # ordered set
    promoted: dict[str, None] = {}
    for value in user_vars.values():
        if not isinstance(value, str):
            continue
        remainder = value
        for pattern in _SYMBOL_PATTERNS:
            for match in pattern.findall(remainder):
                explicit.setdefault(match, None)
            # Blank matched spans so the bare scan can't split a suffixed
            # symbol into bogus fragments (BTC-USDT -> BTC.US).
            remainder = pattern.sub(" ", remainder)
        for token in _BARE_US_TICKER_PATTERN.findall(remainder):
            if token not in _BARE_TICKER_STOPWORDS:
                promoted.setdefault(f"{token}.US", None)
    return list(explicit) + [s for s in promoted if s not in explicit]


def max_grounding_symbols() -> int:
    """Return the configured cap for symbols fetched into worker prompts."""
    raw = os.getenv(MAX_SYMBOLS_ENV, "").strip()
    if not raw:
        return DEFAULT_MAX_SYMBOLS
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "grounding: invalid %s=%r, using default %d",
            MAX_SYMBOLS_ENV, raw, DEFAULT_MAX_SYMBOLS,
        )
        return DEFAULT_MAX_SYMBOLS
    return max(1, value)


def fetch_grounding_data(
    symbols: Iterable[str],
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    today: date | None = None,
) -> dict[str, list[dict]]:
    """Fetch OHLCV for *symbols* and return a code -> list-of-bars mapping.

    Each bar is a plain dict with ``trade_date`` (ISO string), ``open``,
    ``high``, ``low``, ``close``, ``volume``. Symbols that fail to
    resolve are simply omitted from the result with a logged warning.

    Args:
        symbols: Iterable of suffixed symbols (``NVDA.US`` etc.).
        window_days: Calendar-day lookback. Defaults to
            :data:`DEFAULT_WINDOW_DAYS`.
        today: Override the upper bound (mainly for tests). Defaults to
            ``date.today()``.

    Returns:
        Dict keyed by the *original* symbol string with the bars list as
        value. Empty if no symbols resolve.
    """
    symbols_list = list(symbols)
    if not symbols_list:
        return {}

    end = today or date.today()
    start = end - timedelta(days=window_days)
    start_str = start.isoformat()
    end_str = end.isoformat()

    # Imported lazily so unit tests of the extraction / formatting layer
    # don't have to drag in pandas + the loader graph just to import.
    # ``resolve_loader`` expects a *market* key (``"us_equity"`` etc.), not a
    # raw code; ``_detect_market`` is the function ``runner.py`` already uses
    # to dispatch the same shapes we extract here, so reusing it keeps the
    # routing identical to the rest of the codebase.
    from backtest.loaders.registry import resolve_loader
    from backtest.runner import _detect_market

    out: dict[str, list[dict]] = {}
    for code in symbols_list:
        try:
            market = _detect_market(code)
            loader = resolve_loader(market)  # already a ready-to-use instance
            df_map = loader.fetch([code], start_str, end_str, interval="1D")
        except Exception as exc:  # pragma: no cover — depends on network
            logger.warning(
                "grounding: failed to fetch %s — %s", code, exc, exc_info=False
            )
            continue
        df = df_map.get(code)
        if df is None or df.empty:
            logger.info("grounding: no data returned for %s", code)
            continue
        rows: list[dict] = []
        for ts, row in df.iterrows():
            rows.append({
                "trade_date": getattr(ts, "isoformat", lambda: str(ts))(),
                "open": float(row.get("open", 0.0)),
                "high": float(row.get("high", 0.0)),
                "low": float(row.get("low", 0.0)),
                "close": float(row.get("close", 0.0)),
                "volume": float(row.get("volume", 0.0)),
            })
        if rows:
            out[code] = rows
    return out


def format_grounding_block(grounding: dict[str, list[dict]]) -> str:
    """Render *grounding* as a markdown block ready to splice into a prompt.

    Returns the empty string if no symbol has any data — callers can use
    that as a falsy guard so the section is omitted entirely instead of
    rendering an empty heading.
    """
    if not grounding:
        return ""

    sections: list[str] = []
    for code, rows in grounding.items():
        if not rows:
            continue
        first_date = rows[0]["trade_date"][:10]
        last_date = rows[-1]["trade_date"][:10]
        closes = [row["close"] for row in rows]
        window_low = min(closes)
        window_high = max(closes)
        last_close = closes[-1]

        lines = [
            f"### {code}  (window {first_date} → {last_date})",
            "",
            "| Date | Close | Volume |",
            "| --- | ---: | ---: |",
        ]
        for row in rows[-PROMPT_TABLE_TAIL:]:
            lines.append(
                f"| {row['trade_date'][:10]} | {row['close']:.2f} "
                f"| {int(row['volume']):,} |"
            )
        lines.append("")
        lines.append(
            f"**Latest close:** {last_close:.2f} ({last_date})  "
            f"**Window range:** {window_low:.2f} – {window_high:.2f}"
        )
        sections.append("\n".join(lines))

    if not sections:
        return ""

    header = (
        "## Ground Truth — Recent Market Data\n\n"
        "**These are the authoritative current prices for this run.** Do NOT "
        "cite prices, valuations, multiples, or returns from your training "
        "data — markets have moved. If you need a price outside this window, "
        "call `get_market_data` for the relevant range. When you state a "
        "price, cite the date from this table."
    )
    return header + "\n\n" + "\n\n".join(sections)
