"""Read-only + order Shoonya (Finvasia) connector via ``NorenRestApiPy`` SDK.

Wraps the Shoonya/NorenApi client for account, positions, orders, quotes, and
historical data. Supports NSE/BSE equities and F&O (NIFTY/BANKNIFTY options).

Zero brokerage on ALL segments — the cheapest Indian broker for algo trading.

Authentication: Shoonya uses a TOTP-based login flow. The user must provide:
- user_id: Shoonya login ID
- password: Login password
- vendor_code: API vendor code (from Shoonya dashboard)
- api_secret: API secret key
- totp_secret: TOTP secret for 2FA (base32 encoded)

Paper-vs-live: Shoonya has no sandbox. Paper mode uses the same API for market
data reads but simulates orders locally.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from src.config.paths import get_runtime_root

CONFIG_FILENAME = "shoonya.json"

PROFILE_ENVIRONMENTS = {
    "paper": "paper",
    "live-readonly": "live",
    "live": "live",
}

SHOONYA_API_URL = "https://api.shoonya.com/NorenWClientTP"

#: Returned by order methods when a non-paper config reaches them. Shoonya
#: exposes no runtime paper/live discriminator (TOTP login reaches the same real
#: account), so — following the Longbridge precedent — the connector is
#: structurally capped at paper and never opens a live order path.
_PAPER_ONLY_ERROR = (
    "Shoonya connector is paper-only: it exposes no runtime paper/live "
    "discriminator, so live order placement is not supported. Use a "
    "shoonya-paper-* profile."
)


class ShoonyaDependencyError(RuntimeError):
    """Raised when ``NorenRestApiPy`` is not installed."""


class ShoonyaConfigError(RuntimeError):
    """Raised when config is missing or invalid."""


# ---------------------------------------------------------------------------
# NSE exchange codes for Shoonya
# ---------------------------------------------------------------------------

class ShoonyaExchange:
    NSE = "NSE"
    NFO = "NFO"      # NSE F&O
    BSE = "BSE"
    BFO = "BFO"      # BSE F&O
    CDS = "CDS"      # Currency
    MCX = "MCX"      # Commodity


@dataclass(frozen=True)
class ShoonyaConfig:
    """Shoonya connector connection settings."""

    user_id: str = ""
    password: str = ""
    vendor_code: str = ""
    api_secret: str = ""
    totp_secret: str = ""
    profile: str = "paper"
    timeout: float = 15.0
    readonly: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "ShoonyaConfig":
        payload = dict(data or {})
        profile = str(payload.get("profile") or "paper").strip().lower()
        if profile not in PROFILE_ENVIRONMENTS:
            raise ShoonyaConfigError("profile must be 'paper', 'live-readonly' or 'live'")
        return cls(
            user_id=str(payload.get("user_id") or "").strip(),
            password=str(payload.get("password") or "").strip(),
            vendor_code=str(payload.get("vendor_code") or "").strip(),
            api_secret=str(payload.get("api_secret") or "").strip(),
            totp_secret=str(payload.get("totp_secret") or "").strip(),
            profile=profile,
            timeout=float(payload.get("timeout") or 15.0),
            readonly=bool(payload.get("readonly", True)),
        )

    def with_overrides(self, **kw: Any) -> "ShoonyaConfig":
        payload = asdict(self)
        for key in ("user_id", "password", "vendor_code", "api_secret", "totp_secret", "profile"):
            if kw.get(key) is not None:
                payload[key] = kw[key]
        return ShoonyaConfig.from_mapping(payload)

    @property
    def environment(self) -> str:
        return PROFILE_ENVIRONMENTS.get(self.profile, "paper")

    @property
    def is_paper(self) -> bool:
        return self.environment == "paper"


_OVERRIDE_KEYS = ("user_id", "password", "vendor_code", "api_secret", "totp_secret", "profile")


def build_config(
    profile_config: Mapping[str, Any] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> "ShoonyaConfig":
    base = asdict(load_config())
    for key, value in dict(profile_config or {}).items():
        if value is not None:
            base[key] = value
    cfg = ShoonyaConfig.from_mapping(base)
    clean = {
        k: v for k, v in dict(overrides or {}).items()
        if k in _OVERRIDE_KEYS and v not in (None, "")
    }
    return cfg.with_overrides(**clean) if clean else cfg


def config_path() -> Path:
    return get_runtime_root() / CONFIG_FILENAME


def load_config() -> ShoonyaConfig:
    path = config_path()
    if not path.exists():
        return ShoonyaConfig()
    try:
        return ShoonyaConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ShoonyaConfigError(f"invalid Shoonya config at {path}: {exc}") from exc


def save_config(config: ShoonyaConfig) -> Path:
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


def shoonya_available() -> bool:
    try:
        _require_shoonya()
        return True
    except ShoonyaDependencyError:
        return False


# ---------------------------------------------------------------------------
# Five read operations + order placement
# ---------------------------------------------------------------------------


def check_status(config: ShoonyaConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    report: dict[str, Any] = {
        "status": "ok",
        "config": _public_config(cfg),
        "sdk": {"package": "NorenRestApiPy", "installed": shoonya_available()},
        "paper_guard": "simulated_locally",
        "host": SHOONYA_API_URL,
        "brokerage": "₹0 (zero) on all segments",
    }

    missing = _missing_fields(cfg)
    if missing:
        report["status"] = "error"
        report["error"] = f"Shoonya connector not configured: missing {', '.join(missing)}."
        return report

    if not report["sdk"]["installed"]:
        report["status"] = "error"
        report["error"] = (
            "Optional dependency missing: install with "
            "`pip install NorenRestApiPy` or from "
            "https://github.com/Shoonya-Dev/ShoonyaApi-py"
        )
        return report

    return report


def get_account_snapshot(config: ShoonyaConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    api = _login(cfg)
    limits = api.get_limits()

    if limits is None:
        return {"status": "error", "error": "Failed to fetch fund limits"}

    return {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "host": SHOONYA_API_URL,
        "brokerage": "₹0",
        "account": {
            "currency": "INR",
            "cash": limits.get("cash", "0"),
            "margin_available": limits.get("marginavailable", "0"),
            "margin_used": limits.get("marginused", "0"),
            "collateral": limits.get("collateral", "0"),
            "payin": limits.get("payin", "0"),
        },
    }


def get_positions(config: ShoonyaConfig | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    api = _login(cfg)
    positions = api.get_positions()

    rows = []
    for item in _as_list(positions):
        rows.append({
            "symbol": item.get("tsym", ""),
            "exchange": item.get("exch", ""),
            "product_type": item.get("prd", ""),
            "quantity": int(item.get("netqty", 0)),
            "average_cost": float(item.get("netavgprc", 0)),
            "ltp": float(item.get("lp", 0)),
            "unrealized_pnl": float(item.get("urmtom", 0)),
            "realized_pnl": float(item.get("rpnl", 0)),
            "day_buy_qty": int(item.get("daybuyqty", 0)),
            "day_sell_qty": int(item.get("daysellqty", 0)),
        })

    return {
        "status": "ok",
        "profile": cfg.profile,
        "is_paper": cfg.is_paper,
        "positions": rows,
    }


def get_open_orders(
    config: ShoonyaConfig | None = None,
    *,
    include_executions: bool = False,
) -> dict[str, Any]:
    cfg = config or load_config()
    api = _login(cfg)
    orders = api.get_order_book()

    open_orders = []
    executions = []
    for item in _as_list(orders):
        order_dict = _order_to_dict(item)
        status = str(item.get("status", "")).upper()
        if status in ("PENDING", "OPEN", "TRIGGER_PENDING"):
            open_orders.append(order_dict)
        elif include_executions and status in ("COMPLETE", "FILLED"):
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
    config: ShoonyaConfig | None = None,
    exchange: str = "NSE",
) -> dict[str, Any]:
    """Fetch quote for a symbol.

    Shoonya uses ``exchange:tradingsymbol`` format for quotes.
    """
    cfg = config or load_config()
    api = _login(cfg)

    clean = symbol.strip().upper()
    try:
        quote = api.get_quotes(exchange=exchange, token=clean)
    except Exception as exc:
        return {"status": "error", "error": str(exc), "symbol": clean}

    if quote is None:
        return {"status": "error", "error": "quote not found", "symbol": clean}

    return {
        "status": "ok",
        "symbol": clean,
        "exchange": exchange,
        "quote": {
            "ltp": float(quote.get("lp", 0)),
            "open": float(quote.get("o", 0)),
            "high": float(quote.get("h", 0)),
            "low": float(quote.get("l", 0)),
            "close": float(quote.get("c", 0)),
            "volume": int(quote.get("v", 0)),
            "bid": float(quote.get("bp1", 0)),
            "ask": float(quote.get("sp1", 0)),
        },
    }


def get_historical_bars(
    symbol: str,
    *,
    config: ShoonyaConfig | None = None,
    exchange: str = "NSE",
    period: str = "1d",
    limit: int = 90,
) -> dict[str, Any]:
    """Fetch historical OHLCV bars."""
    cfg = config or load_config()
    api = _login(cfg)

    clean = symbol.strip().upper()
    from datetime import datetime, timedelta

    end = datetime.now()
    if period in ("1m", "5m", "15m", "30m"):
        start = end - timedelta(days=5)
    else:
        start = end - timedelta(days=min(limit * 2, 365))

    interval_map = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "1d": "D"}
    interval = interval_map.get(period, "D")

    try:
        if interval == "D":
            data = api.get_daily_price_series(
                exchange=exchange,
                tradingsymbol=clean,
                startdate=start.timestamp(),
                enddate=end.timestamp(),
            )
        else:
            data = api.get_time_price_series(
                exchange=exchange,
                token=clean,
                starttime=start.timestamp(),
                endtime=end.timestamp(),
                interval=interval,
            )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "symbol": clean}

    bars = []
    for item in _as_list(data):
        bars.append({
            "time": item.get("time", item.get("ssboe", "")),
            "open": float(item.get("into", item.get("o", 0))),
            "high": float(item.get("inth", item.get("h", 0))),
            "low": float(item.get("intl", item.get("l", 0))),
            "close": float(item.get("intc", item.get("c", 0))),
            "volume": int(item.get("intv", item.get("v", 0))),
        })

    return {
        "status": "ok",
        "symbol": clean,
        "exchange": exchange,
        "period": period,
        "bars": bars[-limit:],
    }


def place_order(
    config: ShoonyaConfig | None = None,
    *,
    symbol: str,
    side: str,
    quantity: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    limit_price: float | None = None,
    time_in_force: str = "day",
    exchange: str = "NSE",
    product_type: str = "I",
) -> dict[str, Any]:
    """Place a PAPER-ONLY order on Shoonya (simulated locally).

    Shoonya exposes no runtime paper/live discriminator, so this connector is
    structurally capped at paper: the very first check refuses any config whose
    ``environment`` is not ``paper``. There is therefore no live order path
    here, by design. Paper orders are simulated locally — Shoonya has no sandbox.

    Args:
        symbol: Trading symbol.
        side: ``buy`` or ``sell``.
        quantity: Number of shares/lots.
        order_type: ``market`` or ``limit``.
        exchange: NSE, NFO, BSE, BFO, MCX, CDS.
        product_type: I (intraday), C (delivery/CNC), M (margin).
    """
    cfg = config or load_config()

    # ---- HARD GUARD: structurally paper-only (must run before anything) ----
    if not cfg.is_paper:
        return {"status": "error", "error": _PAPER_ONLY_ERROR}

    clean_symbol = str(symbol or "").strip().upper()
    if not clean_symbol:
        return {"status": "error", "error": "symbol is required"}

    side_token = str(side or "").strip().upper()
    side_map = {"BUY": "B", "SELL": "S", "B": "B", "S": "S"}
    if side_token not in side_map:
        return {"status": "error", "error": "side must be 'buy' or 'sell'"}
    buy_or_sell = side_map[side_token]

    type_map = {"MARKET": "MKT", "LIMIT": "LMT", "MKT": "MKT", "LMT": "LMT"}
    type_token = str(order_type or "").strip().upper()
    if type_token not in type_map:
        return {"status": "error", "error": "order_type must be 'market' or 'limit'"}
    price_type = type_map[type_token]

    if quantity is None or float(quantity) <= 0:
        return {"status": "error", "error": "quantity must be positive"}

    qty = int(float(quantity))
    price = float(limit_price) if limit_price is not None else 0.0

    if price_type == "LMT" and limit_price is None:
        return {"status": "error", "error": "limit order requires limit_price"}

    # Paper-only: simulate locally (Shoonya has no sandbox).
    return {
        "status": "ok",
        "order_id": f"PAPER-{clean_symbol}-{buy_or_sell}-{qty}",
        "symbol": clean_symbol,
        "side": side_token.lower(),
        "profile": cfg.profile,
        "is_paper": True,
        "paper_guard": "simulated_locally",
        "order_type": order_type.lower(),
        "quantity": qty,
        "limit_price": price if price_type == "LMT" else None,
        "order_status": "simulated_fill",
        "exchange": exchange,
        "product_type": product_type,
        "brokerage": "₹0",
    }


def cancel_order(
    config: ShoonyaConfig | None = None,
    order_id: str = "",
    *,
    symbol: str | None = None,
) -> dict[str, Any]:
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

#: Authenticated NorenApi sessions keyed by login identity (``user_id``), so a
#: second account's reads never reuse the first account's session.
_api_cache: dict[str, Any] = {}


def _require_shoonya() -> ModuleType:
    try:
        import NorenRestApiPy.NorenApi as NorenApi  # type: ignore
    except ModuleNotFoundError as exc:
        raise ShoonyaDependencyError(
            "NorenRestApiPy is not installed; run "
            "`pip install NorenRestApiPy` or install from "
            "https://github.com/Shoonya-Dev/ShoonyaApi-py"
        ) from exc
    return NorenApi


def _login(cfg: ShoonyaConfig):
    """Login to Shoonya API with TOTP authentication.

    Sessions are cached per ``user_id`` so distinct accounts never share an
    authenticated client.
    """
    missing = _missing_fields(cfg)
    if missing:
        raise ShoonyaConfigError(
            f"Shoonya connector not configured: missing {', '.join(missing)}. "
            "Set them in ~/.vibe-trading/shoonya.json"
        )

    cached = _api_cache.get(cfg.user_id)
    if cached is not None:
        return cached

    NorenApi = _require_shoonya()

    try:
        import pyotp
    except ModuleNotFoundError as exc:
        raise ShoonyaDependencyError(
            "pyotp is not installed (required for Shoonya TOTP login); run "
            "`pip install pyotp`."
        ) from exc

    class ShoonyaApi(NorenApi.NorenApi):
        def __init__(self):
            super().__init__(
                host=SHOONYA_API_URL,
                websocket="wss://api.shoonya.com/NorenWSTP/",
            )

    api = ShoonyaApi()

    totp = pyotp.TOTP(cfg.totp_secret).now()

    ret = api.login(
        userid=cfg.user_id,
        password=cfg.password,
        twoFA=totp,
        vendor_code=cfg.vendor_code,
        api_secret=cfg.api_secret,
        imei="vibe-trading",
    )

    if ret is None or ret.get("stat") != "Ok":
        error_msg = ret.get("emsg", "Login failed") if ret else "Login returned None"
        raise ShoonyaConfigError(f"Shoonya login failed: {error_msg}")

    _api_cache[cfg.user_id] = api
    return api


def _missing_fields(cfg: ShoonyaConfig) -> list[str]:
    missing = []
    for field in ("user_id", "password", "vendor_code", "api_secret", "totp_secret"):
        if not getattr(cfg, field):
            missing.append(field)
    return missing


def _public_config(cfg: ShoonyaConfig) -> dict[str, Any]:
    data = asdict(cfg)
    for secret in ("password", "api_secret", "totp_secret"):
        if data.get(secret):
            data[secret] = "***redacted***"
    if data.get("user_id"):
        data["user_id"] = data["user_id"][:2] + "***"
    return data


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _order_to_dict(item: Any) -> dict[str, Any]:
    return {
        "order_id": str(item.get("norenordno", "")),
        "symbol": item.get("tsym", ""),
        "exchange": item.get("exch", ""),
        "side": "buy" if item.get("trantype") == "B" else "sell",
        "order_type": item.get("prctyp", "").lower(),
        "quantity": int(item.get("qty", 0)),
        "filled_qty": int(item.get("fillshares", 0)),
        "price": float(item.get("prc", 0)),
        "status": item.get("status", ""),
        "product_type": item.get("prd", ""),
    }
