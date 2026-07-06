"""Local read-only Interactive Brokers connector via TWS / IB Gateway.

This module intentionally connects only to a user-owned local TWS or IB Gateway
session. It does not handle IBKR credentials, does not talk to cloud broker
endpoints directly, and exposes no order-placement method.
"""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping

from src.config.paths import get_runtime_root

CONFIG_FILENAME = "ibkr-local.json"

DEFAULT_ENDPOINTS: tuple[dict[str, Any], ...] = (
    {"profile": "paper", "label": "TWS Paper", "host": "127.0.0.1", "port": 7497},
    {"profile": "paper", "label": "IB Gateway Paper", "host": "127.0.0.1", "port": 4002},
    {"profile": "live-readonly", "label": "TWS Live", "host": "127.0.0.1", "port": 7496},
    {"profile": "live-readonly", "label": "IB Gateway Live", "host": "127.0.0.1", "port": 4001},
)

PROFILE_DEFAULT_PORTS = {
    "paper": 7497,
    "live-readonly": 7496,
}


class IBKRDependencyError(RuntimeError):
    """Raised when the optional ``ib_async`` package is not installed."""


class IBKRConnectionError(RuntimeError):
    """Raised when a local TWS / IB Gateway connection cannot be established."""


class IBKRProfileMismatchError(RuntimeError):
    """Raised when a paper profile appears to be connected to a live account."""


@dataclass(frozen=True)
class IBKRLocalConfig:
    """Local TWS / IB Gateway connection settings.

    Args:
        host: Local host where TWS / IB Gateway listens.
        port: Socket API port. TWS paper defaults to 7497.
        client_id: TWS API client id.
        profile: ``paper`` or ``live-readonly``.
        account: Optional account code to filter requests.
        timeout: Connection timeout in seconds.
        readonly: Always passed as true when the SDK supports it.
    """

    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 77
    profile: str = "paper"
    account: str | None = None
    timeout: float = 8.0
    readonly: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "IBKRLocalConfig":
        """Build a config from a JSON-like mapping.

        Args:
            data: Mapping with any subset of config fields.

        Returns:
            A normalized config.
        """
        payload = dict(data or {})
        profile = str(payload.get("profile") or "paper").strip().lower()
        if profile not in PROFILE_DEFAULT_PORTS:
            raise ValueError("profile must be 'paper' or 'live-readonly'")
        default_port = PROFILE_DEFAULT_PORTS[profile]
        return cls(
            host=str(payload.get("host") or "127.0.0.1").strip(),
            port=int(payload.get("port") or default_port),
            client_id=int(payload.get("client_id", payload.get("clientId", 77))),
            profile=profile,
            account=_clean_optional_str(payload.get("account")),
            timeout=float(payload.get("timeout") or 8.0),
            readonly=bool(payload.get("readonly", True)),
        )

    def with_overrides(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        client_id: int | None = None,
        profile: str | None = None,
        account: str | None = None,
    ) -> "IBKRLocalConfig":
        """Return a copy with CLI/tool overrides applied."""
        payload = asdict(self)
        if profile is not None:
            payload["profile"] = profile
            if port is None:
                payload["port"] = PROFILE_DEFAULT_PORTS[profile]
        if host is not None:
            payload["host"] = host
        if port is not None:
            payload["port"] = port
        if client_id is not None:
            payload["client_id"] = client_id
        if account is not None:
            payload["account"] = account
        return IBKRLocalConfig.from_mapping(payload)


def config_path() -> Path:
    """Return the user-level IBKR local config path."""
    return get_runtime_root() / CONFIG_FILENAME


