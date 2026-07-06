"""Read-only Alpaca connector via the official ``alpaca-py`` SDK.

Wraps ``TradingClient`` (account/positions/orders) and
``StockHistoricalDataClient`` (quote/bars) for the five read operations. No
order-placement method is exposed here.

Paper-vs-live is structural: ``profile == "paper"`` constructs the client with
``paper=True`` (host ``paper-api.alpaca.markets``) using the paper key pair; a
live profile uses ``paper=False`` (host ``api.alpaca.markets``) with the live
key pair. A paper key cannot reach the live host, so the configured profile —
recorded as ``paper`` in every payload — is the authoritative discriminator.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from src.config.paths import get_runtime_root

CONFIG_FILENAME = "alpaca.json"

PROFILE_ENVIRONMENTS = {
    "paper": "paper",
    "live-readonly": "live",
    "live": "live",
}

PAPER_HOST = "https://paper-api.alpaca.markets"
LIVE_HOST = "https://api.alpaca.markets"


class AlpacaDependencyError(RuntimeError):
    """Raised when the optional ``alpaca-py`` package is not installed."""


class AlpacaConfigError(RuntimeError):
    """Raised when the connector configuration is missing or invalid."""


@dataclass(frozen=True)
class AlpacaConfig:
    """Alpaca connector connection settings.

    Args:
        api_key: Alpaca API key id (paper and live use different keys).
        secret_key: Alpaca API secret key.
        profile: ``paper``, ``live-readonly`` or ``live``.
        feed: Market-data feed, ``iex`` (free) or ``sip`` (paid).
        timeout: Network timeout in seconds.
        readonly: Always true for this layer; order methods are not exposed.
    """

    api_key: str = ""
    secret_key: str = ""
    profile: str = "paper"
    feed: str = "iex"
    timeout: float = 15.0
    readonly: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "AlpacaConfig":
        """Build a config from a JSON-like mapping, normalizing the profile."""
        payload = dict(data or {})
        profile = str(payload.get("profile") or "paper").strip().lower()
        if profile not in PROFILE_ENVIRONMENTS:
            raise AlpacaConfigError("profile must be 'paper', 'live-readonly' or 'live'")
        feed = str(payload.get("feed") or "iex").strip().lower()
        if feed not in ("iex", "sip"):
            raise AlpacaConfigError("feed must be 'iex' or 'sip'")
        return cls(
            api_key=str(payload.get("api_key") or "").strip(),
            secret_key=str(payload.get("secret_key") or "").strip(),
            profile=profile,
            feed=feed,
            timeout=float(payload.get("timeout") or 15.0),
            readonly=bool(payload.get("readonly", True)),
        )

    def with_overrides(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        profile: str | None = None,
        feed: str | None = None,
    ) -> "AlpacaConfig":
        """Return a copy with CLI/tool overrides applied."""
        payload = asdict(self)
        if api_key is not None:
            payload["api_key"] = api_key
        if secret_key is not None:
            payload["secret_key"] = secret_key
        if profile is not None:
            payload["profile"] = profile
        if feed is not None:
            payload["feed"] = feed
        return AlpacaConfig.from_mapping(payload)

    @property
    def environment(self) -> str:
        """Return ``paper`` or ``live`` for this profile."""
        return PROFILE_ENVIRONMENTS.get(self.profile, "paper")

    @property
    def is_paper(self) -> bool:
        """Return whether this profile targets the paper host/key."""
        return self.environment == "paper"

    @property
    def host(self) -> str:
        """Return the REST host this profile connects to."""
        return PAPER_HOST if self.is_paper else LIVE_HOST


_OVERRIDE_KEYS = ("api_key", "secret_key", "profile", "feed")


def build_config(profile_config: Mapping[str, Any] | None = None, overrides: Mapping[str, Any] | None = None) -> "AlpacaConfig":
    """Resolve config: saved file ← profile defaults ← CLI overrides."""
    base = asdict(load_config())
    for key, value in dict(profile_config or {}).items():
        if value is not None:
            base[key] = value
    cfg = AlpacaConfig.from_mapping(base)
    clean = {k: v for k, v in dict(overrides or {}).items() if k in _OVERRIDE_KEYS and v not in (None, "")}
    return cfg.with_overrides(**clean) if clean else cfg


def config_path() -> Path:
    """Return the user-level Alpaca config path."""
    return get_runtime_root() / CONFIG_FILENAME


def load_config() -> AlpacaConfig:
    """Load Alpaca settings from ``~/.vibe-trading/alpaca.json``."""
    path = config_path()
    if not path.exists():
        return AlpacaConfig()
    try:
        return AlpacaConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise AlpacaConfigError(f"invalid Alpaca config at {path}: {exc}") from exc


def save_config(config: AlpacaConfig) -> Path:
    """Persist Alpaca settings with owner-only permissions."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def alpaca_available() -> bool:
    """Return whether the optional ``alpaca-py`` SDK can be imported."""
    try:
        _require_alpaca()
        return True
    except AlpacaDependencyError:
        return False


