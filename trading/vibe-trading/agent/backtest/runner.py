"""Fixed backtest entrypoint: read config.json, select loader by source, import signal_engine, run engine.

Supports ``source="auto"`` to route codes to loaders by symbol format.
Supports ``interval`` for bar size (1m/5m/15m/30m/1H/4H/1D, default 1D).
Supports ``engine`` for backtest engine (daily/options, default daily).

Usage: ``python -m backtest.runner <run_dir>``
"""

import ast
import importlib.util
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, model_validator, field_validator

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backtest.loaders.registry import (
    FALLBACK_CHAINS,
    LOADER_REGISTRY,
    VALID_SOURCES,
    get_loader_cls_with_fallback,
    resolve_loader,
)
from backtest.loaders.base import NoAvailableSourceError, validate_ohlc
# Symbol classification lives in ``_market_hooks`` so runner.py and
# composite.py share a single source of truth (audit-2026-05-18 B1+C1+C2).
# ``_detect_market`` is also re-exported here for back-compat with
# ``agent/src/swarm/grounding.py`` and existing tests that import it
# from ``backtest.runner``.
from backtest.engines._market_hooks import (  # noqa: F401  (re-exported)
    _detect_market,
    _detect_submarket,
    _is_china_futures,
)

logger = logging.getLogger(__name__)

_VALID_INTERVALS = {"1m", "5m", "15m", "30m", "1H", "4H", "1D"}
_VALID_ENGINES = {"daily", "options"}