def load_config() -> IBKRLocalConfig:
    """Load local IBKR settings from ``~/.vibe-trading/ibkr-local.json``."""
    path = config_path()
    if not path.exists():
        return IBKRLocalConfig()
    try:
        return IBKRLocalConfig.from_mapping(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid IBKR local config at {path}: {exc}") from exc


def save_config(config: IBKRLocalConfig) -> Path:
    """Persist local IBKR settings.

    Args:
        config: Settings to write.

    Returns:
        The config path.
    """
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def ib_async_available() -> bool:
    """Return whether the optional ``ib_async`` SDK can be imported."""
    try:
        _require_ib_async()
        return True
    except IBKRDependencyError:
        return False


def check_local_status(
    config: IBKRLocalConfig | None = None,
    *,
    scan: bool = True,
) -> dict[str, Any]:
    """Check local port and SDK readiness.

    Args:
        config: Optional target config.
        scan: Whether to scan the default local ports.

    Returns:
        JSON-serializable health report.
    """
    cfg = config or load_config()
    report: dict[str, Any] = {
        "status": "ok",
        "config": asdict(cfg),
        "sdk": {"package": "ib_async", "installed": ib_async_available()},
    }
    if scan:
        report["ports"] = scan_default_ports()

    target_open = tcp_port_open(cfg.host, cfg.port)
    report["target"] = {
        "host": cfg.host,
        "port": cfg.port,
        "open": target_open,
    }
    if not target_open:
        report["status"] = "error"
        report["error"] = (
            f"No TWS / IB Gateway socket is listening at {cfg.host}:{cfg.port}. "
            "Open TWS or IB Gateway, log in, and enable API socket clients."
        )
        return report

    if not report["sdk"]["installed"]:
        report["status"] = "error"
        report["error"] = "Optional dependency missing: install with `pip install ib_async>=2.0`."
        return report

    try:
        account = get_account_snapshot(config=cfg)
    except Exception as exc:  # noqa: BLE001 - health endpoint should report cleanly
        report["status"] = "error"
        report["error"] = str(exc)
        return report

    report["account"] = {
        "accounts": account.get("accounts", []),
        "profile": cfg.profile,
    }
    return report


def scan_default_ports(timeout: float = 0.35) -> list[dict[str, Any]]:
    """Scan the standard local IBKR socket ports."""
    return [
        {
            **endpoint,
            "open": tcp_port_open(str(endpoint["host"]), int(endpoint["port"]), timeout=timeout),
        }
        for endpoint in DEFAULT_ENDPOINTS
    ]


def tcp_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return whether a TCP socket accepts connections."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def get_account_snapshot(config: IBKRLocalConfig | None = None) -> dict[str, Any]:
    """Fetch account codes and account summary values."""
    cfg = config or load_config()
    ib = _connect(cfg)
    try:
        accounts = _managed_accounts(ib)
        summary = [_account_value_to_dict(item) for item in _account_summary(ib, cfg.account)]
        accounts = sorted(set(accounts) | {str(item.get("account")) for item in summary if item.get("account")})
        _assert_profile(cfg, accounts)
        return {
            "status": "ok",
            "profile": cfg.profile,
            "accounts": accounts,
            "summary": summary,
        }
    finally:
        _disconnect(ib)


def get_positions(config: IBKRLocalConfig | None = None) -> dict[str, Any]:
    """Fetch current IBKR positions."""
    cfg = config or load_config()
    ib = _connect(cfg)
    try:
        accounts = _managed_accounts(ib)
        _assert_profile(cfg, accounts)
        rows = []
        for item in _call(ib, "positions"):
            account = str(_obj_get(item, "account", ""))
            if cfg.account and account and account != cfg.account:
                continue
            contract = _obj_get(item, "contract")
            rows.append(
                {
                    "account": account,
                    "symbol": _obj_get(contract, "symbol"),
                    "local_symbol": _obj_get(contract, "localSymbol"),
                    "sec_type": _obj_get(contract, "secType"),
                    "exchange": _obj_get(contract, "exchange"),
                    "currency": _obj_get(contract, "currency"),
                    "con_id": _obj_get(contract, "conId"),
                    "position": _obj_get(item, "position"),
                    "avg_cost": _obj_get(item, "avgCost"),
                }
            )
        return {"status": "ok", "profile": cfg.profile, "positions": rows}
    finally:
        _disconnect(ib)


def get_open_orders(config: IBKRLocalConfig | None = None, *, include_executions: bool = False) -> dict[str, Any]:
    """Fetch open orders and optionally recent executions."""
    cfg = config or load_config()
    ib = _connect(cfg)
    try:
        accounts = _managed_accounts(ib)
        _assert_profile(cfg, accounts)
        trades = _safe_call(ib, "openTrades") or []
        orders = [_trade_to_dict(trade) for trade in trades]
        if not orders:
            orders = [_order_to_dict(order) for order in (_safe_call(ib, "openOrders") or [])]
        result: dict[str, Any] = {"status": "ok", "profile": cfg.profile, "open_orders": orders}
        if include_executions:
            result["executions"] = [_execution_to_dict(item) for item in _executions(ib)]
        return result
    finally:
        _disconnect(ib)


def get_quote(
    symbol: str,
    *,
    config: IBKRLocalConfig | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
) -> dict[str, Any]:
    """Fetch a top-of-book quote snapshot."""
    cfg = config or load_config()
    ib = _connect(cfg)
    try:
        accounts = _managed_accounts(ib)
        _assert_profile(cfg, accounts)
        contract = _make_contract(symbol, exchange=exchange, currency=currency, sec_type=sec_type)
        _qualify_contract(ib, contract)
        ticker = ib.reqMktData(contract, "", False, False)
        _sleep(ib, 2.0)
        try:
            ib.cancelMktData(contract)
        except Exception:
            pass
        return {
            "status": "ok",
            "symbol": symbol.upper(),
            "exchange": exchange,
            "currency": currency,
            "quote": {
                "bid": _obj_get(ticker, "bid"),
                "ask": _obj_get(ticker, "ask"),
                "last": _obj_get(ticker, "last"),
                "close": _obj_get(ticker, "close"),
                "volume": _obj_get(ticker, "volume"),
                "time": str(_obj_get(ticker, "time", "")),
            },
        }
    finally:
        _disconnect(ib)


def get_historical_bars(
    symbol: str,
    *,
    config: IBKRLocalConfig | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    sec_type: str = "STK",
    duration: str = "30 D",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
) -> dict[str, Any]:
    """Fetch historical bars from local TWS / IB Gateway."""
    cfg = config or load_config()
    ib = _connect(cfg)
    try:
        accounts = _managed_accounts(ib)
        _assert_profile(cfg, accounts)
        contract = _make_contract(symbol, exchange=exchange, currency=currency, sec_type=sec_type)
        _qualify_contract(ib, contract)
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1,
        )
        return {
            "status": "ok",
            "symbol": symbol.upper(),
            "duration": duration,
            "bar_size": bar_size,
            "bars": [_bar_to_dict(bar) for bar in bars],
        }
    finally:
        _disconnect(ib)


