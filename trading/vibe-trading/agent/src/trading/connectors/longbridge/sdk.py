"""Read-only Longbridge (LongPort OpenAPI) connector via the official SDK.

Wraps ``TradeContext`` / ``QuoteContext`` for the five read operations the
trading layer exposes (account / positions / orders / quote / history). No
order-placement method is exposed here.

Auth is static-key (App Key + App Secret + Access Token). The SDK was renamed
from ``longport`` to ``longbridge``; this module imports whichever is installed.

Paper-vs-live identity guard: **none is possible from the API** — Longbridge
exposes no response field, account prefix, or host that distinguishes paper from
live (they differ only by the loaded Access Token). The configured ``profile``
label is therefore trust-based and recorded in every payload as
``paper_guard="config_declared"`` so callers never mistake it for a verified
environment.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from src.config.paths import get_runtime_root

CONFIG_FILENAME = "longbridge.json"

PROFILE_ENVIRONMENTS = {
    "paper": "paper",
    "live-readonly": "live",
    "live": "live",
}

#: Region → HTTP host (used only for display/diagnostics; the SDK selects the
#: host from the same region setting). Paper and live share these hosts.
REGION_HOSTS = {
    "global": "openapi.longbridge.com",
    "cn": "openapi.longbridge.cn",
}


class LongbridgeDependencyError(RuntimeError):
    """Raised when neither ``longbridge`` nor ``longport`` SDK is installed."""


class LongbridgeConfigError(RuntimeError):
    """Raised when the connector configuration is missing or invalid."""


@dataclass(frozen=True)
class LongbridgeConfig:
    """Longbridge connector connection settings.

    Args:
        app_key: LongPort App Key.
        app_secret: LongPort App Secret.
        access_token: LongPort Access Token (selects paper vs live account).
        profile: ``paper``, ``live-readonly`` or ``live`` (operator-declared).
        region: ``global`` or ``cn`` (host region; not a paper/live signal).
        timeout: Network timeout in seconds.
        readonly: Always true for this layer; order methods are not exposed.
    """

    app_key: str = ""
    app_secret: str = ""
    access_token: str = ""
    profile: str = "paper"
    region: str = "global"
    timeout: float = 15.0
    readonly: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "LongbridgeConfig":
        """Build a config from a JSON-like mapping, normalizing the profile."""
        payload = dict(data or {})
        profile = str(payload.get("profile") or "paper").strip().lower()
        if profile not in PROFILE_ENVIRONMENTS:
            raise LongbridgeConfigError("profile must be 'paper', 'live-readonly' or 'live'")
        region = str(payload.get("region") or "global").strip().lower()
        if region not in REGION_HOSTS:
            raise LongbridgeConfigError("region must be 'global' or 'cn'")
        return cls(
            app_key=str(payload.get("app_key") or "").strip(),
            app_secret=str(payload.get("app_secret") or "").strip(),
            access_token=str(payload.get("access_token") or "").strip(),
            profile=profile,
            region=region,
            timeout=float(payload.get("timeout") or 15.0),
            readonly=bool(payload.get("readonly", True)),
        )

    def with_overrides(
        self,
        *,
        app_key: str | None = None,
        app_secret: str | None = None,
        access_token: str | None = None,
        profile: str | None = None,
        region: str | None = None,
    ) -> "LongbridgeConfig":
        """Return a copy with CLI/tool overrides applied."""
        payload = asdict(self)
        if app_key is not None:
            payload["app_key"] = app_key
        if app_secret is not None:
            payload["app_secret"] = app_secret
        if access_token is not None:
            payload["access_token"] = access_token
        if profile is not None:
            payload["profile"] = profile
        if region is not None:
            payload["region"] = region
        return LongbridgeConfig.from_mapping(payload)

    @property
    def environment(self) -> str:
        """Return ``paper`` or ``live`` for this profile."""
        return PROFILE_ENVIRONMENTS.get(self.profile, "paper")


_OVERRIDE_KEYS = ("app_key", "app_secret", "access_token", "profile", "region")


def build_config(profile_config: Mapping[str, Any] | None = None, overrides: Mapping[str, Any] | None = None) -> "LongbridgeConfig":
    """Resolve the effective config: saved file ← profile defaults ← CLI overrides.

    Credentials (``app_key`` / ``app_secret`` / ``access_token``) come from the
    saved ``~/.vibe-trading/longbridge.json``; the selected connector profile
    supplies the ``profile`` / ``region`` intent; CLI/tool overrides win last.

    Args:
        profile_config: The connector profile's ``config`` dict.
        overrides: Per-call overrides (only known config keys are applied).

    Returns:
        A normalized :class:`LongbridgeConfig`.
    """
    base = asdict(load_config())
    for key, value in dict(profile_config or {}).items():
        if value is not None:
            base[key] = value
    cfg = LongbridgeConfig.from_mapping(base)
    clean = {k: v for k, v in dict(overrides or {}).items() if k in _OVERRIDE_KEYS and v not in (None, "")}
    return cfg.with_overrides(**clean) if clean else cfg


def config_path() -> Path:
    """Return the user-level Longbridge config path."""
    return get_runtime_root() / CONFIG_FILENAME


def load_config() -> LongbridgeConfig:
    """Load Longbridge settings from ``~/.vibe-trading/longbridge.json``."""
    path = config_path()
    if not path.exists():
        return LongbridgeConfig()
    try:
        return LongbridgeConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise LongbridgeConfigError(f"invalid Longbridge config at {path}: {exc}") from exc


def save_config(config: LongbridgeConfig) -> Path:
    """Persist Longbridge settings with owner-only permissions."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def longbridge_available() -> bool:
    """Return whether the optional Longbridge SDK can be imported."""
    try:
        _require_openapi()
        return True
    except LongbridgeDependencyError:
        return False


