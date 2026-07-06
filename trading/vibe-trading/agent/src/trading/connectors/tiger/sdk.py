"""Read-only Tiger Brokers (TigerOpen) connector via the official ``tigeropen`` SDK.

This module wraps Tiger's ``QuoteClient`` / ``TradeClient`` for the five read
operations the trading layer exposes (account / positions / orders / quote /
history). It holds no order-placement method — writes are introduced in a later
layer behind the paper guard and, for live, the mandate gate.

Auth is RSA-signed static-key (``tiger_id`` + a local PKCS#1 private key +
account number); no OAuth, no token refresh. Credentials never leave the user's
machine: the private key is read from a local path the operator configures.

Paper-vs-live identity guard (the documented Tiger discriminator): a paper
account number is 17 digits, all numeric (e.g. ``20191106192858300``); a
standard/prime account is 5–10 digits; a global account starts with ``U``. The
``paper`` profile fails closed unless the configured account matches the
17-digit paper format, so a live account can never be driven under a paper
profile by mistake.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from src.config.paths import get_runtime_root

CONFIG_FILENAME = "tiger.json"

#: Profiles this connector understands and their default account environment.
PROFILE_ENVIRONMENTS = {
    "paper": "paper",
    "live-readonly": "live",
    "live": "live",
}

#: A Tiger paper account number is exactly 17 numeric digits.
_PAPER_ACCOUNT_RE = re.compile(r"^\d{17}$")


class TigerDependencyError(RuntimeError):
    """Raised when the optional ``tigeropen`` package is not installed."""


class TigerConfigError(RuntimeError):
    """Raised when the connector configuration is missing or invalid."""


class TigerProfileMismatchError(RuntimeError):
    """Raised when a profile's account does not match its declared environment."""


def is_paper_account(account: str | None) -> bool:
    """Return whether an account number is a Tiger paper account (17 digits)."""
    return bool(account) and bool(_PAPER_ACCOUNT_RE.match(account.strip()))


@dataclass(frozen=True)
class TigerConfig:
    """Tiger connector connection settings.

    Args:
        tiger_id: Developer ``tiger_id`` issued by the Tiger open platform.
        private_key_path: Path to the local PKCS#1 RSA private key (PEM).
        account: Tiger account number. A 17-digit number is a paper account.
        profile: ``paper``, ``live-readonly`` or ``live``.
        timeout: Network timeout in seconds.
        readonly: Always true for this layer; order methods are not exposed.
    """

    tiger_id: str = ""
    private_key_path: str = ""
    account: str = ""
    profile: str = "paper"
    timeout: float = 15.0
    readonly: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "TigerConfig":
        """Build a config from a JSON-like mapping, normalizing the profile."""
        payload = dict(data or {})
        profile = str(payload.get("profile") or "paper").strip().lower()
        if profile not in PROFILE_ENVIRONMENTS:
            raise TigerConfigError("profile must be 'paper', 'live-readonly' or 'live'")
        return cls(
            tiger_id=str(payload.get("tiger_id") or "").strip(),
            private_key_path=str(payload.get("private_key_path") or "").strip(),
            account=str(payload.get("account") or "").strip(),
            profile=profile,
            timeout=float(payload.get("timeout") or 15.0),
            readonly=bool(payload.get("readonly", True)),
        )

    def with_overrides(
        self,
        *,
        tiger_id: str | None = None,
        private_key_path: str | None = None,
        account: str | None = None,
        profile: str | None = None,
    ) -> "TigerConfig":
        """Return a copy with CLI/tool overrides applied."""
        payload = asdict(self)
        if tiger_id is not None:
            payload["tiger_id"] = tiger_id
        if private_key_path is not None:
            payload["private_key_path"] = private_key_path
        if account is not None:
            payload["account"] = account
        if profile is not None:
            payload["profile"] = profile
        return TigerConfig.from_mapping(payload)

    @property
    def environment(self) -> str:
        """Return ``paper`` or ``live`` for this profile."""
        return PROFILE_ENVIRONMENTS.get(self.profile, "paper")


_OVERRIDE_KEYS = ("tiger_id", "private_key_path", "account", "profile")