class BacktestConfigSchema(BaseModel):
    """Validates backtest config.json before execution."""

    model_config = ConfigDict(extra="allow")

    codes: List[str]
    start_date: str
    end_date: str
    source: str = "tushare"
    interval: str = "1D"
    engine: str = "daily"
    fundamental_fields: Optional[Dict[str, List[str]]] = None
    event_feeds: Optional[List[Dict[str, Any]]] = None

    @field_validator("codes")
    @classmethod
    def codes_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("codes must be a non-empty list")
        if any(not c.strip() for c in v):
            raise ValueError("codes must not contain empty strings")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        try:
            pd.Timestamp(v)
        except Exception:
            raise ValueError(f"invalid date format: {v!r} (expected YYYY-MM-DD)")
        return v

    @field_validator("interval")
    @classmethod
    def valid_interval(cls, v: str) -> str:
        if v not in _VALID_INTERVALS:
            raise ValueError(f"unsupported interval {v!r}, must be one of {_VALID_INTERVALS}")
        return v

    @field_validator("engine")
    @classmethod
    def valid_engine(cls, v: str) -> str:
        if v not in _VALID_ENGINES:
            raise ValueError(f"unsupported engine {v!r}, must be one of {_VALID_ENGINES}")
        return v

    @field_validator("source")
    @classmethod
    def valid_source(cls, v: str) -> str:
        if v not in VALID_SOURCES:
            raise ValueError(f"unsupported source {v!r}, must be one of {VALID_SOURCES}")
        return v

    @field_validator("fundamental_fields")
    @classmethod
    def valid_fundamental_fields(
        cls,
        v: Optional[Dict[str, List[str]]],
    ) -> Optional[Dict[str, List[str]]]:
        if v is None:
            return v
        for table, fields in v.items():
            if not table.strip():
                raise ValueError("fundamental_fields table names must be non-empty strings")
            if any(not field.strip() for field in fields):
                raise ValueError("fundamental_fields field names must be non-empty strings")
        return v

    @field_validator("event_feeds")
    @classmethod
    def valid_event_feeds(cls, v: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        if v is None:
            return v
        for entry in v:
            if not isinstance(entry, dict):
                raise ValueError(
                    "each event_feeds entry must be an object with name/route_template/event_type"
                )
            for key in ("name", "route_template", "event_type"):
                if not str(entry.get(key, "")).strip():
                    raise ValueError(f"event_feeds entry missing required field: {key}")
        return v

    @model_validator(mode="after")
    def start_before_end(self) -> "BacktestConfigSchema":
        if pd.Timestamp(self.start_date) > pd.Timestamp(self.end_date):
            raise ValueError(
                f"start_date ({self.start_date}) must be <= end_date ({self.end_date})"
            )
        return self


def _load_module_from_file(file_path: Path, module_name: str):
    """Load a Python module from a file path via importlib.

    Args:
        file_path: Path to the ``.py`` file.
        module_name: Logical module name.

    Returns:
        Loaded module object.
    """
    _validate_signal_engine_source(file_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _is_literal_node(node: ast.AST) -> bool:
    """Return whether an AST node is made only from literal values."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_is_literal_node(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or _is_literal_node(key)) and _is_literal_node(value)
            for key, value in zip(node.keys, node.values)
        )
    return False


def _is_safe_constant_assignment(node: ast.AST) -> bool:
    """Return whether a top-level assignment is literal-only."""
    if isinstance(node, ast.Assign):
        return _is_literal_node(node.value)
    if isinstance(node, ast.AnnAssign):
        return node.value is None or _is_literal_node(node.value)
    return False


def _is_safe_reference(node: ast.AST | None) -> bool:
    """Return whether an annotation/base expression cannot call code."""
    if node is None:
        return True
    if isinstance(node, (ast.Name, ast.Attribute, ast.Constant)):
        return True
    if isinstance(node, ast.Subscript):
        return _is_safe_reference(node.value) and _is_safe_reference(node.slice)
    if isinstance(node, ast.Tuple):
        return all(_is_safe_reference(item) for item in node.elts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _is_safe_reference(node.left) and _is_safe_reference(node.right)
    return False


def _validate_function_def(node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
    """Reject import-time execution in function definitions."""
    if node.decorator_list:
        raise ValueError(f"Decorators are not allowed on function {node.name!r}")
    for default in [*node.args.defaults, *[d for d in node.args.kw_defaults if d]]:
        if not _is_literal_node(default):
            raise ValueError(f"Non-literal default is not allowed on function {node.name!r}")
    annotations = [node.returns]
    annotations.extend(arg.annotation for arg in node.args.posonlyargs)
    annotations.extend(arg.annotation for arg in node.args.args)
    annotations.extend(arg.annotation for arg in node.args.kwonlyargs)
    annotations.append(node.args.vararg.annotation if node.args.vararg else None)
    annotations.append(node.args.kwarg.annotation if node.args.kwarg else None)
    for annotation in annotations:
        if not _is_safe_reference(annotation):
            raise ValueError(f"Unsafe annotation is not allowed on function {node.name!r}")


def _validate_class_body(node: ast.ClassDef) -> None:
    """Reject import-time execution inside class bodies."""
    if node.decorator_list:
        raise ValueError(f"Decorators are not allowed on class {node.name!r}")
    for base in node.bases:
        if not _is_safe_reference(base):
            raise ValueError(f"Unsafe base class is not allowed on class {node.name!r}")
    if node.keywords:
        raise ValueError(f"Class keywords are not allowed on class {node.name!r}")
    for child in node.body:
        if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _validate_function_def(child)
            continue
        if _is_safe_constant_assignment(child):
            continue
        if isinstance(child, ast.Pass):
            continue
        raise ValueError(
            f"Executable class-level statement {type(child).__name__} is not allowed"
        )


def _validate_signal_engine_source(file_path: Path) -> None:
    """Reject import-time executable statements before loading signal_engine.py."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except SyntaxError as exc:
        raise ValueError(f"Invalid signal_engine.py syntax: {exc}") from exc

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "signal_engine":
            raise ValueError(
                "Circular import: 'from signal_engine import ...' imports the file from itself. "
                "Remove this import — SignalEngine is defined in this same file."
            )
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _validate_function_def(node)
            continue
        if isinstance(node, ast.ClassDef):
            _validate_class_body(node)
            continue
        if _is_safe_constant_assignment(node):
            continue
        raise ValueError(
            f"Executable top-level statement {type(node).__name__} is not allowed"
        )


def _validate_signal_engine_class(engine_cls) -> None:
    """Pre-flight check: SignalEngine can be instantiated with no args and has generate()."""
    sig = inspect.signature(engine_cls.__init__)
    required = [
        p.name for p in sig.parameters.values()
        if p.name != "self" and p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]
    if required:
        raise ValueError(
            f"SignalEngine.__init__() has required arguments {required}. "
            "All parameters must have default values so the runner can call SignalEngine()."
        )
    if not callable(getattr(engine_cls, "generate", None)):
        raise ValueError(
            "SignalEngine must have a callable 'generate' method. "
            "Expected: def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]"
        )


# --- Market detection ---
# ``_MARKET_PATTERNS``, ``_detect_market``, ``_is_china_futures``,
# ``_detect_submarket`` are imported from ``_market_hooks`` above and
# re-exported here for back-compat (swarm/grounding.py, tests).

# Back-compat: market type -> legacy source name (for engine selection & metrics)
_MARKET_TO_SOURCE = {
    "a_share": "tushare",
    "us_equity": "yfinance",
    "hk_equity": "yfinance",
    "crypto": "okx",
    "futures": "tushare",
    "fund": "tushare",
    "macro": "akshare",
    "forex": "akshare",
}


def _detect_source(code: str) -> str:
    """Infer legacy source name from symbol (back-compat for metrics/engine).

    Args:
        code: Ticker / symbol string.

    Returns:
        Source name (tushare/okx/yfinance/akshare).
    """
    market = _detect_market(code)
    return _MARKET_TO_SOURCE.get(market, "tushare")


def _group_codes_by_market(codes: List[str]) -> Dict[str, List[str]]:
    """Group symbols by detected market type.

    Args:
        codes: List of symbol strings.

    Returns:
        Mapping market_type -> list of codes.
    """
    groups: Dict[str, List[str]] = {}
    for code in codes:
        market = _detect_market(code)
        groups.setdefault(market, []).append(code)
    return groups


def _group_codes_by_source(codes: List[str]) -> Dict[str, List[str]]:
    """Group symbols by inferred source (back-compat).

    Args:
        codes: List of symbol strings.

    Returns:
        Mapping source -> list of codes.
    """
    groups: Dict[str, List[str]] = {}
    for code in codes:
        src = _detect_source(code)
        groups.setdefault(src, []).append(code)
    return groups


def _get_loader(source: str):
    """Return a DataLoader class for a source name, with fallback.

    Args:
        source: Source name (tushare/okx/yfinance/akshare/ccxt).

    Returns:
        DataLoader class.
    """
    try:
        return get_loader_cls_with_fallback(source)
    except NoAvailableSourceError:
        # Ultimate fallback for unknown sources
        if "tushare" in LOADER_REGISTRY:
            return LOADER_REGISTRY["tushare"]
        raise


def _normalize_codes(codes: List[str], source: str) -> List[str]:
    """Normalize symbol strings for a source.

    Args:
        codes: Raw code list.
        source: Data source.

    Returns:
        Normalized codes.
    """
    if source in ("okx", "ccxt"):
        return [c.replace("/", "-").upper() for c in codes]
    return codes


# --- Main entry ---

def main(run_dir: Path) -> None:
    """Load config, fetch data, run the selected backtest engine.

    With ``source="auto"``, routes each code through the appropriate loader.

    Args:
        run_dir: Run directory containing ``config.json`` and ``code/signal_engine.py``.
            The path is validated against the allowed run roots
            (``VIBE_TRADING_ALLOWED_RUN_ROOTS`` plus the defaults) before any
            file is read so an arbitrary filesystem location cannot be used
            to source ``code/signal_engine.py``.
    """
    # Guard the CLI entry point with the same root whitelist the MCP
    # ``backtest`` tool already uses (src/tools/backtest_tool.py:23). Without
    # this, ``python -m backtest.runner /tmp/attacker_path`` would happily
    # import ``signal_engine.py`` from anywhere on disk; the AST scrubber
    # below blocks executable top-level statements but a method body still
    # runs on instantiation. See ``safe_run_dir`` for the policy.
    from src.tools.path_utils import safe_run_dir
    try:
        run_dir = safe_run_dir(str(run_dir))
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

    config_path = run_dir / "config.json"
    if not config_path.exists():
        print(json.dumps({"error": "config.json not found"}))
        sys.exit(1)

    raw_config = json.loads(config_path.read_text(encoding="utf-8"))

    # Validate config schema
    try:
        BacktestConfigSchema(**raw_config)
    except Exception as exc:
        errors = str(exc)
        print(json.dumps({"error": f"Invalid config: {errors}"}))
        sys.exit(1)

    config = raw_config
    source = config.get("source", "tushare")
    codes = config.get("codes", [])

    # Load signal engine
    signal_path = run_dir / "code" / "signal_engine.py"
    if not signal_path.exists():
        print(json.dumps({"error": "code/signal_engine.py not found"}))
        sys.exit(1)

    try:
        signal_module = _load_module_from_file(signal_path, "signal_engine")
    except ValueError as exc:
        # Source-level AST validation (circular self-import, unsafe imports,
        # decorators, top-level statements) raises ValueError. Surface it as a
        # clean JSON envelope instead of a raw traceback so the agent gets an
        # actionable message.
        print(json.dumps({"error": f"SignalEngine source error: {exc}"}))
        sys.exit(1)
    engine_cls = getattr(signal_module, "SignalEngine", None)
    if engine_cls is None:
        print(json.dumps({"error": "SignalEngine class not found in signal_engine.py"}))
        sys.exit(1)

    try:
        _validate_signal_engine_class(engine_cls)
    except ValueError as exc:
        print(json.dumps({"error": f"SignalEngine interface error: {exc}"}))
        sys.exit(1)

    # Data: auto split vs single loader
    interval = config.get("interval", "1D")

    if source == "auto":
        data_map = _fetch_auto(codes, config, interval)
    else:
        codes = _normalize_codes(codes, source)
        config["codes"] = codes
        LoaderCls = _get_loader(source)
        loader = LoaderCls()
        data_map = loader.fetch(
            codes,
            config.get("start_date", ""),
            config.get("end_date", ""),
            fields=config.get("extra_fields") or None,
            interval=interval,
        )
        if data_map and len(data_map) < len(codes):
            missing = set(codes) - set(data_map.keys())
            logger.warning(
                "source=%s returned data for %d/%d symbols; missing: %s",
                source, len(data_map), len(codes), missing,
            )
        # Runtime fallback: try next sources in chain when primary returns empty
        if not data_map and codes:
            market = _detect_market(codes[0])
            for fb_name in FALLBACK_CHAINS.get(market, []):
                if fb_name == source or fb_name not in LOADER_REGISTRY:
                    continue
                fb_loader = LOADER_REGISTRY[fb_name]()
                if not fb_loader.is_available():
                    continue
                fb_codes = _normalize_codes(codes, fb_name)
                data_map = fb_loader.fetch(
                    fb_codes, config.get("start_date", ""),
                    config.get("end_date", ""), interval=interval,
                )
                if data_map:
                    logger.info("Runtime fallback: %s -> %s", source, fb_name)
                    source = fb_name
                    loader = fb_loader
                    break

    # Loader-boundary OHLC sanity for every source, centralized at the one
    # point all fetch paths converge (auto / single / runtime fallback).
    data_map = _sanitize_data_map(data_map)
    if not data_map:
        print(json.dumps({"error": "No data fetched"}))
        sys.exit(1)

    if source == "auto":
        config["_run_card_effective_sources"] = sorted(_group_codes_by_source(codes))
    else:
        config["_run_card_effective_sources"] = [source]

    # Engine
    engine_type = config.get("engine", "daily")
    signal_engine = engine_cls()

    # Annualization bars
    effective_source = _detect_primary_source(codes, source)
    from backtest.metrics import calc_bars_per_year
    # Cross-market: use calendar-day annualization (bars_per_year=None)
    market_types = {_detect_market(c) for c in codes}
    if len(market_types) > 1:
        bars_per_year = None
    else:
        bars_per_year = calc_bars_per_year(interval, effective_source)

    # Auto mode: wrap preloaded data in a dummy loader
    if source == "auto":
        loader = _AutoLoader(data_map)

    if engine_type == "options":
        from backtest.engines.options_portfolio import run_options_backtest
        run_options_backtest(config, loader, signal_engine, run_dir, bars_per_year=bars_per_year)
    else:
        market_engine = _create_market_engine(effective_source, config, codes)
        market_engine.run_backtest(config, loader, signal_engine, run_dir, bars_per_year=bars_per_year)


def _create_market_engine(source: str, config: dict, codes: List[str]):
    """Create the appropriate market engine based on data source and market type.

    Routing priority:
      1. Detect market type from symbol patterns (futures, forex, etc.)
      2. Fall back to source-based routing (okx->crypto, tushare->china_a, etc.)

    Args:
        source: Data source (okx/ccxt/tushare/akshare/yfinance).
        config: Backtest configuration.
        codes: Instrument codes.

    Returns:
        BaseEngine subclass instance.
    """
    # Detect dominant market type from codes
    markets = {_detect_market(c) for c in codes} if codes else set()

    # Cross-market -> CompositeEngine
    if len(markets) > 1:
        from backtest.engines.composite import CompositeEngine
        return CompositeEngine(config, codes)

    # Futures routing (Wave 2)
    if "futures" in markets:
        # Distinguish China vs global futures by exchange suffix
        if any(_is_china_futures(c) for c in codes):
            from backtest.engines.china_futures import ChinaFuturesEngine
            return ChinaFuturesEngine(config)
        from backtest.engines.global_futures import GlobalFuturesEngine
        return GlobalFuturesEngine(config)

    # Forex routing (Wave 2)
    if "forex" in markets:
        from backtest.engines.forex import ForexEngine
        return ForexEngine(config)

    # Original routing (Wave 1)
    if source in ("okx", "ccxt"):
        from backtest.engines.crypto import CryptoEngine
        return CryptoEngine(config)
    elif source in ("tushare", "akshare"):
        if markets & {"us_equity", "hk_equity"}:
            from backtest.engines.global_equity import GlobalEquityEngine
            market = _detect_submarket(codes)
            return GlobalEquityEngine(config, market=market)
        from backtest.engines.china_a import ChinaAEngine
        return ChinaAEngine(config)
    elif source == "yfinance":
        from backtest.engines.global_equity import GlobalEquityEngine
        market = _detect_submarket(codes)
        return GlobalEquityEngine(config, market=market)
    else:
        from backtest.engines.crypto import CryptoEngine
        return CryptoEngine(config)


def _detect_primary_source(codes: List[str], source: str) -> str:
    """Pick primary source for annualization (e.g. bars per year).

    Args:
        codes: All symbols.
        source: Config ``source`` field.

    Returns:
        Dominant source name.
    """
    if source != "auto":
        return source
    groups = _group_codes_by_source(codes)
    if len(groups) == 1:
        return list(groups.keys())[0]
    # Mixed: use the source with the most symbols
    return max(groups, key=lambda s: len(groups[s]))


def _fetch_auto(codes: List[str], config: dict, interval: str = "1D") -> dict:
    """Auto mode: route each market group through fallback chain.

    Args:
        codes: All symbols.
        config: Backtest config dict.
        interval: Bar interval string.

    Returns:
        Merged ``code -> DataFrame`` map.
    """
    market_groups = _group_codes_by_market(codes)
    merged = {}
    start_date = config.get("start_date", "")
    end_date = config.get("end_date", "")

    for market, market_codes in market_groups.items():
        try:
            loader = resolve_loader(market)
        except NoAvailableSourceError as exc:
            # Fallback: try legacy source mapping
            legacy_src = _MARKET_TO_SOURCE.get(market, "tushare")
            logger.warning("Fallback chain failed for %s: %s — trying %s", market, exc, legacy_src)
            LoaderCls = _get_loader(legacy_src)
            loader = LoaderCls()

        src_name = getattr(loader, "name", "unknown")
        normalized_codes = _normalize_codes(market_codes, src_name)
        fields = config.get("extra_fields") if src_name == "tushare" else None
        result = loader.fetch(normalized_codes, start_date, end_date, fields=fields, interval=interval)

        # Runtime fallback: try remaining sources when primary returns empty
        if not result:
            for fb_name in FALLBACK_CHAINS.get(market, []):
                if fb_name == src_name or fb_name not in LOADER_REGISTRY:
                    continue
                fb_loader = LOADER_REGISTRY[fb_name]()
                if not fb_loader.is_available():
                    continue
                fb_codes = _normalize_codes(market_codes, fb_name)
                result = fb_loader.fetch(fb_codes, start_date, end_date, interval=interval)
                if result:
                    logger.info("Runtime fallback: %s -> %s for %s", src_name, fb_name, market)
                    break

        merged.update(result)

    return merged


def _sanitize_data_map(data_map: dict) -> dict:
    """Drop structurally-invalid OHLC bars from every fetched frame.

    Each loader only drops NaN rows, so a bar that violates the OHLC
    invariants (``high < low``, a non-positive price, or a high/low that fails
    to bracket open/close) can still reach the backtest and surface as NaN/inf
    metrics. Applying :func:`validate_ohlc` here — the single point every
    fetched map converges through — guards every source uniformly (``auto``,
    single-source, runtime fallback, and any future loader), so the per-loader
    checks no longer have to be added one at a time.

    Args:
        data_map: ``code -> DataFrame`` map as returned by a loader fetch.

    Returns:
        The same mapping with each frame's invalid bars removed.
    """
    return {code: validate_ohlc(frame) for code, frame in data_map.items()}


class _AutoLoader:
    """Dummy loader for auto mode: returns pre-fetched data maps."""

    def __init__(self, data_map: dict):
        self._data = data_map

    def fetch(self, codes, start_date, end_date, fields=None, interval="1D"):
        """Return preloaded rows for requested codes."""
        return {c: df for c, df in self._data.items() if c in codes}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backtest.runner <run_dir>")
        sys.exit(1)
    main(Path(sys.argv[1]))