def check_status(config: LongbridgeConfig | None = None) -> dict[str, Any]:
    """Check SDK readiness and config completeness without mutating broker state."""
    cfg = config or load_config()
    report: dict[str, Any] = {
        "status": "ok",
        "config": _public_config(cfg),
        "sdk": {"package": "longbridge", "installed": longbridge_available()},
        "paper_guard": "config_declared",
    }

    missing = _missing_fields(cfg)
    if missing:
        report["status"] = "error"
        report["error"] = f"Longbridge connector not configured: missing {', '.join(missing)}."
        return report

    if not report["sdk"]["installed"]:
        report["status"] = "error"
        report["error"] = "Optional dependency missing: install with `pip install longbridge`."
        return report

    try:
        snapshot = get_account_snapshot(cfg)
    except Exception as exc:  # noqa: BLE001 - health endpoint reports cleanly
        report["status"] = "error"
        report["error"] = str(exc)
        return report

    report["account"] = {
        "profile": cfg.profile,
        "region": cfg.region,
        "balances_currency": [row.get("currency") for row in snapshot.get("balances", [])],
    }
    return report


def get_account_snapshot(config: LongbridgeConfig | None = None) -> dict[str, Any]:
    """Fetch account balances for the configured account."""
    cfg = config or load_config()
    trade = _trade_context(cfg)
    balances = _call(trade, "account_balance")
    rows = [_balance_to_dict(item) for item in _as_iter(balances)]
    return {
        "status": "ok",
        "profile": cfg.profile,
        "paper_guard": "config_declared",
        "balances": rows,
    }


def get_positions(config: LongbridgeConfig | None = None) -> dict[str, Any]:
    """Fetch current stock positions for the configured account."""
    cfg = config or load_config()
    trade = _trade_context(cfg)
    response = _call(trade, "stock_positions")
    rows = [_position_to_dict(item) for item in _iter_positions(response)]
    return {"status": "ok", "profile": cfg.profile, "paper_guard": "config_declared", "positions": rows}


#: Longbridge OrderStatus values that mean the order is no longer live (bare
#: member names). Used to filter ``today_orders`` (which returns ALL of today's
#: orders) down to the genuinely-open ones, so ``open_orders`` matches the other
#: connectors' meaning. Matching is normalized so it works whether the SDK
#: stringifies a status as ``Filled``, ``FilledStatus`` or ``OrderStatus.Filled``.
#: ``PartialFilled`` is deliberately NOT terminal (still open).
_TERMINAL_ORDER_STATUSES = frozenset(
    {"filled", "canceled", "cancelled", "rejected", "expired", "partialwithdrawal"}
)


def _normalize_status(value: Any) -> str:
    """Normalize a status to a bare lower-case member name for comparison."""
    text = str(value or "").strip().lower()
    text = text.rsplit(".", 1)[-1]          # drop an ``orderstatus.`` prefix
    if text.endswith("status"):
        text = text[: -len("status")]        # drop a ``...Status`` suffix
    return text


