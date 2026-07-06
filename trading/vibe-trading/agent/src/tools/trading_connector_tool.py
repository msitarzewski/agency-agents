"""Connector-first trading tools.

Tools take an optional ``connection`` profile id. If omitted, they use the
selected profile from ``~/.vibe-trading/trading-connections.json``.
"""

from __future__ import annotations

import json
from typing import Any

from src.agent.tools import BaseTool
from src.trading.profiles import (
    list_profiles,
    load_selected_profile_id,
    profile_by_id,
    save_selected_profile_id,
)
from src.trading.service import (
    cancel_order,
    check_connection,
    get_account,
    get_history,
    get_open_orders,
    get_positions,
    get_quote,
    place_order,
)


def _json_result(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _connection(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _num_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


TRADING_COMMON_PARAMETERS = {
    "connection": {
        "type": "string",
        "description": "Trading connector profile id, e.g. ibkr-paper-local or robinhood-live-mcp. Defaults to the selected profile.",
    },
    "host": {
        "type": "string",
        "description": "Optional local TWS/Gateway host override for local profiles.",
    },
    "port": {
        "type": "integer",
        "description": "Optional local TWS/Gateway port override for local profiles.",
    },
    "client_id": {
        "type": "integer",
        "description": "Optional local TWS/Gateway client id override for local profiles.",
    },
    "account": {
        "type": "string",
        "description": "Optional account code filter when supported by the connector.",
    },
}


def _overrides(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "host": _connection(kwargs.get("host")),
        "port": _int_or_none(kwargs.get("port")),
        "client_id": _int_or_none(kwargs.get("client_id")),
        "account": _connection(kwargs.get("account")),
    }


class TradingConnectionsTool(BaseTool):
    """List available trading connector profiles."""

    name = "trading_connections"
    description = (
        "List selectable trading connector profiles. Connectors come first; paper/live is a profile attribute."
    )
    parameters = {"type": "object", "properties": {}, "required": []}
    repeatable = True
    is_readonly = True

    def execute(self, **_: Any) -> str:
        """List connector profiles and mark the selected one."""
        try:
            selected = load_selected_profile_id()
            return _json_result(
                {
                    "status": "ok",
                    "selected_profile": selected,
                    "profiles": [profile.to_dict(selected=profile.id == selected) for profile in list_profiles()],
                }
            )
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingSelectConnectionTool(BaseTool):
    """Select the default trading connector profile."""

    name = "trading_select_connection"
    description = "Select the default trading connector profile for subsequent trading_* tool calls."
    parameters = {
        "type": "object",
        "properties": {
            "connection": {
                "type": "string",
                "description": "Profile id to select, e.g. ibkr-paper-local.",
            }
        },
        "required": ["connection"],
    }
    repeatable = True
    is_readonly = False

    def execute(self, **kwargs: Any) -> str:
        """Persist the selected profile id."""
        try:
            profile = profile_by_id(str(kwargs["connection"]).strip())
            path = save_selected_profile_id(profile.id)
            return _json_result({"status": "ok", "selected_profile": profile.id, "path": str(path)})
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingCheckTool(BaseTool):
    """Check a trading connector profile."""

    name = "trading_check"
    description = "Check whether a trading connector profile is configured and reachable. This never places orders."
    parameters = {
        "type": "object",
        "properties": TRADING_COMMON_PARAMETERS,
        "required": [],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Check connector readiness."""
        try:
            return _json_result(check_connection(_connection(kwargs.get("connection")), **_overrides(kwargs)))
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingAccountTool(BaseTool):
    """Read account summary from a trading connector profile."""

    name = "trading_account"
    description = "Read account summary from the selected trading connector profile. Read-only."
    parameters = TradingCheckTool.parameters
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Read account summary."""
        try:
            return _json_result(get_account(_connection(kwargs.get("connection")), **_overrides(kwargs)))
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingPositionsTool(BaseTool):
    """Read positions from a trading connector profile."""

    name = "trading_positions"
    description = "Read positions from the selected trading connector profile. Read-only."
    parameters = TradingCheckTool.parameters
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Read positions."""
        try:
            return _json_result(get_positions(_connection(kwargs.get("connection")), **_overrides(kwargs)))
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingOrdersTool(BaseTool):
    """Read open orders from a trading connector profile."""

    name = "trading_orders"
    description = "Read open orders from the selected trading connector profile. Read-only."
    parameters = {
        "type": "object",
        "properties": {
            **TRADING_COMMON_PARAMETERS,
            "include_executions": {"type": "boolean", "default": False},
        },
        "required": [],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Read open orders."""
        try:
            return _json_result(
                get_open_orders(
                    _connection(kwargs.get("connection")),
                    include_executions=bool(kwargs.get("include_executions", False)),
                    **_overrides(kwargs),
                )
            )
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingQuoteTool(BaseTool):
    """Read a quote from a trading connector profile."""

    name = "trading_quote"
    description = "Read a quote snapshot from the selected trading connector profile. Read-only."
    parameters = {
        "type": "object",
        "properties": {
            **TRADING_COMMON_PARAMETERS,
            "symbol": {"type": "string", "description": "Symbol, e.g. AAPL"},
            "exchange": {"type": "string", "default": "SMART"},
            "currency": {"type": "string", "default": "USD"},
            "sec_type": {"type": "string", "default": "STK"},
        },
        "required": ["symbol"],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Read quote snapshot."""
        try:
            return _json_result(
                get_quote(
                    str(kwargs["symbol"]),
                    _connection(kwargs.get("connection")),
                    exchange=str(kwargs.get("exchange") or "SMART"),
                    currency=str(kwargs.get("currency") or "USD"),
                    sec_type=str(kwargs.get("sec_type") or "STK"),
                    **_overrides(kwargs),
                )
            )
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingHistoryTool(BaseTool):
    """Read historical bars from a trading connector profile."""

    name = "trading_history"
    description = "Read historical bars from the selected trading connector profile. Read-only."
    parameters = {
        "type": "object",
        "properties": {
            **TradingQuoteTool.parameters["properties"],
            "duration": {"type": "string", "default": "30 D", "description": "IBKR (local_tws) duration string."},
            "bar_size": {"type": "string", "default": "1 day", "description": "IBKR (local_tws) bar size."},
            "what_to_show": {"type": "string", "default": "TRADES"},
            "use_rth": {"type": "boolean", "default": True},
            "period": {
                "type": "string",
                "default": "1d",
                "description": "Bar interval for SDK connectors (broker_sdk): 1m/5m/15m/30m/1h/4h/1d/1w/1M.",
            },
            "limit": {"type": "integer", "default": 90, "description": "Number of bars for SDK connectors."},
        },
        "required": ["symbol"],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Read historical bars."""
        try:
            return _json_result(
                get_history(
                    str(kwargs["symbol"]),
                    _connection(kwargs.get("connection")),
                    exchange=str(kwargs.get("exchange") or "SMART"),
                    currency=str(kwargs.get("currency") or "USD"),
                    sec_type=str(kwargs.get("sec_type") or "STK"),
                    duration=str(kwargs.get("duration") or "30 D"),
                    bar_size=str(kwargs.get("bar_size") or "1 day"),
                    what_to_show=str(kwargs.get("what_to_show") or "TRADES"),
                    use_rth=bool(kwargs.get("use_rth", True)),
                    period=str(kwargs.get("period") or "1d"),
                    limit=int(kwargs.get("limit") or 90),
                    **_overrides(kwargs),
                )
            )
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingPlaceOrderTool(BaseTool):
    """Place an order through a trading connector profile.

    Paper profiles place against the broker's sandbox account. Live profiles
    route through the bounded-autonomy mandate gate (mandate + kill switch +
    fail-closed pre-trade checks + audit) before any order reaches the broker.
    Not read-only; not repeatable (an order must never be silently re-issued).
    """

    name = "trading_place_order"
    description = (
        "Place an order through the selected trading connector profile. Paper "
        "profiles trade a sandbox account; live profiles are gated by the user's "
        "mandate and kill switch. side is 'buy' or 'sell'; give exactly one of "
        "quantity (units) or notional (account-currency amount)."
    )
    parameters = {
        "type": "object",
        "properties": {
            **TRADING_COMMON_PARAMETERS,
            "symbol": {"type": "string", "description": "Symbol, e.g. AAPL, BTC-USDT, 700.HK, HK.00700."},
            "side": {"type": "string", "enum": ["buy", "sell"]},
            "quantity": {"type": "number", "description": "Order size in units/shares/contracts. Exactly one of quantity/notional."},
            "notional": {"type": "number", "description": "Order size as an account-currency amount. Exactly one of quantity/notional."},
            "order_type": {"type": "string", "enum": ["market", "limit"], "default": "market"},
            "limit_price": {"type": "number", "description": "Required for limit orders."},
            "time_in_force": {"type": "string", "enum": ["day", "gtc"], "default": "day"},
        },
        "required": ["symbol", "side"],
    }
    repeatable = False
    is_readonly = False

    def execute(self, **kwargs: Any) -> str:
        """Place an order via the connector profile."""
        try:
            return _json_result(
                place_order(
                    str(kwargs["symbol"]),
                    _connection(kwargs.get("connection")),
                    side=str(kwargs.get("side") or ""),
                    quantity=_num_or_none(kwargs.get("quantity")),
                    notional=_num_or_none(kwargs.get("notional")),
                    order_type=str(kwargs.get("order_type") or "market"),
                    limit_price=_num_or_none(kwargs.get("limit_price")),
                    time_in_force=str(kwargs.get("time_in_force") or "day"),
                    **_overrides(kwargs),
                )
            )
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})


class TradingCancelOrderTool(BaseTool):
    """Cancel an order through a trading connector profile (risk-reducing)."""

    name = "trading_cancel_order"
    description = "Cancel an open order on the selected trading connector profile by order id."
    parameters = {
        "type": "object",
        "properties": {
            **TRADING_COMMON_PARAMETERS,
            "order_id": {"type": "string", "description": "Broker order id to cancel."},
            "symbol": {"type": "string", "description": "Symbol (required by some brokers, e.g. OKX/Binance)."},
        },
        "required": ["order_id"],
    }
    repeatable = False
    is_readonly = False

    def execute(self, **kwargs: Any) -> str:
        """Cancel an order via the connector profile."""
        try:
            return _json_result(
                cancel_order(
                    str(kwargs["order_id"]),
                    _connection(kwargs.get("connection")),
                    symbol=_connection(kwargs.get("symbol")),
                    **_overrides(kwargs),
                )
            )
        except Exception as exc:  # noqa: BLE001
            return _json_result({"status": "error", "error": str(exc)})
