"""Read-only + order Dhan connector via the official ``dhanhq`` SDK.

Wraps ``DhanHQ`` client for account, positions, orders, quotes, and historical
data. Supports NSE/BSE equities and F&O (NIFTY/BANKNIFTY options).

Paper-vs-live: Dhan has no sandbox environment. Paper mode uses the same API
for market data reads but simulates orders locally. Live mode places real orders
through Dhan's production API.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from src.config.paths import get_runtime_root

CONFIG_FILENAME = "dhan.json"

PROFILE_ENVIRONMENTS = {
    "paper": "paper",
    "live-readonly": "live",
    "live": "live",
}

DHAN_API_URL = "https://api.dhan.co"

#: Returned by order methods when a non-paper config reaches them. Dhan exposes
#: no runtime paper/live discriminator (same token reads the same account), so —
#: following the Longbridge precedent — the connector is structurally capped at
#: paper and never opens a live order path.
_PAPER_ONLY_ERROR = (
    "Dhan connector is paper-only: it exposes no runtime paper/live "
    "discriminator, so live order placement is not supported. Use a "
    "dhan-paper-* profile."
)


class DhanDependencyError(RuntimeError):
    """Raised when the optional ``dhanhq`` package is not installed."""


class DhanConfigError(RuntimeError):
    """Raised when the connector configuration is missing or invalid."""


# ---------------------------------------------------------------------------
# NSE instrument constants for F&O
# ---------------------------------------------------------------------------

#: NSE exchange segment codes used by Dhan API.
class DhanSegment:
    NSE_EQ = "NSE_EQ"
    NSE_FNO = "NSE_FNO"
    BSE_EQ = "BSE_EQ"
    BSE_FNO = "BSE_FNO"
    MCX_COMM = "MCX_COMM"
    CUR = "CUR"


#: Common NIFTY/BANKNIFTY security IDs (Dhan uses numeric security IDs).
NIFTY_SECURITY_ID = "13"      # NIFTY 50 index
BANKNIFTY_SECURITY_ID = "25"  # BANK NIFTY index


@dataclass(frozen=True)
class DhanConfig:
    """Dhan connector connection settings.

    Args:
        client_id: Dhan client ID (visible on dhan.co dashboard).
        access_token: Dhan API access token (generated from dhan.co).
        profile: ``paper``, ``live-readonly`` or ``live``.
        timeout: Network timeout in seconds.
        readonly: Whether order placement is disabled.
    """

    client_id: str = ""
    access_token: str = ""
    profile: str = "paper"
    timeout: float = 15.0
    readonly: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "DhanConfig":
        """Build a config from a JSON-like mapping."""
        payload = dict(data or {})
        profile = str(payload.get("profile") or "paper").strip().lower()
        if profile not in PROFILE_ENVIRONMENTS:
            raise DhanConfigError("profile must be 'paper', 'live-readonly' or 'live'")
        return cls(
            client_id=str(payload.get("client_id") or "").strip(),
            access_token=str(payload.get("access_token") or "").strip(),
            profile=profile,
            timeout=float(payload.get("timeout") or 15.0),
            readonly=bool(payload.get("readonly", True)),
        )

    def with_overrides(
        self,
        *,
        client_id: str | None = None,
        access_token: str | None = None,
        profile: str | None = None,
    ) -> "DhanConfig":
        """Return a copy with CLI/tool overrides applied."""
        payload = asdict(self)
        if client_id is not None:
            payload["client_id"] = client_id
        if access_token is not None:
            payload["access_token"] = access_token
        if profile is not None:
            payload["profile"] = profile
        return DhanConfig.from_mapping(payload)

    @property
    def environment(self) -> str:
        return PROFILE_ENVIRONMENTS.get(self.profile, "paper")

    @property
    def is_paper(self) -> bool:
        return self.environment == "paper"


_OVERRIDE_KEYS = ("client_id", "access_token", "profile")


def build_config(
    profile_config: Mapping[str, Any] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> "DhanConfig":
    """Resolve config: saved file ← profile defaults ← CLI overrides."""
    base = asdict(load_config())
    for key, value in dict(profile_config or {}).items():
        if value is not None:
            base[key] = value
    cfg = DhanConfig.from_mapping(base)
    clean = {
        k: v
        for k, v in dict(overrides or {}).items()
        if k in _OVERRIDE_KEYS and v not in (None, "")
    }
    return cfg.with_overrides(**clean) if clean else cfg


def config_path() -> Path:
    return get_runtime_root() / CONFIG_FILENAME


def load_config() -> DhanConfig:
    path = config_path()
    if not path.exists():
        return DhanConfig()
    try:
        return DhanConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise DhanConfigError(f"invalid Dhan config at {path}: {exc}") from exc


def save_config(config: DhanConfig) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def dhan_available() -> bool:
    try:
        _require_dhan()
        return True
    except DhanDependencyError:
        return False


# ---------------------------------------------------------------------------
# Five read operations + order placement
# ---------------------------------------------------------------------------


def check_status(config: DhanConfig | None = None) -> dict[str, Any]:
    """Check SDK readiness and config completeness."""
    cfg = config or load_config()
    report: dict[str, Any] = {
        "status": "ok",
        "config": _public_config(cfg),
        "sdk": {"package": "dhanhq", "installed": dhan_available()},
        "paper_guard": "simulated_locally",
        "host": DHAN_API_URL,
    }

    missing = _missing_fields(cfg)
    if missing:
        report["status"] = "error"
        report["error"] = f"Dhan connector not configured: missing {', '.join(missing)}."
        return report

    if not report["sdk"]["installed"]:
        report["status"] = "error"
        report["error"] = "Optional dependency missing: install with `pip install dhanhq`."
        return report

    try:
        get_account_snapshot(cfg)  # connectivity probe; result unused
    except Exception as exc:
        report["status"] = "error"
        report["error"] = str(exc)
        return report

    report["account"] = {
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
    }
    return report


def get_account_snapshot(config: DhanConfig | None = None) -> dict[str, Any]:
    """Fetch fund limits (account summary) for the configured account."""
    cfg = config or load_config()
    client = _dhan_client(cfg)
    funds = client.get_fund_limits()

    return {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "host": DHAN_API_URL,
        "account": {
            "currency": "INR",
            "available_margin": _safe_get(funds, "data", "availabelBalance"),
            "used_margin": _safe_get(funds, "data", "utilizedAmount"),
            "collateral": _safe_get(funds, "data", "collateralAmount"),
        },
    }


def get_positions(config: DhanConfig | None = None) -> dict[str, Any]:
    """Fetch current positions."""
    cfg = config or load_config()
    client = _dhan_client(cfg)
    positions = client.get_positions()

    rows = []
    for item in _as_list(positions.get("data")):
        rows.append({
            "symbol": item.get("tradingSymbol", ""),
            "security_id": item.get("securityId", ""),
            "exchange_segment": item.get("exchangeSegment", ""),
            "product_type": item.get("productType", ""),
            "quantity": item.get("netQty", 0),
            "average_cost": item.get("costPrice", 0),
            "current_price": item.get("currentPrice", 0),
            "unrealized_pnl": item.get("realizedProfit", 0),
            "day_buy_qty": item.get("dayBuyQty", 0),
            "day_sell_qty": item.get("daySellQty", 0),
        })

    return {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "positions": rows,
    }


def get_open_orders(
    config: DhanConfig | None = None,
    *,
    include_executions: bool = False,
) -> dict[str, Any]:
    """Fetch open orders and optionally executed trades."""
    cfg = config or load_config()
    client = _dhan_client(cfg)
    orders = client.get_order_list()

    open_orders = []
    executions = []
    for item in _as_list(orders.get("data")):
        order_dict = _order_to_dict(item)
        status = str(item.get("orderStatus", "")).upper()
        if status in ("PENDING", "TRANSIT", "OPEN"):
            open_orders.append(order_dict)
        elif include_executions and status in ("TRADED", "FILLED"):
            executions.append(order_dict)

    result: dict[str, Any] = {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "open_orders": open_orders,
    }
    if include_executions:
        result["executions"] = executions
    return result


def get_quote(
    symbol: str,
    *,
    config: DhanConfig | None = None,
    security_id: str | None = None,
    exchange_segment: str = "NSE_EQ",
) -> dict[str, Any]:
    """Fetch LTP + OHLC for a symbol.

    Dhan requires numeric ``security_id`` + ``exchange_segment`` for quotes.
    If ``security_id`` is not provided, attempt to use ``symbol`` as the ID.
    """
    cfg = config or load_config()
    client = _dhan_client(cfg)

    sec_id = str(security_id or symbol).strip()
    segment = exchange_segment.strip().upper()

    try:
        ltp_data = client.ltp(security_id=sec_id, exchange_segment=segment)
        ohlc_data = client.ohlc(security_id=sec_id, exchange_segment=segment)
    except Exception as exc:
        return {"status": "error", "error": str(exc), "symbol": symbol}

    return {
        "status": "ok",
        "symbol": symbol,
        "security_id": sec_id,
        "exchange_segment": segment,
        "quote": {
            "ltp": _safe_get(ltp_data, "data", "lastPrice"),
            "open": _safe_get(ohlc_data, "data", "open"),
            "high": _safe_get(ohlc_data, "data", "high"),
            "low": _safe_get(ohlc_data, "data", "low"),
            "close": _safe_get(ohlc_data, "data", "close"),
            "volume": _safe_get(ohlc_data, "data", "volume"),
        },
    }


def get_historical_bars(
    symbol: str,
    *,
    config: DhanConfig | None = None,
    security_id: str | None = None,
    exchange_segment: str = "NSE_EQ",
    instrument_type: str = "EQUITY",
    period: str = "1d",
    limit: int = 90,
) -> dict[str, Any]:
    """Fetch historical OHLCV bars.

    ``period`` tokens: ``1m``, ``5m``, ``15m``, ``30m`` → intraday candles.
    ``1d`` → daily candles. Dhan's intraday data is limited to last 5 trading
    days; daily goes back much further.
    """
    cfg = config or load_config()
    client = _dhan_client(cfg)

    sec_id = str(security_id or symbol).strip()
    segment = exchange_segment.strip().upper()

    from datetime import datetime, timedelta

    to_date = datetime.now()
    # Intraday: max 5 days back; daily: use limit
    if period in ("1m", "5m", "15m", "30m"):
        from_date = to_date - timedelta(days=5)
    else:
        from_date = to_date - timedelta(days=min(limit * 2, 365))

    try:
        if period in ("1m", "5m", "15m", "30m"):
            data = client.intraday_daily_candle_data(
                security_id=sec_id,
                exchange_segment=segment,
                instrument_type=instrument_type,
            )
        else:
            data = client.historical_daily_candle_data(
                security_id=sec_id,
                exchange_segment=segment,
                instrument_type=instrument_type,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
            )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "symbol": symbol}

    bars = []
    for candle in _as_list(data.get("data", {}).get("candles")):
        if len(candle) >= 6:
            bars.append({
                "time": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
            })

    return {
        "status": "ok",
        "symbol": symbol,
        "security_id": sec_id,
        "period": period,
        "bars": bars[-limit:],
    }


def place_order(
    config: DhanConfig | None = None,
    *,
    symbol: str,
    side: str,
    quantity: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    limit_price: float | None = None,
    time_in_force: str = "day",
    security_id: str | None = None,
    exchange_segment: str = "NSE_EQ",
    product_type: str = "INTRADAY",
) -> dict[str, Any]:
    """Place a PAPER-ONLY order on Dhan (simulated locally).

    Dhan exposes no runtime paper/live discriminator, so this connector is
    structurally capped at paper: the very first check refuses any config whose
    ``environment`` is not ``paper``. There is therefore no live order path
    here, by design. Paper orders are simulated locally — Dhan has no sandbox.

    Args:
        symbol: Trading symbol or security ID.
        side: ``buy`` or ``sell``.
        quantity: Number of shares/lots.
        order_type: ``market`` or ``limit``.
        limit_price: Required for limit orders.
        security_id: Dhan numeric security ID.
        exchange_segment: NSE_EQ, NSE_FNO, BSE_EQ, etc.
        product_type: INTRADAY, CNC (delivery), MARGIN.
    """
    cfg = config or load_config()

    # ---- HARD GUARD: structurally paper-only (must run before anything) ----
    if not cfg.is_paper:
        return {"status": "error", "error": _PAPER_ONLY_ERROR}

    clean_symbol = str(symbol or "").strip().upper()
    if not clean_symbol:
        return {"status": "error", "error": "symbol is required"}

    side_token = str(side or "").strip().upper()
    if side_token not in ("BUY", "SELL"):
        return {"status": "error", "error": "side must be 'buy' or 'sell'"}

    type_token = str(order_type or "").strip().upper()
    if type_token not in ("MARKET", "LIMIT"):
        return {"status": "error", "error": "order_type must be 'market' or 'limit'"}

    if quantity is None or float(quantity) <= 0:
        return {"status": "error", "error": "quantity must be positive"}

    qty = int(float(quantity))
    sec_id = str(security_id or symbol).strip()

    if type_token == "LIMIT" and limit_price is None:
        return {"status": "error", "error": "limit order requires limit_price"}

    price = float(limit_price) if limit_price is not None else 0

    # Paper-only: simulate locally (Dhan has no sandbox).
    return {
        "status": "ok",
        "order_id": f"PAPER-{sec_id}-{side_token}-{qty}",
        "symbol": clean_symbol,
        "security_id": sec_id,
        "side": side_token.lower(),
        "profile": cfg.profile,
        "is_paper": True,
        "paper_guard": "simulated_locally",
        "order_type": type_token.lower(),
        "quantity": qty,
        "limit_price": price if type_token == "LIMIT" else None,
        "order_status": "simulated_fill",
        "exchange_segment": exchange_segment,
        "product_type": product_type,
    }


def cancel_order(
    config: DhanConfig | None = None,
    order_id: str = "",
    *,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Cancel a PAPER-ONLY order on Dhan (simulated locally).

    Like :func:`place_order`, the first check refuses any non-paper config —
    this connector never reaches a live order, so it never cancels one.
    """
    cfg = config or load_config()

    # ---- HARD GUARD: structurally paper-only (must run before anything) ----
    if not cfg.is_paper:
        return {"status": "error", "error": _PAPER_ONLY_ERROR}

    clean_id = str(order_id or "").strip()
    if not clean_id:
        return {"status": "error", "error": "order_id is required"}

    return {
        "status": "ok",
        "order_id": clean_id,
        "symbol": symbol.strip().upper() if isinstance(symbol, str) and symbol.strip() else None,
        "profile": cfg.profile,
        "is_paper": True,
        "cancelled": True,
    }