def _is_open_order(row: dict[str, Any]) -> bool:
    """Return whether a mapped order row is still live (not in a terminal state)."""
    return _normalize_status(row.get("status")) not in _TERMINAL_ORDER_STATUSES


def get_open_orders(config: LongbridgeConfig | None = None, *, include_executions: bool = False) -> dict[str, Any]:
    """Fetch today's still-open orders and, optionally, today's executions.

    Longbridge's ``today_orders`` returns ALL of today's orders (including
    filled/cancelled). We filter to non-terminal statuses so ``open_orders``
    means the same thing here as in the other connectors.
    """
    cfg = config or load_config()
    trade = _trade_context(cfg)
    orders = _call(trade, "today_orders")
    mapped = [_order_to_dict(item) for item in _as_iter(orders)]
    result: dict[str, Any] = {
        "status": "ok",
        "profile": cfg.profile,
        "paper_guard": "config_declared",
        "open_orders": [row for row in mapped if _is_open_order(row)],
    }
    if include_executions:
        execs = _safe_call(trade, "today_executions")
        result["executions"] = [_execution_to_dict(item) for item in _as_iter(execs)]
    return result


def get_quote(symbol: str, *, config: LongbridgeConfig | None = None, **_: Any) -> dict[str, Any]:
    """Fetch a quote snapshot for ``symbol`` (top-of-book bid/ask via depth)."""
    cfg = config or load_config()
    quote_ctx = _quote_context(cfg)
    clean = symbol.strip().upper()
    quotes = _call(quote_ctx, "quote", [clean])
    rows = [_quote_to_dict(item) for item in _as_iter(quotes)]
    payload = rows[0] if rows else {}
    depth = _safe_call(quote_ctx, "depth", clean)
    bid, ask = _top_of_book(depth)
    if bid is not None:
        payload["bid"] = bid
    if ask is not None:
        payload["ask"] = ask
    return {"status": "ok", "symbol": clean, "quote": payload}


def get_historical_bars(
    symbol: str,
    *,
    config: LongbridgeConfig | None = None,
    period: str = "1d",
    limit: int = 90,
    **_: Any,
) -> dict[str, Any]:
    """Fetch historical OHLCV candlesticks for ``symbol`` (``period`` canonical)."""
    cfg = config or load_config()
    quote_ctx = _quote_context(cfg)
    clean = symbol.strip().upper()
    period_enum, adjust_enum = _candlestick_enums(period)
    bars = _call(quote_ctx, "candlesticks", clean, period_enum, int(limit), adjust_enum)
    return {
        "status": "ok",
        "symbol": clean,
        "period": period,
        "bars": [_bar_to_dict(item) for item in _as_iter(bars)],
    }


# ---------------------------------------------------------------------------
# Order placement — PAPER ONLY (no runtime paper/live discriminator exists)
# ---------------------------------------------------------------------------

#: Message used by both order entry points when the config is not a paper
#: profile. Longbridge exposes no API field that distinguishes paper from live,
#: so we structurally refuse anything that is not the declared paper profile —
#: this connector can never place a live order by design.
_PAPER_ONLY_ERROR = (
    "Longbridge order placement is paper-only (no runtime paper/live "
    "discriminator); live orders are not supported."
)

_SIDE_MAP = {"buy": "Buy", "sell": "Sell"}
_ORDER_TYPE_MAP = {"market": "MO", "limit": "LO"}
_TIF_MAP = {"day": "Day"}