def _connect(config: IBKRLocalConfig):
    if not tcp_port_open(config.host, config.port):
        raise IBKRConnectionError(
            f"No TWS / IB Gateway socket is listening at {config.host}:{config.port}. "
            "Open TWS or IB Gateway, log in, and enable API socket clients."
        )
    module = _require_ib_async()
    ib = module.IB()
    try:
        ib.connect(
            config.host,
            config.port,
            clientId=config.client_id,
            timeout=config.timeout,
            readonly=config.readonly,
            account=config.account or "",
        )
    except TypeError:
        ib.connect(config.host, config.port, clientId=config.client_id, timeout=config.timeout)
    except Exception as exc:
        raise IBKRConnectionError(f"Could not connect to TWS / IB Gateway at {config.host}:{config.port}: {exc}") from exc
    return ib


def _disconnect(ib: Any) -> None:
    try:
        ib.disconnect()
    except Exception:
        pass


def _require_ib_async() -> ModuleType:
    try:
        import ib_async  # type: ignore
    except ModuleNotFoundError as exc:
        raise IBKRDependencyError("ib_async is not installed; run `pip install ib_async>=2.0`.") from exc
    return ib_async


def _managed_accounts(ib: Any) -> list[str]:
    accounts = _safe_call(ib, "managedAccounts") or []
    if isinstance(accounts, str):
        return [item.strip() for item in accounts.split(",") if item.strip()]
    return [str(item) for item in accounts if str(item)]


def _account_summary(ib: Any, account: str | None) -> list[Any]:
    try:
        if account:
            return list(ib.accountSummary(account))
        return list(ib.accountSummary())
    except TypeError:
        return list(ib.accountSummary())


def _assert_profile(config: IBKRLocalConfig, accounts: Iterable[str]) -> None:
    account_list = [account for account in accounts if account]
    if config.profile != "paper":
        return
    has_paper = any(account.upper().startswith("DU") for account in account_list)
    has_live = any(account.upper().startswith("U") and not account.upper().startswith("DU") for account in account_list)
    if account_list and (not has_paper or has_live):
        raise IBKRProfileMismatchError(
            "Configured profile is paper, but connected accounts do not look like IBKR paper accounts. "
            "Use `vibe-trading connector configure ibkr-live-local-readonly` only if you intend "
            "read-only live-account access."
        )