def check_status(config: AlpacaConfig | None = None) -> dict[str, Any]:
    """Check SDK readiness and config completeness without mutating broker state."""
    cfg = config or load_config()
    report: dict[str, Any] = {
        "status": "ok",
        "config": _public_config(cfg),
        "sdk": {"package": "alpaca-py", "installed": alpaca_available()},
        "paper_guard": "host_separated",
        "host": cfg.host,
    }

    missing = _missing_fields(cfg)
    if missing:
        report["status"] = "error"
        report["error"] = f"Alpaca connector not configured: missing {', '.join(missing)}."
        return report

    if not report["sdk"]["installed"]:
        report["status"] = "error"
        report["error"] = "Optional dependency missing: install with `pip install alpaca-py`."
        return report

    try:
        snapshot = get_account_snapshot(cfg)
    except Exception as exc:  # noqa: BLE001 - health endpoint reports cleanly
        report["status"] = "error"
        report["error"] = str(exc)
        return report

    report["account"] = {
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "account_number": snapshot.get("account", {}).get("account_number"),
    }
    return report


def get_account_snapshot(config: AlpacaConfig | None = None) -> dict[str, Any]:
    """Fetch account summary for the configured account."""
    cfg = config or load_config()
    client = _trading_client(cfg)
    account = client.get_account()
    return {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "host": cfg.host,
        "account": {
            "account_number": _obj_get(account, "account_number"),
            "status": str(_obj_get(account, "status", "")),
            "currency": _obj_get(account, "currency"),
            "cash": _obj_get(account, "cash"),
            "equity": _obj_get(account, "equity"),
            "buying_power": _obj_get(account, "buying_power"),
            "portfolio_value": _obj_get(account, "portfolio_value"),
            "pattern_day_trader": _obj_get(account, "pattern_day_trader"),
            "trading_blocked": _obj_get(account, "trading_blocked"),
        },
    }


def get_positions(config: AlpacaConfig | None = None) -> dict[str, Any]:
    """Fetch current positions for the configured account."""
    cfg = config or load_config()
    client = _trading_client(cfg)
    positions = client.get_all_positions()
    rows = [_position_to_dict(item) for item in _as_iter(positions)]
    return {"status": "ok", "profile": cfg.profile, "is_paper": cfg.is_paper, "positions": rows}


def get_open_orders(config: AlpacaConfig | None = None, *, include_executions: bool = False) -> dict[str, Any]:
    """Fetch open orders and, optionally, recently filled orders."""
    cfg = config or load_config()
    client = _trading_client(cfg)
    _require_alpaca()
    from alpaca.trading.requests import GetOrdersRequest  # type: ignore
    from alpaca.trading.enums import QueryOrderStatus  # type: ignore

    open_req = GetOrdersRequest(status=QueryOrderStatus.OPEN)
    open_orders = client.get_orders(filter=open_req)
    result: dict[str, Any] = {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "open_orders": [_order_to_dict(item) for item in _as_iter(open_orders)],
    }
    if include_executions:
        closed_req = GetOrdersRequest(status=QueryOrderStatus.CLOSED)
        closed = client.get_orders(filter=closed_req)
        result["executions"] = [_order_to_dict(item) for item in _as_iter(closed) if _obj_get(item, "filled_qty")]
    return result