def place_order(
    config: LongbridgeConfig,
    *,
    symbol: str,
    side: str,
    quantity: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    limit_price: float | None = None,
    time_in_force: str = "day",
) -> dict[str, Any]:
    """Place a PAPER-ONLY stock order via the Longbridge ``TradeContext``.

    Longbridge exposes no runtime paper/live discriminator (paper vs live is
    only the loaded Access Token), so this connector is structurally capped at
    paper: the very first check refuses any config whose ``environment`` is not
    ``paper``. There is therefore no live order path here, by design.

    The order is submitted against whatever account the loaded paper Access
    Token points at. The connector only executes; authorization (mandate gate,
    kill switch) is the caller's responsibility.

    Args:
        config: Resolved :class:`LongbridgeConfig`. Must be a paper profile.
        symbol: Longbridge symbol, e.g. ``700.HK`` or ``AAPL.US`` (passed
            through uppercased).
        side: ``buy`` or ``sell`` (case-insensitive).
        quantity: Order size in shares. Longbridge requires an explicit share
            quantity; provide this (not ``notional``).
        notional: Unsupported — Longbridge has no notional order path, so a
            notional-only request fails closed with a clear error.
        order_type: ``market`` or ``limit`` (a ``limit`` order requires
            ``limit_price``).
        limit_price: Limit price; required for and only used by limit orders.
        time_in_force: Only ``day`` is supported.

    Returns:
        ``{"status": "ok", "order_id": str, "symbol", "side", "profile", ...}``
        on success, otherwise ``{"status": "error", "error": str}``. Never
        raises: every failure mode is reported in the envelope.
    """
    # ---- HARD GUARD: structurally paper-only (must run before anything) ----
    if config.environment != "paper":
        return {"status": "error", "error": _PAPER_ONLY_ERROR}

    # ---- input validation (fail closed before touching the SDK) ----
    side_key = str(side or "").strip().lower()
    side_attr = _SIDE_MAP.get(side_key)
    if side_attr is None:
        return {"status": "error", "error": "side must be 'buy' or 'sell'"}

    if (quantity is None) == (notional is None):
        return {"status": "error", "error": "provide exactly one of quantity or notional"}
    if notional is not None:
        return {"status": "error", "error": "Longbridge requires quantity (shares), not notional"}

    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        return {"status": "error", "error": "quantity must be a number"}
    if qty <= 0:
        return {"status": "error", "error": "quantity must be positive"}

    type_key = str(order_type or "").strip().lower()
    type_attr = _ORDER_TYPE_MAP.get(type_key)
    if type_attr is None:
        return {"status": "error", "error": "order_type must be 'market' or 'limit'"}

    px: float | None = None
    if type_key == "limit":
        if limit_price is None:
            return {"status": "error", "error": "limit order requires limit_price"}
        try:
            px = float(limit_price)
        except (TypeError, ValueError):
            return {"status": "error", "error": "limit_price must be a number"}
        if px <= 0:
            return {"status": "error", "error": "limit_price must be positive"}

    tif_key = str(time_in_force or "").strip().lower()
    tif_attr = _TIF_MAP.get(tif_key)
    if tif_attr is None:
        return {"status": "error", "error": "time_in_force must be 'day'"}

    clean_symbol = str(symbol or "").strip().upper()
    if not clean_symbol:
        return {"status": "error", "error": "symbol is required"}

    # ---- resolve SDK enums + build + submit ----
    try:
        from decimal import Decimal

        openapi = _require_openapi()
        order_type_enum = getattr(getattr(openapi, "OrderType"), type_attr)
        order_side_enum = getattr(getattr(openapi, "OrderSide"), side_attr)
        tif_enum = getattr(getattr(openapi, "TimeInForceType"), tif_attr)

        kwargs: dict[str, Any] = {
            "symbol": clean_symbol,
            "order_type": order_type_enum,
            "side": order_side_enum,
            "submitted_quantity": Decimal(str(qty)),
            "time_in_force": tif_enum,
        }
        if type_key == "limit":
            kwargs["submitted_price"] = Decimal(str(px))

        trade = _trade_context(config)
        response = _call(trade, "submit_order", **kwargs)
        order_id = _obj_get(response, "order_id", None)
    except Exception as exc:  # noqa: BLE001 - fail closed, never raise to caller
        return {"status": "error", "error": str(exc)}

    if order_id is None:
        return {"status": "error", "error": "Longbridge did not return an order id"}

    return {
        "status": "ok",
        "order_id": str(order_id),
        "symbol": clean_symbol,
        "side": side_key,
        "profile": config.profile,
        "paper_guard": "config_declared",
        "order_type": type_key,
        "quantity": qty,
        "limit_price": px,
        "time_in_force": tif_key,
    }


