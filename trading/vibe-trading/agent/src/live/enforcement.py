"""Pre-trade mandate enforcement (SPEC.md Mandate Enforcement §5–§6).

This module owns the broker-agnostic order representation
(:class:`OrderIntent`), the breach contract the consent layer consumes
(:class:`BreachEvent`, SPEC §6 verbatim), and the pure decision function
:func:`check_mandate` that the enforcement gate (``src.live.order_guard``) calls
on every live order before forwarding it to the broker.

Every check is **fail-closed**: any unparseable input, missing market data, or
ambiguous field denies the order rather than waving it through. Checks run in a
fixed order — exclude-list → instrument → asset-class → single-order notional →
total exposure → leverage → daily count → funding (defense-in-depth). The first
failing check produces the verdict; the broker-side funding ceiling remains the
backstop the agent physically cannot breach regardless of any data staleness on
our side.

The verdict is a :class:`BreachEvent` whose ``kind`` is one of
``"universe"`` / ``"instrument"`` / ``"quantitative"``:

* ``universe`` / ``instrument`` → structural violation; the gate DENIES outright
  (no widening short of editing the mandate could permit it, and the agent may
  never edit the mandate).
* ``quantitative`` → the gate emits the event and PAUSES for re-authorization.

``check_mandate`` returns ``None`` when the order is fully in-mandate (ALLOW).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd

from src.live.mandate.model import (
    AssetClass,
    InstrumentType,
    Mandate,
)

logger = logging.getLogger(__name__)


class UniverseDataUnavailable(Exception):
    """Raised when no data loader can return a usable universe figure.

    Callers treat this exactly like a ``None`` result — fail-closed DENY — but
    it lets the market-cap / liquidity helpers distinguish "loader said the
    figure is missing" from "loader chain is entirely unavailable".
    """


#: AssetClass → the loader market key (``backtest.loaders.registry`` fallback
#: chains). US equities/ETFs route to the ``us_equity`` chain (yfinance →
#: akshare); crypto routes to the ``crypto`` chain (okx → ccxt).
_ASSET_CLASS_MARKET: dict[AssetClass, str] = {
    AssetClass.US_EQUITY: "us_equity",
    AssetClass.US_ETF: "us_equity",
    AssetClass.HK_EQUITY: "hk_equity",
    AssetClass.CRYPTO: "crypto",
    # CN_EQUITY has no loader market wired here, so market-cap / liquidity floors
    # for A-shares fail closed (deny) rather than wave through — intentional. If
    # ever wired, the registry's A-share market key is "a_share" (not "cn_equity").
}

#: Breach ``kind`` values. ``universe``/``instrument`` are structural (DENY);
#: ``quantitative`` pauses for re-authorization (SPEC §6).
BREACH_KIND_UNIVERSE = "universe"
BREACH_KIND_INSTRUMENT = "instrument"
BREACH_KIND_QUANTITATIVE = "quantitative"

#: InstrumentType → the AssetClass bucket it belongs to. OPTION has no
#: universe-level asset-class bucket (the user permits asset classes, not
#: option chains), so an option is gated purely by ``allowed_instruments``.
_INSTRUMENT_ASSET_CLASS: dict[InstrumentType, AssetClass] = {
    InstrumentType.EQUITY: AssetClass.US_EQUITY,
    InstrumentType.ETF: AssetClass.US_ETF,
    InstrumentType.CRYPTO: AssetClass.CRYPTO,
}


def instrument_asset_class(instrument_type: InstrumentType) -> AssetClass | None:
    """Map an :class:`InstrumentType` to its universe :class:`AssetClass` bucket.

    Returns ``None`` for instruments with no equity-style universe bucket (e.g.
    ``OPTION``), which the quote/universe paths skip. Exposed so the gate can
    pick the right loader market chain when deriving a quantity quote.

    Args:
        instrument_type: The order's instrument type.

    Returns:
        The mapped :class:`AssetClass`, or ``None`` when the instrument has no
        bucket.
    """
    return _INSTRUMENT_ASSET_CLASS.get(instrument_type)


@dataclass(frozen=True)
class OrderIntent:
    """Broker-agnostic normalized order, units explicit.

    Attributes:
        symbol: Normalized upper-case symbol (e.g. ``AAPL``, ``BTC-USDT``).
        side: ``"buy"`` or ``"sell"``.
        notional_usd: Order notional in USD when derivable.
        quantity: Share/contract/coin quantity when notional is not given.
        instrument_type: Mapped :class:`~src.live.mandate.model.InstrumentType`.
        asset_class: Explicit universe :class:`~src.live.mandate.model.AssetClass`
            when the caller can determine the market (multi-market connectors:
            an ``EQUITY`` may be US, HK or A-share). When ``None`` the gate falls
            back to the instrument-type default (US-centric), preserving the
            single-market behavior. Carrying it explicitly is what lets the
            mandate gate distinguish e.g. an HK equity from a US equity.
    """

    symbol: str
    side: str
    notional_usd: float | None
    quantity: float | None
    instrument_type: InstrumentType
    asset_class: AssetClass | None = None


@dataclass(frozen=True)
class BreachEvent:
    """Emitted by the gate when an order would breach a limit.

    Consumed by the consent/re-authorization section. Structural violations
    (exclude-list, disallowed instrument/asset-class) carry ``kind`` ==
    ``"universe"`` / ``"instrument"`` and cause an outright DENY, since no
    widening short of editing the mandate could permit them and the agent may
    never edit the mandate. Quantitative breaches carry ``kind`` ==
    ``"quantitative"`` and pause for re-authorization.

    Attributes:
        broker: Broker key.
        limit: Which limit tripped (e.g. ``"max_order_notional_usd"``,
            ``"max_total_exposure_usd"``, ``"max_leverage"``,
            ``"max_trades_per_day"``).
        limit_value: The mandate's configured value for that limit.
        attempted_value: The post-trade value the order would have produced.
        overage: ``attempted_value - limit_value`` in the limit's native unit.
        proposed_action: The normalized :class:`OrderIntent` that triggered the
            breach.
        remote_tool: Broker remote tool name the agent invoked.
        created_at: ISO-8601 UTC timestamp.
        kind: One of ``"universe"`` / ``"instrument"`` / ``"quantitative"`` —
            the gate routes structural kinds to DENY and quantitative to
            PAUSE_FOR_REAUTH.
        detail: Human-readable explanation, mainly for structural breaches whose
            ``limit_value`` / ``attempted_value`` numbers are not meaningful.
    """

    broker: str
    limit: str
    limit_value: float
    attempted_value: float
    overage: float
    proposed_action: OrderIntent
    remote_tool: str
    created_at: str
    kind: str
    detail: str = ""


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _breach(
    *,
    broker: str,
    remote_tool: str,
    intent: OrderIntent,
    kind: str,
    limit: str,
    limit_value: float,
    attempted_value: float,
    detail: str = "",
) -> BreachEvent:
    """Construct a :class:`BreachEvent` with a computed ``overage``."""
    return BreachEvent(
        broker=broker,
        limit=limit,
        limit_value=limit_value,
        attempted_value=attempted_value,
        overage=attempted_value - limit_value,
        proposed_action=intent,
        remote_tool=remote_tool,
        created_at=_utc_now_iso(),
        kind=kind,
        detail=detail,
    )


def _resolve_order_notional(intent: OrderIntent) -> float | None:
    """Return the order's USD notional from ``intent.notional_usd``, fail-closed.

    The gate is responsible for normalizing the intent BEFORE ``check_mandate``
    runs: when an order carries ``quantity`` (with or without an explicit
    ``notional_usd``), the gate derives a quantity-implied notional from a live
    quote and stamps the LARGER of the two onto ``intent.notional_usd`` (see
    :func:`src.live.order_guard.LiveOrderGuardTool._normalize_intent_notional`).
    By the time the intent reaches here it therefore always carries a single,
    authoritative ``notional_usd``; an intent that still lacks one is
    unresolvable and denies upstream.

    Args:
        intent: The normalized order intent (notional already reconciled by the
            gate against any quantity).

    Returns:
        The order notional in USD, or ``None`` when it cannot be resolved
        (→ fail-closed DENY upstream).
    """
    notional = intent.notional_usd
    if notional is None:
        return None
    try:
        value = float(notional)
    except (TypeError, ValueError):
        return None
    if value <= 0 or value != value:  # reject non-positive and NaN
        return None
    return value


def last_price_usd(symbol: str, asset_class: AssetClass) -> float | None:
    """Last traded price (USD) for ``symbol`` via the data loaders, fail-closed.

    The fallback path the gate uses when the broker's own quote read tool is
    unavailable: pull the most recent daily close from the first available
    loader in the asset-class market chain (yfinance/akshare for US equity,
    okx/ccxt for crypto — the project's standard auto-fallback). Used to convert
    a quantity-only order into a USD notional so the notional cap stays
    enforceable (SPEC §4).

    Args:
        symbol: Normalized upper-case symbol.
        asset_class: The order's universe asset-class bucket.

    Returns:
        Last close price in USD, or ``None`` when no loader can return a usable
        price (→ fail-closed DENY upstream — never a wave-through).
    """
    try:
        loader = _resolve_loader(asset_class)
    except UniverseDataUnavailable:
        return None
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=_QUOTE_WINDOW_DAYS)
    try:
        frames = loader.fetch(
            [symbol],
            start.isoformat(),
            end.isoformat(),
            interval="1D",
        )
    except Exception as exc:  # loader / network failure → fail-closed
        logger.warning("quote fetch failed for %s via %s: %s", symbol, loader.name, exc)
        return None
    frame = frames.get(symbol) if isinstance(frames, dict) else None
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    if "close" not in frame.columns:
        return None
    closes = frame["close"].astype(float).dropna()
    if closes.empty:
        return None
    price = float(closes.iloc[-1])
    return price if price == price and price > 0 else None


def _positions_market_value(positions: object) -> float | None:
    """Sum the USD market value of all open positions, fail-closed.

    Accepts the broker read tool's positions payload in the two shapes the read
    path may return: a list of position dicts, or a dict envelope with a
    ``positions`` / ``data`` list. Each position must expose a numeric market
    value under one of the common keys.

    Args:
        positions: Positions payload from the broker's read MCP tool.

    Returns:
        Total market value in USD, or ``None`` when any position cannot be
        parsed (→ fail-closed DENY upstream).
    """
    rows = _coerce_position_rows(positions)
    if rows is None:
        return None
    total = 0.0
    for row in rows:
        value = _position_market_value(row)
        if value is None:
            return None
        total += value
    return total


def _coerce_position_rows(positions: object) -> list[dict] | None:
    """Normalize a positions payload to a list of position dicts."""
    if isinstance(positions, list):
        rows = positions
    elif isinstance(positions, dict):
        # TODO(L6): pin the exact Robinhood positions envelope key once the real
        # read-tool schema is observed (get_positions). Until then accept the
        # common envelope shapes and fail-closed on anything else.
        rows = positions.get("positions")
        if rows is None:
            rows = positions.get("data")
        if rows is None:
            # A bare mapping of symbol -> position dict is also accepted.
            rows = list(positions.values()) if positions else []
    else:
        return None
    if not isinstance(rows, list):
        return None
    if not all(isinstance(row, dict) for row in rows):
        return None
    return rows


def _position_market_value(row: dict) -> float | None:
    """Extract one position's USD market value, fail-closed.

    Prefers an explicit ``market_value`` field; otherwise derives it from
    ``quantity`` × (``price`` | ``last_price`` | ``mark_price``). Returns
    ``None`` if neither is parseable.
    """
    for key in ("market_value", "marketValue", "value_usd", "value"):
        if key in row:
            parsed = _as_float(row[key])
            return parsed  # may be None → fail-closed upstream
    qty = None
    for key in ("quantity", "qty", "shares"):
        if key in row:
            qty = _as_float(row[key])
            break
    price = None
    for key in ("price", "last_price", "mark_price", "market_price"):
        if key in row:
            price = _as_float(row[key])
            break
    if qty is None or price is None:
        return None
    return abs(qty) * price


def _account_balance_market_value(balance: object) -> float | None:
    """Return account funding/equity in USD from the balance payload.

    This is read defensively for completeness; mandate leverage math uses the
    mandate's ``account_funding_usd`` as the denominator per SPEC §5, so this
    helper is only used to sanity-parse the read payload. Returns ``None`` when
    unparseable.
    """
    if isinstance(balance, dict):
        for key in ("equity", "buying_power", "cash", "account_value", "total"):
            if key in balance:
                return _as_float(balance[key])
    return _as_float(balance)


def _as_float(value: object) -> float | None:
    """Coerce ``value`` to a finite positive-or-zero float, else ``None``."""
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def check_mandate(
    mandate: Mandate,
    intent: OrderIntent,
    positions: object,
    balance: object,
    *,
    broker: str,
    remote_tool: str,
    daily_count: int,
) -> BreachEvent | None:
    """Evaluate one order intent against the mandate (fail-closed).

    Checks run in a fixed order and the first failure produces the verdict:
    exclude-list, instrument allowance, asset-class allowance (universe market-
    cap/liquidity), single-order notional, post-trade total exposure, post-trade
    gross leverage, daily order count, and funding (defense-in-depth). Any
    unparseable input (bad intent, unreadable positions, missing market data)
    denies rather than allows.

    Args:
        mandate: The active, schema-valid, unexpired mandate (validated by the
            gate before this is called).
        intent: The normalized order intent extracted from the tool call.
        positions: Current positions from the broker's read MCP tool.
        balance: Current balance from the broker's read MCP tool.
        broker: Broker key (stamped onto any :class:`BreachEvent`).
        remote_tool: Broker remote tool name the agent invoked.
        daily_count: Orders already placed today (from the persisted counter,
            after UTC rollover).

    Returns:
        ``None`` when the order is fully in-mandate (ALLOW), otherwise a
        :class:`BreachEvent` describing the first violated rule.
    """
    caps = mandate.hard_caps
    universe = mandate.universe

    symbol = (intent.symbol or "").strip().upper()
    if not symbol or intent.side not in ("buy", "sell"):
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_INSTRUMENT, limit="order_intent",
            limit_value=0.0, attempted_value=0.0,
            detail="order intent missing symbol or side",
        )

    # 1. Exclude-list — takes precedence over every other universe rule.
    if symbol in {s.strip().upper() for s in universe.exclude_symbols}:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_UNIVERSE, limit="exclude_symbols",
            limit_value=0.0, attempted_value=0.0,
            detail=f"{symbol} is on the mandate exclude list",
        )

    # 2. Instrument-type allowance (empty == deny all, fail-closed).
    if intent.instrument_type not in caps.allowed_instruments:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_INSTRUMENT, limit="allowed_instruments",
            limit_value=0.0, attempted_value=0.0,
            detail=f"{intent.instrument_type.value} not in allowed_instruments",
        )

    # 3. Asset-class allowance (universe bucket). OPTION has no bucket and is
    #    governed by allowed_instruments alone. An explicit intent.asset_class
    #    (multi-market connectors: US/HK/CN equities) wins over the instrument
    #    default so the gate buckets HK/A-share correctly.
    asset_class = intent.asset_class or _INSTRUMENT_ASSET_CLASS.get(intent.instrument_type)
    if asset_class is not None and asset_class not in universe.asset_classes:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_UNIVERSE, limit="asset_classes",
            limit_value=0.0, attempted_value=0.0,
            detail=f"{asset_class.value} not in permitted asset_classes",
        )

    # 4. Single-order notional.
    notional = _resolve_order_notional(intent)
    if notional is None:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_INSTRUMENT, limit="order_intent",
            limit_value=0.0, attempted_value=0.0,
            detail="order notional could not be resolved",
        )
    if notional > caps.max_order_notional_usd:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="max_order_notional_usd",
            limit_value=caps.max_order_notional_usd, attempted_value=notional,
        )

    # 5–6. Exposure + leverage need observable positions; fail-closed on any
    #      unparseable position. A sell reduces gross exposure (signed by side).
    current_exposure = _positions_market_value(positions)
    if current_exposure is None:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="max_total_exposure_usd",
            limit_value=caps.max_total_exposure_usd, attempted_value=0.0,
            detail="current positions could not be read (fail-closed)",
        )
    signed = notional if intent.side == "buy" else -notional
    post_exposure = current_exposure + signed
    if post_exposure > caps.max_total_exposure_usd:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="max_total_exposure_usd",
            limit_value=caps.max_total_exposure_usd, attempted_value=post_exposure,
        )

    # 6. Gross leverage = post-trade gross exposure / account_funding_usd.
    if caps.account_funding_usd <= 0:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="max_leverage",
            limit_value=caps.max_leverage, attempted_value=float("inf"),
            detail="account_funding_usd is non-positive (fail-closed)",
        )
    post_leverage = abs(post_exposure) / caps.account_funding_usd
    if post_leverage > caps.max_leverage:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="max_leverage",
            limit_value=caps.max_leverage, attempted_value=post_leverage,
        )

    # 7. Daily order count (count over UTC calendar days).
    attempted_count = daily_count + 1
    if attempted_count > caps.max_trades_per_day:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="max_trades_per_day",
            limit_value=float(caps.max_trades_per_day),
            attempted_value=float(attempted_count),
        )

    # 8. Funding (defense-in-depth; broker is the real ceiling). Only a buy can
    #    push us past funding — never block a sell on this.
    if intent.side == "buy" and post_exposure > caps.account_funding_usd:
        return _breach(
            broker=broker, remote_tool=remote_tool, intent=intent,
            kind=BREACH_KIND_QUANTITATIVE, limit="account_funding_usd",
            limit_value=caps.account_funding_usd, attempted_value=post_exposure,
            detail="post-trade exposure exceeds mirrored funding ceiling",
        )

    # 9. Expensive universe rules (market-cap / liquidity floors). Fail-closed
    #    on missing data per SPEC §5. Skipped for instruments with no equity
    #    universe bucket (e.g. options) where these floors do not apply.
    if asset_class is not None:
        universe_breach = _check_universe_floors(
            universe, intent, symbol, asset_class,
            broker=broker, remote_tool=remote_tool,
        )
        if universe_breach is not None:
            return universe_breach

    return None


def _check_universe_floors(
    universe,
    intent: OrderIntent,
    symbol: str,
    asset_class: AssetClass,
    *,
    broker: str,
    remote_tool: str,
) -> BreachEvent | None:
    """Enforce market-cap / liquidity floors via the data loaders (fail-closed).

    Both floors are optional (``None`` == no floor). When a floor is set, the
    figure is fetched from Vibe-Trading's existing loaders (with auto-fallback);
    if no loader can return a usable figure, the order is DENIED rather than
    waved through (SPEC §5 fail-closed contract).

    Returns:
        A universe-kind :class:`BreachEvent`, or ``None`` when both floors pass
        (or neither is set).
    """
    if universe.min_market_cap_usd is not None:
        try:
            cap = market_cap_usd(symbol, asset_class)
        except UniverseDataUnavailable:
            cap = None
        if cap is None or cap < universe.min_market_cap_usd:
            return _breach(
                broker=broker, remote_tool=remote_tool, intent=intent,
                kind=BREACH_KIND_UNIVERSE, limit="min_market_cap_usd",
                limit_value=universe.min_market_cap_usd,
                attempted_value=cap if cap is not None else 0.0,
                detail=(
                    f"market cap for {symbol} unavailable (fail-closed)"
                    if cap is None
                    else f"{symbol} market cap below floor"
                ),
            )

    if universe.min_avg_daily_volume_usd is not None:
        try:
            adv = avg_daily_dollar_volume(symbol, asset_class)
        except UniverseDataUnavailable:
            adv = None
        if adv is None or adv < universe.min_avg_daily_volume_usd:
            return _breach(
                broker=broker, remote_tool=remote_tool, intent=intent,
                kind=BREACH_KIND_UNIVERSE, limit="min_avg_daily_volume_usd",
                limit_value=universe.min_avg_daily_volume_usd,
                attempted_value=adv if adv is not None else 0.0,
                detail=(
                    f"liquidity for {symbol} unavailable (fail-closed)"
                    if adv is None
                    else f"{symbol} avg daily $ volume below floor"
                ),
            )

    return None


# ---------------------------------------------------------------------------
# Universe market-cap / liquidity via the existing data loaders (auto-fallback).
# ---------------------------------------------------------------------------

#: Trailing window (calendar days) over which average daily dollar volume is
#: computed from OHLCV. ~30 trading days of context with weekend slack.
_ADV_WINDOW_DAYS = 45

#: Trailing window (calendar days) the quote fallback fetches to recover the most
#: recent daily close. A short window with weekend/holiday slack so a Monday
#: order still resolves Friday's close.
_QUOTE_WINDOW_DAYS = 10


def _resolve_loader(asset_class: AssetClass):
    """Return the first available data loader for ``asset_class``.

    Raises:
        UniverseDataUnavailable: When no loader in the market's fallback chain
            is available (e.g. no network / no credentials).
    """
    from backtest.loaders.base import NoAvailableSourceError
    from backtest.loaders.registry import resolve_loader

    market = _ASSET_CLASS_MARKET.get(asset_class)
    if market is None:
        raise UniverseDataUnavailable(f"no loader market for {asset_class.value}")
    try:
        return resolve_loader(market)
    except NoAvailableSourceError as exc:
        raise UniverseDataUnavailable(str(exc)) from exc


def avg_daily_dollar_volume(symbol: str, asset_class: AssetClass) -> float | None:
    """Trailing average daily dollar volume (USD) for ``symbol``, fail-closed.

    Computed as ``mean(close * volume)`` over the trailing
    :data:`_ADV_WINDOW_DAYS` of daily OHLCV from the first available loader.
    This is exact and derivable from data the loaders already return.

    Args:
        symbol: Normalized upper-case symbol.
        asset_class: The order's universe asset-class bucket.

    Returns:
        Average daily dollar volume in USD, or ``None`` when no loader can
        return usable OHLCV for the symbol (→ fail-closed DENY upstream).
    """
    loader = _resolve_loader(asset_class)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=_ADV_WINDOW_DAYS)
    try:
        frames = loader.fetch(
            [symbol],
            start.isoformat(),
            end.isoformat(),
            interval="1D",
        )
    except Exception as exc:  # loader / network failure → fail-closed
        logger.warning("ADV fetch failed for %s via %s: %s", symbol, loader.name, exc)
        return None
    frame = frames.get(symbol) if isinstance(frames, dict) else None
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    if "close" not in frame.columns or "volume" not in frame.columns:
        return None
    dollar = (frame["close"].astype(float) * frame["volume"].astype(float)).dropna()
    if dollar.empty:
        return None
    value = float(dollar.mean())
    return value if value == value and value >= 0 else None


def market_cap_usd(symbol: str, asset_class: AssetClass) -> float | None:
    """Market capitalization (USD) for ``symbol``, fail-closed.

    The existing OHLCV loaders do not expose a unified market-cap field, so this
    is best-effort: for US equities/ETFs it reads ``yfinance``'s ``.info``
    when available; it returns ``None`` (→ fail-closed DENY) whenever the figure
    cannot be obtained. This keeps the contract honest — an unenforceable floor
    denies rather than waves the order through.

    TODO(L6): once the real Robinhood read-tool catalog is observed, prefer a
    broker-reported fundamentals/quote figure (and a dedicated fundamentals
    loader for non-US assets) over the yfinance ``.info`` best-effort below.

    Args:
        symbol: Normalized upper-case symbol.
        asset_class: The order's universe asset-class bucket.

    Returns:
        Market cap in USD, or ``None`` when unavailable.
    """
    if asset_class not in (AssetClass.US_EQUITY, AssetClass.US_ETF):
        # No unified market-cap source for crypto/other here — fail-closed.
        return None
    try:
        import yfinance  # type: ignore
    except Exception:
        return None
    try:
        info = yfinance.Ticker(symbol).info
    except Exception as exc:
        logger.warning("market-cap lookup failed for %s: %s", symbol, exc)
        return None
    if not isinstance(info, dict):
        return None
    cap = info.get("marketCap")
    parsed = _as_float(cap)
    return parsed if parsed and parsed > 0 else None