def build_config(profile_config: Mapping[str, Any] | None = None, overrides: Mapping[str, Any] | None = None) -> "TigerConfig":
    """Resolve the effective config: saved file ← profile defaults ← CLI overrides.

    Credentials (``tiger_id`` / ``private_key_path`` / ``account``) come from the
    saved ``~/.vibe-trading/tiger.json``; the selected connector profile supplies
    the ``profile`` intent; CLI/tool overrides win last.

    Args:
        profile_config: The connector profile's ``config`` dict.
        overrides: Per-call overrides (only known config keys are applied).

    Returns:
        A normalized :class:`TigerConfig`.
    """
    base = asdict(load_config())
    for key, value in dict(profile_config or {}).items():
        if value is not None:
            base[key] = value
    cfg = TigerConfig.from_mapping(base)
    clean = {k: v for k, v in dict(overrides or {}).items() if k in _OVERRIDE_KEYS and v not in (None, "")}
    return cfg.with_overrides(**clean) if clean else cfg


def config_path() -> Path:
    """Return the user-level Tiger config path."""
    return get_runtime_root() / CONFIG_FILENAME


def load_config() -> TigerConfig:
    """Load Tiger settings from ``~/.vibe-trading/tiger.json``."""
    path = config_path()
    if not path.exists():
        return TigerConfig()
    try:
        return TigerConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise TigerConfigError(f"invalid Tiger config at {path}: {exc}") from exc