def cancel_order(config: LongbridgeConfig, order_id: Any, *, symbol: str | None = None) -> dict[str, Any]:
    """Cancel a PAPER-ONLY order via the Longbridge ``TradeContext``.

    Like :func:`place_order`, the very first check refuses any config whose
    ``environment`` is not ``paper`` — this connector never cancels a live
    order. Longbridge cancels by order id; ``symbol`` is echoed back only for
    caller convenience. Never raises: every failure is returned in the envelope.

    Args:
        config: Resolved :class:`LongbridgeConfig`. Must be a paper profile.
        order_id: The order id returned by :func:`place_order`.
        symbol: Optional symbol, echoed back; Longbridge cancels by id and does
            not require it.

    Returns:
        ``{"status": "ok", "order_id": str, "profile", ...}`` on success,
        otherwise ``{"status": "error", "error": str}``.
    """
    # ---- HARD GUARD: structurally paper-only (must run before anything) ----
    if config.environment != "paper":
        return {"status": "error", "error": _PAPER_ONLY_ERROR}

    if order_id is None or str(order_id).strip() == "":
        return {"status": "error", "error": "order_id is required"}

    clean_id = str(order_id).strip()
    try:
        trade = _trade_context(config)
        _call(trade, "cancel_order", clean_id)
    except Exception as exc:  # noqa: BLE001 - fail closed, never raise to caller
        return {"status": "error", "error": str(exc)}

    result: dict[str, Any] = {
        "status": "ok",
        "order_id": clean_id,
        "profile": config.profile,
        "paper_guard": "config_declared",
    }
    if symbol is not None:
        result["symbol"] = str(symbol).strip().upper()
    return result


# ---------------------------------------------------------------------------
# SDK plumbing — import either the renamed ``longbridge`` or legacy ``longport``
# ---------------------------------------------------------------------------


def _require_openapi() -> ModuleType:
    """Return the ``openapi`` submodule from whichever SDK package is installed."""
    for package in ("longbridge", "longport"):
        try:
            module = __import__(f"{package}.openapi", fromlist=["openapi"])
            return module
        except ModuleNotFoundError:
            continue
    raise LongbridgeDependencyError(
        "Longbridge SDK is not installed; run `pip install longbridge`."
    )


def _build_config(cfg: LongbridgeConfig):
    openapi = _require_openapi()
    config_cls = getattr(openapi, "Config")
    # SDK exposes both a keyword constructor and a ``from_apikey`` factory across
    # versions; try the direct constructor, fall back to the factory.
    try:
        return config_cls(
            app_key=cfg.app_key,
            app_secret=cfg.app_secret,
            access_token=cfg.access_token,
        )
    except TypeError:
        return config_cls.from_apikey(cfg.app_key, cfg.app_secret, cfg.access_token)


def _trade_context(cfg: LongbridgeConfig):
    openapi = _require_openapi()
    return getattr(openapi, "TradeContext")(_build_config(cfg))


def _quote_context(cfg: LongbridgeConfig):
    openapi = _require_openapi()
    return getattr(openapi, "QuoteContext")(_build_config(cfg))


def _candlestick_enums(period: str):
    """Map a period string to the SDK ``Period`` and ``AdjustType`` enums."""
    openapi = _require_openapi()
    period_cls = getattr(openapi, "Period")
    adjust_cls = getattr(openapi, "AdjustType")
    period_map = {
        "1m": "Min_1",
        "5m": "Min_5",
        "15m": "Min_15",
        "30m": "Min_30",
        "1h": "Min_60",
        "4h": "Min_60",
        "1d": "Day",
        "1w": "Week",
        "1M": "Month",
    }
    attr = period_map.get(period.strip(), "Day")
    period_enum = getattr(period_cls, attr, getattr(period_cls, "Day"))
    adjust_enum = getattr(adjust_cls, "NoAdjust", getattr(adjust_cls, "ForwardAdjust", None))
    return period_enum, adjust_enum


def _missing_fields(cfg: LongbridgeConfig) -> list[str]:
    missing = []
    if not cfg.app_key:
        missing.append("app_key")
    if not cfg.app_secret:
        missing.append("app_secret")
    if not cfg.access_token:
        missing.append("access_token")
    return missing


def _public_config(cfg: LongbridgeConfig) -> dict[str, Any]:
    """Config snapshot with secrets redacted."""
    data = asdict(cfg)
    for secret in ("app_secret", "access_token"):
        if data.get(secret):
            data[secret] = "***redacted***"
    if data.get("app_key"):
        data["app_key"] = data["app_key"][:4] + "***"
    data["host"] = REGION_HOSTS.get(cfg.region)
    return data


# ---------------------------------------------------------------------------
# Defensive field extraction
# ---------------------------------------------------------------------------