def get_quote(symbol: str, *, config: AlpacaConfig | None = None, **_: Any) -> dict[str, Any]:
    """Fetch a latest quote snapshot for ``symbol``."""
    cfg = config or load_config()
    client = _data_client(cfg)
    from alpaca.data.requests import StockLatestQuoteRequest  # type: ignore

    clean = symbol.strip().upper()
    req = StockLatestQuoteRequest(symbol_or_symbols=clean, feed=_data_feed(cfg))
    quotes = client.get_stock_latest_quote(req)
    quote = quotes.get(clean) if isinstance(quotes, Mapping) else _obj_get(quotes, clean)
    return {
        "status": "ok",
        "symbol": clean,
        "quote": {
            "bid": _obj_get(quote, "bid_price"),
            "ask": _obj_get(quote, "ask_price"),
            "bid_size": _obj_get(quote, "bid_size"),
            "ask_size": _obj_get(quote, "ask_size"),
            "time": str(_obj_get(quote, "timestamp", "")),
        },
    }


def get_historical_bars(
    symbol: str,
    *,
    config: AlpacaConfig | None = None,
    period: str = "1d",
    limit: int = 90,
    **_: Any,
) -> dict[str, Any]:
    """Fetch historical bars for ``symbol`` (``period`` is a canonical token)."""
    cfg = config or load_config()
    client = _data_client(cfg)
    from alpaca.data.requests import StockBarsRequest  # type: ignore
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # type: ignore

    clean = symbol.strip().upper()
    timeframe = _timeframe(period, TimeFrame, TimeFrameUnit)
    req = StockBarsRequest(symbol_or_symbols=clean, timeframe=timeframe, limit=int(limit), feed=_data_feed(cfg))
    bars = client.get_stock_bars(req)
    rows = bars.data.get(clean, []) if hasattr(bars, "data") else _as_iter(bars)
    return {
        "status": "ok",
        "symbol": clean,
        "period": period,
        "bars": [_bar_to_dict(item) for item in _as_iter(rows)],
    }