def save_config(config: TigerConfig) -> Path:
    """Persist Tiger settings with owner-only permissions."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def tigeropen_available() -> bool:
    """Return whether the optional ``tigeropen`` SDK can be imported."""
    try:
        _require_tigeropen()
        return True
    except TigerDependencyError:
        return False


def check_status(config: TigerConfig | None = None) -> dict[str, Any]:
    """Check SDK readiness, config completeness, and account identity.

    Returns a JSON-serializable health report. Does not place or mutate any
    broker state.
    """
    cfg = config or load_config()
    report: dict[str, Any] = {
        "status": "ok",
        "config": _public_config(cfg),
        "sdk": {"package": "tigeropen", "installed": tigeropen_available()},
    }

    missing = _missing_fields(cfg)
    if missing:
        report["status"] = "error"
        report["error"] = f"Tiger connector not configured: missing {', '.join(missing)}."
        return report

    if not report["sdk"]["installed"]:
        report["status"] = "error"
        report["error"] = "Optional dependency missing: install with `pip install tigeropen`."
        return report

    try:
        _assert_profile(cfg)
    except (TigerProfileMismatchError, TigerConfigError) as exc:
        report["status"] = "error"
        report["error"] = str(exc)
        return report

    try:
        snapshot = get_account_snapshot(cfg)
    except Exception as exc:  # noqa: BLE001 - health endpoint reports cleanly
        report["status"] = "error"
        report["error"] = str(exc)
        return report

    report["account"] = {
        "account": cfg.account,
        "is_paper": is_paper_account(cfg.account),
        "profile": cfg.profile,
        "assets_currency": [row.get("currency") for row in snapshot.get("assets", [])],
    }
    return report


def get_account_snapshot(config: TigerConfig | None = None) -> dict[str, Any]:
    """Fetch account assets / balance for the configured account."""
    cfg = config or load_config()
    _assert_profile(cfg)
    trade = _trade_client(cfg)
    assets = _safe_call(trade, "get_assets", account=cfg.account) or _safe_call(trade, "get_assets")
    rows = [_asset_to_dict(item) for item in _as_iter(assets)]
    return {
        "status": "ok",
        "profile": cfg.profile,
        "account": cfg.account,
        "is_paper": is_paper_account(cfg.account),
        "assets": rows,
    }


def get_positions(config: TigerConfig | None = None) -> dict[str, Any]:
    """Fetch current positions for the configured account."""
    cfg = config or load_config()
    _assert_profile(cfg)
    trade = _trade_client(cfg)
    positions = _safe_call(trade, "get_positions", account=cfg.account) or _safe_call(trade, "get_positions")
    rows = [_position_to_dict(item) for item in _as_iter(positions)]
    return {"status": "ok", "profile": cfg.profile, "account": cfg.account, "positions": rows}


def get_open_orders(config: TigerConfig | None = None, *, include_executions: bool = False) -> dict[str, Any]:
    """Fetch open orders and, optionally, recently filled orders."""
    cfg = config or load_config()
    _assert_profile(cfg)
    trade = _trade_client(cfg)
    open_orders = _safe_call(trade, "get_open_orders", account=cfg.account) or _safe_call(trade, "get_open_orders")
    result: dict[str, Any] = {
        "status": "ok",
        "profile": cfg.profile,
        "account": cfg.account,
        "open_orders": [_order_to_dict(item) for item in _as_iter(open_orders)],
    }
    if include_executions:
        filled = _safe_call(trade, "get_filled_orders", account=cfg.account) or _safe_call(trade, "get_filled_orders")
        result["executions"] = [_order_to_dict(item) for item in _as_iter(filled)]
    return result


def get_quote(symbol: str, *, config: TigerConfig | None = None, **_: Any) -> dict[str, Any]:
    """Fetch a top-of-book quote snapshot for ``symbol``."""
    cfg = config or load_config()
    _assert_profile(cfg)
    quote = _quote_client(cfg)
    clean = symbol.strip().upper()
    briefs = _safe_call(quote, "get_stock_briefs", [clean])
    rows = [_quote_to_dict(item) for item in _as_iter(briefs)]
    payload = rows[0] if rows else {}
    return {"status": "ok", "symbol": clean, "quote": payload}


#: Canonical period token → Tiger ``get_bars`` period string.
_PERIOD_MAP = {
    "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "60min", "4h": "60min", "1d": "day", "1w": "week", "1M": "month",
}


def get_historical_bars(
    symbol: str,
    *,
    config: TigerConfig | None = None,
    period: str = "1d",
    limit: int = 90,
    **_: Any,
) -> dict[str, Any]:
    """Fetch historical OHLCV bars for ``symbol`` (``period`` is a canonical token)."""
    cfg = config or load_config()
    _assert_profile(cfg)
    quote = _quote_client(cfg)
    clean = symbol.strip().upper()
    # Case-sensitive: ``1m`` (minute) must not collide with ``1M`` (month).
    tiger_period = _PERIOD_MAP.get(period.strip(), "day")
    bars = _safe_call(quote, "get_bars", [clean], period=tiger_period, limit=int(limit))
    return {
        "status": "ok",
        "symbol": clean,
        "period": period,
        "bars": [_bar_to_dict(item) for item in _as_iter(bars)],
    }


# ---------------------------------------------------------------------------
# Order placement (Layer B/C) — fails closed, never raises
# ---------------------------------------------------------------------------

#: Accepted ``side`` tokens → Tiger ``action`` (uppercase).
_ACTION_MAP = {"buy": "BUY", "sell": "SELL"}

#: Accepted ``time_in_force`` tokens → Tiger TIF string.
_TIF_MAP = {"day": "DAY", "gtc": "GTC"}


def place_order(
    config: TigerConfig,
    *,
    symbol: str,
    side: str,
    quantity: float | None = None,
    notional: float | None = None,
    order_type: str = "market",
    limit_price: float | None = None,
    time_in_force: str = "day",
) -> dict[str, Any]:
    """Place a stock order against the account in ``config``.

    This executes a REAL order against whatever account ``config`` points at: a
    paper config drives the Tiger paper (sandbox) account, a live config drives
    the live account. The connector only executes; authorization (mandate gate,
    kill switch) is the caller's responsibility. ``_assert_profile`` runs first
    so a live account can never be driven under a paper profile by mistake.

    Args:
        config: Resolved :class:`TigerConfig`. Its ``profile`` selects the
            account environment (paper account = sandbox order).
        symbol: Stock symbol, e.g. ``AAPL``.
        side: ``buy`` or ``sell`` (case-insensitive).
        quantity: Order size in units. Provide exactly one of ``quantity`` or
            ``notional``.
        notional: Notional amount. Tiger has no notional path for stocks, so a
            notional-only request fails closed with a clear error.
        order_type: ``market`` or ``limit`` (a ``limit`` order requires
            ``limit_price``).
        limit_price: Limit price; required for and only used by limit orders.
        time_in_force: ``day`` or ``gtc``. Paper accounts do not support GTC, so
            it is forced to DAY when ``config`` is a paper profile.

    Returns:
        ``{"status": "ok", "order_id": str, "symbol", "side", "profile", ...}``
        on success, otherwise ``{"status": "error", "error": str}``. Never
        raises: all failure modes are reported in the envelope.
    """
    # ---- input validation (fail closed before touching the SDK) ----
    side_key = str(side or "").strip().lower()
    action = _ACTION_MAP.get(side_key)
    if action is None:
        return {"status": "error", "error": "side must be 'buy' or 'sell'"}

    if (quantity is None) == (notional is None):
        return {"status": "error", "error": "provide exactly one of quantity or notional"}
    if notional is not None:
        return {"status": "error", "error": "Tiger requires quantity (units), not notional"}

    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        return {"status": "error", "error": "quantity must be a number"}
    if qty <= 0:
        return {"status": "error", "error": "quantity must be positive"}

    type_key = str(order_type or "").strip().lower()
    if type_key not in ("market", "limit"):
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
    tif = _TIF_MAP.get(tif_key)
    if tif is None:
        return {"status": "error", "error": "time_in_force must be 'day' or 'gtc'"}

    clean_symbol = str(symbol or "").strip().upper()
    if not clean_symbol:
        return {"status": "error", "error": "symbol is required"}

    # ---- profile / environment guard ----
    try:
        _assert_profile(config)
    except (TigerProfileMismatchError, TigerConfigError) as exc:
        return {"status": "error", "error": str(exc)}

    # Paper accounts do not support GTC; force DAY rather than failing the order.
    paper = is_paper_account(config.account)
    if paper and tif == "GTC":
        tif = "DAY"

    # ---- build + submit ----
    try:
        from tigeropen.common.util.contract_utils import stock_contract  # type: ignore
        from tigeropen.common.util.order_utils import limit_order, market_order  # type: ignore
    except ModuleNotFoundError as exc:
        return {"status": "error", "error": f"tigeropen is not installed; run `pip install tigeropen` ({exc})"}

    try:
        trade = _trade_client(config)
        contract = stock_contract(symbol=clean_symbol, currency="USD")
        if type_key == "limit":
            order = limit_order(
                account=config.account,
                contract=contract,
                action=action,
                quantity=qty,
                limit_price=px,
                time_in_force=tif,
            )
        else:
            order = market_order(
                account=config.account,
                contract=contract,
                action=action,
                quantity=qty,
                time_in_force=tif,
            )
        # ``place_order`` mutates ``order.id`` with the global id and returns it;
        # read both defensively in case the SDK only does one.
        returned = trade.place_order(order)
        order_id = _obj_get(order, "id", None)
        if order_id is None:
            order_id = returned
    except Exception as exc:  # noqa: BLE001 - fail closed, never raise to caller
        return {"status": "error", "error": str(exc)}

    if order_id is None:
        return {"status": "error", "error": "Tiger did not return an order id"}

    # Best-effort rejection check: tigeropen mutates the order object with a
    # status/reason. A rejected order can still come back with an id, so don't
    # report success when the broker flagged it rejected.
    order_status = str(_obj_get(order, "status", "") or "")
    reason = _obj_get(order, "reason", None)
    if order_status.strip().lower() in ("rejected", "inactive") or (reason and str(reason).strip()):
        return {
            "status": "error",
            "error": f"Tiger rejected order: {reason or order_status}",
            "order_id": str(order_id),
            "symbol": clean_symbol,
        }

    return {
        "status": "ok",
        "order_id": str(order_id),
        "symbol": clean_symbol,
        "side": side_key,
        "profile": config.profile,
        "account": config.account,
        "is_paper": paper,
        "order_type": type_key,
        "quantity": qty,
        "limit_price": px,
        "time_in_force": tif,
    }


def cancel_order(config: TigerConfig, order_id: Any, *, symbol: str | None = None) -> dict[str, Any]:
    """Cancel a previously placed order on the account in ``config``.

    Runs ``_assert_profile`` first so the cancel targets the intended account
    environment. Like :func:`place_order`, this never raises: every failure is
    returned in the envelope.

    Args:
        config: Resolved :class:`TigerConfig` selecting the account.
        order_id: The global order id returned by :func:`place_order`.
        symbol: Optional symbol, echoed back for caller convenience; Tiger
            cancels by id and does not require it.

    Returns:
        ``{"status": "ok", "order_id": str, "profile", ...}`` on success,
        otherwise ``{"status": "error", "error": str}``.
    """
    if order_id is None or str(order_id).strip() == "":
        return {"status": "error", "error": "order_id is required"}

    try:
        _assert_profile(config)
    except (TigerProfileMismatchError, TigerConfigError) as exc:
        return {"status": "error", "error": str(exc)}

    try:
        oid: Any = int(order_id)
    except (TypeError, ValueError):
        oid = order_id

    try:
        trade = _trade_client(config)
        # SDK accepts ``id=``; older builds use ``order_id=`` — try the canonical
        # keyword first and fall back so a signature drift still cancels.
        try:
            trade.cancel_order(id=oid)
        except TypeError:
            trade.cancel_order(order_id=oid)
    except Exception as exc:  # noqa: BLE001 - fail closed, never raise to caller
        return {"status": "error", "error": str(exc)}

    result: dict[str, Any] = {
        "status": "ok",
        "order_id": str(order_id),
        "profile": config.profile,
        "account": config.account,
    }
    if symbol:
        result["symbol"] = str(symbol).strip().upper()
    return result


# ---------------------------------------------------------------------------
# SDK plumbing
# ---------------------------------------------------------------------------


def _require_tigeropen() -> ModuleType:
    try:
        import tigeropen  # type: ignore
    except ModuleNotFoundError as exc:
        raise TigerDependencyError("tigeropen is not installed; run `pip install tigeropen`.") from exc
    return tigeropen


def _client_config(cfg: TigerConfig):
    """Build a ``TigerOpenClientConfig`` from connector settings."""
    _require_tigeropen()
    from tigeropen.common.util.signature_utils import read_private_key  # type: ignore
    from tigeropen.tiger_open_config import TigerOpenClientConfig  # type: ignore

    key_path = Path(cfg.private_key_path).expanduser()
    if not key_path.exists():
        raise TigerConfigError(f"Tiger private key not found at {key_path}")
    client_config = TigerOpenClientConfig()
    client_config.private_key = read_private_key(str(key_path))
    client_config.tiger_id = cfg.tiger_id
    client_config.account = cfg.account
    try:
        client_config.timeout = cfg.timeout
    except Exception:  # noqa: BLE001 - older SDKs may not expose timeout
        pass
    return client_config


def _trade_client(cfg: TigerConfig):
    _require_tigeropen()
    from tigeropen.trade.trade_client import TradeClient  # type: ignore

    return TradeClient(_client_config(cfg))


def _quote_client(cfg: TigerConfig):
    _require_tigeropen()
    from tigeropen.quote.quote_client import QuoteClient  # type: ignore

    return QuoteClient(_client_config(cfg))


def _assert_profile(cfg: TigerConfig) -> None:
    """Fail closed when the account does not match the declared environment."""
    account = (cfg.account or "").strip()
    if not account:
        raise TigerConfigError("Tiger account number is not configured")
    paper = is_paper_account(account)
    if cfg.environment == "paper" and not paper:
        raise TigerProfileMismatchError(
            "Configured profile is paper, but the account number is not a 17-digit Tiger paper account. "
            "Use a live profile only if you intend live-account access."
        )
    if cfg.environment == "live" and paper:
        raise TigerProfileMismatchError(
            "Configured profile is live, but the account number is a 17-digit Tiger paper account. "
            "Select a paper profile for paper accounts."
        )


def _missing_fields(cfg: TigerConfig) -> list[str]:
    missing = []
    if not cfg.tiger_id:
        missing.append("tiger_id")
    if not cfg.private_key_path:
        missing.append("private_key_path")
    if not cfg.account:
        missing.append("account")
    return missing


def _public_config(cfg: TigerConfig) -> dict[str, Any]:
    """Config snapshot with credential material masked (key path only, never contents)."""
    data = asdict(cfg)
    if data.get("tiger_id"):
        data["tiger_id"] = data["tiger_id"][:4] + "***"
    return data


# ---------------------------------------------------------------------------
# Defensive field extraction (SDK returns objects or dicts depending on version)
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


def _asset_to_dict(item: Any) -> dict[str, Any]:
    return {
        "currency": _first(item, ("currency",)),
        "cash": _first(item, ("cash", "cash_balance")),
        "net_liquidation": _first(item, ("net_liquidation", "net_liquidation_value")),
        "buying_power": _first(item, ("buying_power",)),
        "equity_with_loan": _first(item, ("equity_with_loan", "equity_with_loan_value")),
        "unrealized_pnl": _first(item, ("unrealized_pnl", "unrealized_pl")),
    }


def _position_to_dict(item: Any) -> dict[str, Any]:
    contract = _obj_get(item, "contract")
    return {
        "symbol": _first(contract, ("symbol",)) or _first(item, ("symbol",)),
        "currency": _first(contract, ("currency",)) or _first(item, ("currency",)),
        "sec_type": _first(contract, ("sec_type", "secType")),
        "quantity": _first(item, ("quantity", "position_qty", "position")),
        "average_cost": _first(item, ("average_cost", "avg_cost")),
        "market_value": _first(item, ("market_value",)),
        "unrealized_pnl": _first(item, ("unrealized_pnl", "unrealized_pl")),
    }


def _order_to_dict(item: Any) -> dict[str, Any]:
    contract = _obj_get(item, "contract")
    return {
        "order_id": _first(item, ("id", "order_id")),
        "symbol": _first(contract, ("symbol",)) or _first(item, ("symbol",)),
        "action": _first(item, ("action",)),
        "order_type": _first(item, ("order_type", "type")),
        "quantity": _first(item, ("quantity",)),
        "filled": _first(item, ("filled",)),
        "remaining": _first(item, ("remaining",)),
        "avg_fill_price": _first(item, ("avg_fill_price",)),
        "limit_price": _first(item, ("limit_price",)),
        "status": str(_first(item, ("status",)) or ""),
        "currency": _first(contract, ("currency",)),
    }


def _quote_to_dict(item: Any) -> dict[str, Any]:
    return {
        "symbol": _first(item, ("symbol",)),
        "last": _first(item, ("latest_price", "last_price", "latest")),
        "bid": _first(item, ("bid_price", "bid")),
        "ask": _first(item, ("ask_price", "ask")),
        "open": _first(item, ("open",)),
        "high": _first(item, ("high",)),
        "low": _first(item, ("low",)),
        "prev_close": _first(item, ("pre_close", "prev_close")),
        "volume": _first(item, ("volume",)),
        "time": str(_first(item, ("latest_time", "time"), "")),
    }


def _bar_to_dict(item: Any) -> dict[str, Any]:
    return {
        "time": str(_first(item, ("time", "date"), "")),
        "open": _first(item, ("open",)),
        "high": _first(item, ("high",)),
        "low": _first(item, ("low",)),
        "close": _first(item, ("close",)),
        "volume": _first(item, ("volume",)),
    }


def _safe_call(obj: Any, name: str, *args: Any, **kwargs: Any) -> Any:
    """Call ``obj.name(*args, **kwargs)`` if it exists, retrying without kwargs.

    Tiger SDK signatures vary across versions (some read methods take an
    ``account`` kwarg, some bind it from the client config). We try the richer
    call first and fall back to the no-arg form so a signature drift degrades to
    a usable call instead of an error.
    """
    fn = getattr(obj, name, None)
    if fn is None:
        return None
    try:
        return fn(*args, **kwargs)
    except TypeError:
        try:
            return fn(*args)
        except TypeError:
            return fn()