def _make_contract(symbol: str, *, exchange: str, currency: str, sec_type: str) -> Any:
    module = _require_ib_async()
    clean_symbol = symbol.strip().upper()
    clean_type = sec_type.strip().upper()
    if clean_type == "STK" and hasattr(module, "Stock"):
        return module.Stock(clean_symbol, exchange, currency)
    contract = module.Contract()
    contract.symbol = clean_symbol
    contract.secType = clean_type
    contract.exchange = exchange
    contract.currency = currency
    return contract


def _qualify_contract(ib: Any, contract: Any) -> None:
    try:
        ib.qualifyContracts(contract)
    except Exception:
        pass


def _sleep(ib: Any, seconds: float) -> None:
    if hasattr(ib, "sleep"):
        ib.sleep(seconds)


def _call(obj: Any, name: str) -> Any:
    return getattr(obj, name)()


def _safe_call(obj: Any, name: str) -> Any:
    fn = getattr(obj, name, None)
    if fn is None:
        return None
    return fn()


def _executions(ib: Any) -> list[Any]:
    for name in ("executions", "fills", "reqExecutions"):
        result = _safe_call(ib, name)
        if result:
            return list(result)
    return []


def _obj_get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _clean_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _account_value_to_dict(item: Any) -> dict[str, Any]:
    return {
        "account": _obj_get(item, "account"),
        "tag": _obj_get(item, "tag"),
        "value": _obj_get(item, "value"),
        "currency": _obj_get(item, "currency"),
        "model_code": _obj_get(item, "modelCode"),
    }


def _trade_to_dict(trade: Any) -> dict[str, Any]:
    return {
        "contract": _contract_to_dict(_obj_get(trade, "contract")),
        "order": _order_to_dict(_obj_get(trade, "order")),
        "status": _order_status_to_dict(_obj_get(trade, "orderStatus")),
    }


def _order_to_dict(order: Any) -> dict[str, Any]:
    return {
        "order_id": _obj_get(order, "orderId"),
        "action": _obj_get(order, "action"),
        "order_type": _obj_get(order, "orderType"),
        "total_quantity": _obj_get(order, "totalQuantity"),
        "limit_price": _obj_get(order, "lmtPrice"),
        "aux_price": _obj_get(order, "auxPrice"),
        "tif": _obj_get(order, "tif"),
        "account": _obj_get(order, "account"),
    }


def _order_status_to_dict(status: Any) -> dict[str, Any]:
    return {
        "status": _obj_get(status, "status"),
        "filled": _obj_get(status, "filled"),
        "remaining": _obj_get(status, "remaining"),
        "avg_fill_price": _obj_get(status, "avgFillPrice"),
    }


def _execution_to_dict(item: Any) -> dict[str, Any]:
    execution = _obj_get(item, "execution", item)
    contract = _obj_get(item, "contract")
    return {
        "contract": _contract_to_dict(contract),
        "exec_id": _obj_get(execution, "execId"),
        "account": _obj_get(execution, "acctNumber"),
        "side": _obj_get(execution, "side"),
        "shares": _obj_get(execution, "shares"),
        "price": _obj_get(execution, "price"),
        "time": str(_obj_get(execution, "time", "")),
    }


def _contract_to_dict(contract: Any) -> dict[str, Any]:
    return {
        "symbol": _obj_get(contract, "symbol"),
        "local_symbol": _obj_get(contract, "localSymbol"),
        "sec_type": _obj_get(contract, "secType"),
        "exchange": _obj_get(contract, "exchange"),
        "currency": _obj_get(contract, "currency"),
        "con_id": _obj_get(contract, "conId"),
    }


def _bar_to_dict(bar: Any) -> dict[str, Any]:
    return {
        "date": str(_obj_get(bar, "date", "")),
        "open": _obj_get(bar, "open"),
        "high": _obj_get(bar, "high"),
        "low": _obj_get(bar, "low"),
        "close": _obj_get(bar, "close"),
        "volume": _obj_get(bar, "volume"),
        "average": _obj_get(bar, "average"),
        "bar_count": _obj_get(bar, "barCount"),
    }