# ---------------------------------------------------------------------------
# SDK plumbing
# ---------------------------------------------------------------------------


def _require_dhan() -> ModuleType:
    try:
        import dhanhq  # type: ignore
    except ModuleNotFoundError as exc:
        raise DhanDependencyError(
            "dhanhq is not installed; run `pip install dhanhq`."
        ) from exc
    return dhanhq


def _dhan_client(cfg: DhanConfig):
    _require_dhan()
    from dhanhq import dhanhq as DhanHQ  # type: ignore

    if not cfg.client_id or not cfg.access_token:
        raise DhanConfigError(
            "Dhan connector not configured: set client_id and access_token "
            "in ~/.vibe-trading/dhan.json or via environment."
        )
    return DhanHQ(cfg.client_id, cfg.access_token)


def _missing_fields(cfg: DhanConfig) -> list[str]:
    missing = []
    if not cfg.client_id:
        missing.append("client_id")
    if not cfg.access_token:
        missing.append("access_token")
    return missing


def _public_config(cfg: DhanConfig) -> dict[str, Any]:
    data = asdict(cfg)
    if data.get("access_token"):
        data["access_token"] = data["access_token"][:8] + "***"
    return data


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _safe_get(data: Any, *keys: str) -> Any:
    """Safely traverse nested dicts."""
    for key in keys:
        if isinstance(data, Mapping):
            data = data.get(key)
        else:
            return None
    return data


def _order_to_dict(item: Any) -> dict[str, Any]:
    return {
        "order_id": str(item.get("orderId", "")),
        "symbol": item.get("tradingSymbol", ""),
        "security_id": item.get("securityId", ""),
        "side": item.get("transactionType", "").lower(),
        "order_type": item.get("orderType", "").lower(),
        "quantity": item.get("quantity", 0),
        "filled_qty": item.get("filledQty", 0),
        "price": item.get("price", 0),
        "status": item.get("orderStatus", ""),
        "exchange_segment": item.get("exchangeSegment", ""),
        "product_type": item.get("productType", ""),
    }