def place_order(
    config: AlpacaConfig | None = None,
    *,
    symbol: str,
    side: str,
    quantity: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    limit_price: float | None = None,
    time_in_force: str = "day",
) -> dict[str, Any]:
    """Submit an order to the configured Alpaca account.

    Paper-vs-live is structural: ``_trading_client`` builds the client with
    ``paper=cfg.is_paper`` so a paper profile reaches the paper host and a live
    profile reaches the live host. This connector only executes against the
    account in ``config``; deciding whether the order is authorized (mandate,
    kill switch, user opt-in) is the caller's responsibility.

    Args:
        config: Connector config; falls back to the saved config when ``None``.
        symbol: Equity symbol (case-insensitive, whitespace tolerated).
        side: ``buy`` or ``sell``.
        quantity: Share quantity; mutually exclusive with ``notional``.
        notional: Dollar amount (fractional); mutually exclusive with ``quantity``.
        order_type: ``market`` or ``limit``.
        limit_price: Required when ``order_type`` is ``limit``.
        time_in_force: ``day`` or ``gtc``.

    Returns:
        On success ``{"status": "ok", "order_id", "symbol", "side", "profile",
        "is_paper", "order_type", "time_in_force", "quantity", "notional",
        "limit_price", "order_status", "filled_qty"}``. On invalid input or
        submission failure ``{"status": "error", "error": <message>}`` — this
        function fails closed and never raises for caller-controlled mistakes.
    """
    cfg = config or load_config()

    clean_symbol = str(symbol or "").strip().upper()
    if not clean_symbol:
        return {"status": "error", "error": "symbol is required"}

    side_token = str(side or "").strip().lower()
    if side_token not in ("buy", "sell"):
        return {"status": "error", "error": "side must be 'buy' or 'sell'"}

    type_token = str(order_type or "").strip().lower()
    if type_token not in ("market", "limit"):
        return {"status": "error", "error": "order_type must be 'market' or 'limit'"}

    tif_token = str(time_in_force or "").strip().lower()
    if tif_token not in ("day", "gtc"):
        return {"status": "error", "error": "time_in_force must be 'day' or 'gtc'"}

    has_qty = quantity is not None
    has_notional = notional is not None
    if has_qty == has_notional:
        return {"status": "error", "error": "provide exactly one of quantity or notional"}

    qty_value: float | None = None
    notional_value: float | None = None
    try:
        if has_qty:
            qty_value = float(quantity)  # type: ignore[arg-type]
            if qty_value <= 0:
                return {"status": "error", "error": "quantity must be positive"}
        else:
            notional_value = float(notional)  # type: ignore[arg-type]
            if notional_value <= 0:
                return {"status": "error", "error": "notional must be positive"}
    except (TypeError, ValueError):
        return {"status": "error", "error": "quantity/notional must be numeric"}

    limit_value: float | None = None
    if type_token == "limit":
        if limit_price is None:
            return {"status": "error", "error": "limit order requires limit_price"}
        try:
            limit_value = float(limit_price)
        except (TypeError, ValueError):
            return {"status": "error", "error": "limit_price must be numeric"}
        if limit_value <= 0:
            return {"status": "error", "error": "limit_price must be positive"}

    try:
        client = _trading_client(cfg)
        from alpaca.trading.enums import OrderSide, TimeInForce  # type: ignore
        from alpaca.trading.requests import (  # type: ignore
            LimitOrderRequest,
            MarketOrderRequest,
        )

        order_side = OrderSide.BUY if side_token == "buy" else OrderSide.SELL
        tif = TimeInForce.DAY if tif_token == "day" else TimeInForce.GTC
        amount = {"qty": qty_value} if has_qty else {"notional": notional_value}

        if type_token == "limit":
            req = LimitOrderRequest(
                symbol=clean_symbol,
                side=order_side,
                time_in_force=tif,
                limit_price=limit_value,
                **amount,
            )
        else:
            req = MarketOrderRequest(
                symbol=clean_symbol,
                side=order_side,
                time_in_force=tif,
                **amount,
            )

        order = client.submit_order(order_data=req)
    except AlpacaDependencyError as exc:
        return {"status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - submission errors are reported, not raised
        return {"status": "error", "error": str(exc)}

    return {
        "status": "ok",
        "order_id": str(_obj_get(order, "id", "")),
        "symbol": clean_symbol,
        "side": side_token,
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "order_type": type_token,
        "time_in_force": tif_token,
        "quantity": qty_value,
        "notional": notional_value,
        "limit_price": limit_value,
        "order_status": str(_obj_get(order, "status", "")),
        "filled_qty": _obj_get(order, "filled_qty"),
    }


def cancel_order(
    config: AlpacaConfig | None = None,
    order_id: str = "",
    *,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Cancel an open order on the configured Alpaca account.

    Args:
        config: Connector config; falls back to the saved config when ``None``.
        order_id: Alpaca order id to cancel.
        symbol: Optional symbol, echoed back for caller bookkeeping only;
            Alpaca cancels purely by id.

    Returns:
        On success ``{"status": "ok", "order_id", "symbol", "side", "profile",
        "is_paper", "cancelled"}``. On invalid input or cancel failure
        ``{"status": "error", "error": <message>}`` — fails closed, never raises.
    """
    cfg = config or load_config()

    clean_id = str(order_id or "").strip()
    if not clean_id:
        return {"status": "error", "error": "order_id is required"}

    try:
        client = _trading_client(cfg)
        client.cancel_order_by_id(clean_id)
    except AlpacaDependencyError as exc:
        return {"status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - cancel errors are reported, not raised
        return {"status": "error", "error": str(exc)}

    return {
        "status": "ok",
        "order_id": clean_id,
        "symbol": symbol.strip().upper() if isinstance(symbol, str) and symbol.strip() else None,
        "side": None,
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "cancelled": True,
    }


def _timeframe(period: str, time_frame_cls: Any, unit_cls: Any) -> Any:
    """Map a canonical period token to an Alpaca ``TimeFrame``.

    Case-sensitive: ``1m`` is one minute, ``1M`` is one month.
    """
    token = period.strip()
    minute_amounts = {"1m": 1, "5m": 5, "15m": 15, "30m": 30}
    if token in minute_amounts:
        return time_frame_cls(minute_amounts[token], unit_cls.Minute)
    if token in ("1h", "4h"):
        return time_frame_cls(1 if token == "1h" else 4, unit_cls.Hour)
    if token == "1w":
        return time_frame_cls(1, unit_cls.Week)
    if token == "1M":
        return time_frame_cls(1, unit_cls.Month)
    return time_frame_cls.Day


# ---------------------------------------------------------------------------
# SDK plumbing
# ---------------------------------------------------------------------------


def _require_alpaca() -> ModuleType:
    try:
        import alpaca  # type: ignore
    except ModuleNotFoundError as exc:
        raise AlpacaDependencyError("alpaca-py is not installed; run `pip install alpaca-py`.") from exc
    return alpaca


def _trading_client(cfg: AlpacaConfig):
    _require_alpaca()
    from alpaca.trading.client import TradingClient  # type: ignore

    return TradingClient(cfg.api_key, cfg.secret_key, paper=cfg.is_paper)


def _data_client(cfg: AlpacaConfig):
    _require_alpaca()
    from alpaca.data.historical import StockHistoricalDataClient  # type: ignore

    return StockHistoricalDataClient(cfg.api_key, cfg.secret_key)


def _data_feed(cfg: AlpacaConfig):
    """Map the configured ``feed`` string to the Alpaca ``DataFeed`` enum."""
    _require_alpaca()
    from alpaca.data.enums import DataFeed  # type: ignore

    return DataFeed.SIP if cfg.feed == "sip" else DataFeed.IEX


def _missing_fields(cfg: AlpacaConfig) -> list[str]:
    missing = []
    if not cfg.api_key:
        missing.append("api_key")
    if not cfg.secret_key:
        missing.append("secret_key")
    return missing


def _public_config(cfg: AlpacaConfig) -> dict[str, Any]:
    """Config snapshot with secrets redacted."""
    data = asdict(cfg)
    if data.get("secret_key"):
        data["secret_key"] = "***redacted***"
    if data.get("api_key"):
        data["api_key"] = data["api_key"][:4] + "***"
    data["host"] = cfg.host
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


def _position_to_dict(item: Any) -> dict[str, Any]:
    return {
        "symbol": _obj_get(item, "symbol"),
        "side": str(_obj_get(item, "side", "")),
        "quantity": _obj_get(item, "qty"),
        "average_cost": _obj_get(item, "avg_entry_price"),
        "market_value": _obj_get(item, "market_value"),
        "current_price": _obj_get(item, "current_price"),
        "unrealized_pnl": _obj_get(item, "unrealized_pl"),
        "cost_basis": _obj_get(item, "cost_basis"),
    }


def _order_to_dict(item: Any) -> dict[str, Any]:
    return {
        "order_id": str(_obj_get(item, "id", "")),
        "symbol": _obj_get(item, "symbol"),
        "side": str(_obj_get(item, "side", "")),
        "order_type": str(_obj_get(item, "order_type", "") or _obj_get(item, "type", "")),
        "quantity": _obj_get(item, "qty"),
        "notional": _obj_get(item, "notional"),
        "filled_qty": _obj_get(item, "filled_qty"),
        "filled_avg_price": _obj_get(item, "filled_avg_price"),
        "limit_price": _obj_get(item, "limit_price"),
        "status": str(_obj_get(item, "status", "")),
        "submitted_at": str(_obj_get(item, "submitted_at", "")),
    }


def _bar_to_dict(item: Any) -> dict[str, Any]:
    return {
        "time": str(_obj_get(item, "timestamp", "")),
        "open": _obj_get(item, "open"),
        "high": _obj_get(item, "high"),
        "low": _obj_get(item, "low"),
        "close": _obj_get(item, "close"),
        "volume": _obj_get(item, "volume"),
    }