def _as_iter(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _obj_get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _first(obj: Any, names: tuple[str, ...], default: Any = None) -> Any:
    for name in names:
        value = _obj_get(obj, name, None)
        if value is not None:
            return value
    return default


def _iter_positions(response: Any) -> list[Any]:
    """Flatten ``stock_positions`` channels into a flat position list."""
    channels = _obj_get(response, "channels")
    if channels is None:
        return _as_iter(response)
    rows: list[Any] = []
    for channel in _as_iter(channels):
        rows.extend(_as_iter(_obj_get(channel, "positions")))
    return rows


def _top_of_book(depth: Any) -> tuple[Any, Any]:
    """Extract best bid/ask price from a depth response."""
    if depth is None:
        return None, None
    asks = _as_iter(_obj_get(depth, "asks") or _obj_get(depth, "ask"))
    bids = _as_iter(_obj_get(depth, "bids") or _obj_get(depth, "bid"))
    bid = _first(bids[0], ("price",)) if bids else None
    ask = _first(asks[0], ("price",)) if asks else None
    return bid, ask


def _balance_to_dict(item: Any) -> dict[str, Any]:
    return {
        "currency": _first(item, ("currency",)),
        "total_cash": _first(item, ("total_cash",)),
        "net_assets": _first(item, ("net_assets",)),
        "buy_power": _first(item, ("buy_power",)),
        "init_margin": _first(item, ("init_margin",)),
        "maintenance_margin": _first(item, ("maintenance_margin",)),
    }


def _position_to_dict(item: Any) -> dict[str, Any]:
    return {
        "symbol": _first(item, ("symbol",)),
        "symbol_name": _first(item, ("symbol_name",)),
        "quantity": _first(item, ("quantity",)),
        "available_quantity": _first(item, ("available_quantity",)),
        "cost_price": _first(item, ("cost_price",)),
        "currency": _first(item, ("currency",)),
        "market": str(_first(item, ("market",), "")),
    }


def _order_to_dict(item: Any) -> dict[str, Any]:
    return {
        "order_id": _first(item, ("order_id",)),
        "symbol": _first(item, ("symbol",)),
        "stock_name": _first(item, ("stock_name",)),
        "side": str(_first(item, ("side",), "")),
        "order_type": str(_first(item, ("order_type",), "")),
        "quantity": _first(item, ("quantity",)),
        "executed_quantity": _first(item, ("executed_quantity",)),
        "price": _first(item, ("price",)),
        "executed_price": _first(item, ("executed_price",)),
        "status": str(_first(item, ("status",), "")),
        "currency": _first(item, ("currency",)),
        "submitted_at": str(_first(item, ("submitted_at",), "")),
    }


def _execution_to_dict(item: Any) -> dict[str, Any]:
    return {
        "order_id": _first(item, ("order_id",)),
        "trade_id": _first(item, ("trade_id",)),
        "symbol": _first(item, ("symbol",)),
        "quantity": _first(item, ("quantity",)),
        "price": _first(item, ("price",)),
        "trade_done_at": str(_first(item, ("trade_done_at",), "")),
    }


def _quote_to_dict(item: Any) -> dict[str, Any]:
    return {
        "symbol": _first(item, ("symbol",)),
        "last": _first(item, ("last_done",)),
        "open": _first(item, ("open",)),
        "high": _first(item, ("high",)),
        "low": _first(item, ("low",)),
        "prev_close": _first(item, ("prev_close",)),
        "volume": _first(item, ("volume",)),
        "turnover": _first(item, ("turnover",)),
        "time": str(_first(item, ("timestamp",), "")),
    }


def _bar_to_dict(item: Any) -> dict[str, Any]:
    return {
        "time": str(_first(item, ("timestamp",), "")),
        "open": _first(item, ("open",)),
        "high": _first(item, ("high",)),
        "low": _first(item, ("low",)),
        "close": _first(item, ("close",)),
        "volume": _first(item, ("volume",)),
        "turnover": _first(item, ("turnover",)),
    }


def _call(obj: Any, name: str, *args: Any, **kwargs: Any) -> Any:
    fn = getattr(obj, name, None)
    if fn is None:
        raise LongbridgeConfigError(f"Longbridge SDK has no method '{name}'")
    return fn(*args, **kwargs)


def _safe_call(obj: Any, name: str, *args: Any) -> Any:
    fn = getattr(obj, name, None)
    if fn is None:
        return None
    try:
        return fn(*args)
    except Exception:  # noqa: BLE001 - optional read, degrade quietly
        return None
