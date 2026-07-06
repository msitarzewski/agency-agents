"""Base backtest engine with shared bar-by-bar execution loop.

All market engines inherit from BaseEngine and override market-rule methods.
The shared run_backtest() handles: data loading → signal generation →
pre-compute target weights (with optimizer) → bar-by-bar execution with
market rule enforcement → metrics → artifacts.
"""

from __future__ import annotations

import importlib
import json
import logging
import re as _re
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from backtest.loaders.rsshub_events import (
    FeedSpec,
    RSSHubEventProvider,
    enrich_price_frames_with_events,
    feed_specs_from_config,
)
from backtest.loaders.tushare_fundamentals import (
    TushareFundamentalProvider,
    enrich_price_frames_with_fundamentals,
)
from backtest.metrics import (
    by_exit_reason_stats,
    by_symbol_stats,
    calc_metrics,
)
from backtest.models import EquitySnapshot, Position, TradeRecord

logger = logging.getLogger(__name__)


def _run_card_data_sources(config: Dict[str, Any], loader: Any) -> List[str]:
    """Return source names for run-card evidence."""
    configured = config.get("_run_card_effective_sources")
    if isinstance(configured, list):
        return [str(source) for source in configured if str(source).strip()]
    if isinstance(configured, str) and configured.strip():
        return [configured.strip()]

    loader_name = getattr(loader, "name", None)
    if loader_name:
        return [str(loader_name)]

    source = config.get("source")
    return [str(source)] if source else []


# ─── Market detection (lightweight, for signal alignment only) ───

_CRYPTO_RE = _re.compile(r"^[A-Z]+-USDT$|^[A-Z]+/USDT$", _re.I)
_FOREX_RE = _re.compile(r"^[A-Z]{3}/[A-Z]{3}$|^[A-Z]{6}\.FX$")


def _detect_market_for_align(code: str) -> str:
    """Lightweight market detection for ffill_limit calculation."""
    if _CRYPTO_RE.match(code):
        return "crypto"
    if _FOREX_RE.match(code):
        return "forex"
    return "equity"


# ─── Signal alignment (reused from daily_portfolio logic) ───


def _align(
    data_map: Dict[str, pd.DataFrame],
    signal_map: Dict[str, pd.Series],
    codes: List[str],
    optimizer: Optional[Callable] = None,
) -> tuple:
    """Build aligned date index, close matrix, target-position matrix, return matrix.

    Signal is shifted by 1 bar (next-bar-open semantics) then normalised so
    ``sum(abs(weights)) <= 1.0``.

    Args:
        data_map: code -> OHLCV DataFrame.
        signal_map: code -> signal Series.
        codes: Valid instrument codes.
        optimizer: Optional weight optimiser ``(ret, pos, dates) -> pos``.

    Returns:
        (dates, close_df, positions_df, returns_df)
    """
    all_dates: set = set()
    for c in codes:
        all_dates.update(data_map[c].index)
    dates = pd.DatetimeIndex(sorted(all_dates))

    close = pd.DataFrame(index=dates, columns=codes, dtype=float)
    for c in codes:
        close[c] = data_map[c]["close"].reindex(dates)

    # ffill with limit to avoid masking long suspensions (e.g. 3-week halt)
    # Cross-market needs larger limit (Chinese New Year can be 9-10 bars)
    ffill_limit = 10 if len({_detect_market_for_align(c) for c in codes}) > 1 else 5
    close = close.ffill(limit=ffill_limit)

    # Drop symbols that are entirely NaN (no data overlap with date range)
    all_nan_cols = [c for c in codes if close[c].isna().all()]
    if all_nan_cols:
        logger.warning("Symbols dropped (no usable price data): %s", all_nan_cols)
        codes = [c for c in codes if c not in all_nan_cols]
        if not codes:
            raise ValueError("All symbols have no data in the requested date range")
        close = close[codes]

    pos = pd.DataFrame(0.0, index=dates, columns=codes)
    for c in codes:
        # Shift on each symbol's OWN trading calendar, then ffill to unified
        own_dates = data_map[c].index
        raw = signal_map[c].reindex(own_dates).fillna(0.0).clip(-1.0, 1.0)
        shifted = raw.shift(1).fillna(0.0)
        pos[c] = shifted.reindex(dates).ffill(limit=ffill_limit).fillna(0.0)

    ret = close.pct_change().fillna(0.0)

    if optimizer is not None:
        pos = optimizer(ret, pos, dates)

    scale = pos.abs().sum(axis=1).clip(lower=1.0)
    pos = pos.div(scale, axis=0)

    return dates, close, pos, ret


def _load_optimizer(config: Dict[str, Any]) -> Optional[Callable]:
    """Dynamically load an optimizer function from config.

    Args:
        config: Backtest configuration.

    Returns:
        Optimizer callable, or None.
    """
    opt_name = config.get("optimizer")
    if not opt_name:
        return None
    opt_params = config.get("optimizer_params") or {}
    try:
        mod = importlib.import_module(f"backtest.optimizers.{opt_name}")
        return lambda ret, pos, dates: mod.optimize(ret, pos, dates, **opt_params)
    except (ImportError, AttributeError) as e:
        print(f"[WARN] Failed to load optimizer '{opt_name}': {e}, falling back to equal weight")
        return None


def _normalise_fundamental_fields(config: Dict[str, Any]) -> dict[str, list[str]]:
    """Read the optional statement-table field map from backtest config."""
    raw_fields = config.get("fundamental_fields")
    if raw_fields in (None, {}):
        return {}
    if not isinstance(raw_fields, dict):
        raise ValueError("fundamental_fields must map table names to field-name lists")

    normalized: dict[str, list[str]] = {}
    for table, fields in raw_fields.items():
        if not isinstance(table, str) or not table.strip():
            raise ValueError("fundamental_fields table names must be non-empty strings")
        if fields is None:
            continue
        if isinstance(fields, str) or not isinstance(fields, Iterable):
            raise ValueError(f"fundamental_fields[{table!r}] must be a list of field names")

        field_list = list(fields)
        if not field_list:
            continue
        invalid = [field for field in field_list if not isinstance(field, str) or not field.strip()]
        if invalid:
            raise ValueError(f"fundamental_fields[{table!r}] contains invalid field names")
        normalized[table.strip()] = field_list
    return normalized


def _maybe_enrich_fundamentals(
    data_map: Dict[str, pd.DataFrame],
    config: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """Attach configured Tushare statement fields before signal generation."""
    fields_by_table = _normalise_fundamental_fields(config)
    if not fields_by_table:
        return data_map

    try:
        provider = TushareFundamentalProvider()
        return enrich_price_frames_with_fundamentals(
            data_map,
            provider,
            fields_by_table,
            as_of=config.get("end_date", ""),
            periods=config.get("fundamental_periods"),
        )
    except Exception as exc:
        raise RuntimeError(
            f"fundamental_fields requested but Tushare enrichment failed: {exc}"
        ) from exc


def _event_feed_specs(config: Dict[str, Any]) -> List[FeedSpec]:
    """Parse the optional ``event_feeds`` feed definitions from backtest config.

    ``event_feeds`` is a list of feed-definition dicts (there is no built-in
    catalogue) — each with ``name``/``route_template``/``event_type`` and an
    optional ``code_style``. An empty/absent value means "no event enrichment".
    """
    raw_feeds = config.get("event_feeds")
    if raw_feeds in (None, [], {}):
        return []
    if not isinstance(raw_feeds, (list, tuple)):
        raise ValueError("event_feeds must be a list of feed definitions")
    return feed_specs_from_config(raw_feeds)


def _maybe_enrich_events(
    data_map: Dict[str, pd.DataFrame],
    config: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """Attach a point-in-time-safe ``event_score`` column before signal generation."""
    specs = _event_feed_specs(config)
    if not specs:
        return data_map

    try:
        provider = RSSHubEventProvider(feeds=specs)
        if not provider.is_available():
            raise RuntimeError(f"RSSHub base URL not configured (set ${'RSSHUB_BASE_URL'})")
        return enrich_price_frames_with_events(
            data_map,
            provider,
            as_of=config.get("end_date", ""),
            decay_lambda=float(config.get("event_decay_lambda", 0.1)),
            lookback=int(config.get("event_lookback", 30)),
        )
    except Exception as exc:
        raise RuntimeError(
            f"event_feeds requested but RSSHub enrichment failed: {exc}"
        ) from exc


# ─── Base Engine ───


class BaseEngine(ABC):
    """Abstract base for all market engines.

    Subclasses override market-rule methods:
      - can_execute: whether a trade is allowed by market rules
      - round_size: lot-size rounding
      - calc_commission: fee structure
      - apply_slippage: slippage model
      - on_bar: per-bar hooks (funding fees, liquidation, etc.)
    """

    def __init__(self, config: dict):
        self.config = config
        self.initial_capital: float = config.get("initial_cash", 1_000_000)
        self.default_leverage: float = config.get("leverage", 1.0)
        self.capital: float = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[TradeRecord] = []
        self.equity_snapshots: List[EquitySnapshot] = []
        self._bar_idx: int = 0
        self._active_symbol: str = ""  # set by _rebalance/_close_position for subclass use

    # ── Market rule interface (subclass must implement) ──

    @abstractmethod
    def can_execute(self, symbol: str, direction: int, bar: pd.Series) -> bool:
        """Whether market rules allow this trade.

        Args:
            symbol: Instrument identifier.
            direction: 1 (long), -1 (short), 0 (close).
            bar: Current bar data (OHLCV + extras).

        Returns:
            True if allowed.
        """

    @abstractmethod
    def round_size(self, raw_size: float, price: float) -> float:
        """Round position size per market lot rules.

        Args:
            raw_size: Desired size.
            price: Current price.

        Returns:
            Rounded size.
        """

    @abstractmethod
    def calc_commission(self, size: float, price: float, direction: int, is_open: bool) -> float:
        """Calculate commission for a trade.

        Args:
            size: Trade size.
            price: Execution price.
            direction: 1 or -1.
            is_open: True for opening, False for closing.

        Returns:
            Commission amount.
        """

    @abstractmethod
    def apply_slippage(self, price: float, direction: int) -> float:
        """Apply slippage to execution price.

        Args:
            price: Raw price.
            direction: 1 (buying / covering short) or -1 (selling / shorting).

        Returns:
            Slipped price.
        """

    def on_bar(self, symbol: str, bar: pd.Series, timestamp: pd.Timestamp) -> None:
        """Per-bar market-rule hook (funding fees, liquidation, etc.).

        Default: no-op. Override in subclass as needed.
        """

    # ── PnL / margin calculation hooks ──
    # Override in FuturesBaseEngine to inject contract multiplier.

    def _calc_pnl(
        self, symbol: str, direction: int, size: float,
        entry_price: float, exit_price: float,
    ) -> float:
        """Realised PnL for a closed position."""
        return direction * size * (exit_price - entry_price)

    def _calc_margin(
        self, symbol: str, size: float, price: float, leverage: float,
    ) -> float:
        """Margin (collateral) required for a position."""
        return size * price / leverage

    def _calc_raw_size(
        self, symbol: str, target_notional: float, price: float,
    ) -> float:
        """Convert target notional exposure to number of units/contracts."""
        return target_notional / price

    # ── Main entry ──

    def run_backtest(
        self,
        config: Dict[str, Any],
        loader: Any,
        signal_engine: Any,
        run_dir: Path,
        bars_per_year: int = 252,
    ) -> Dict[str, Any]:
        """Full backtest pipeline.

        Signature matches ``daily_portfolio.run_backtest`` for drop-in replacement.

        Args:
            config: Backtest configuration dict.
            loader: DataLoader with ``fetch()`` method.
            signal_engine: SignalEngine with ``generate()`` method.
            run_dir: Artifacts output directory.
            bars_per_year: Annualisation factor.

        Returns:
            Metrics dictionary.
        """
        codes = config.get("codes", [])
        interval = config.get("interval", "1D")
        extra_fields = config.get("extra_fields") or None

        # 1. Load data
        data_map = loader.fetch(
            codes,
            config.get("start_date", ""),
            config.get("end_date", ""),
            fields=extra_fields,
            interval=interval,
        )
        if not data_map:
            print(json.dumps({"error": "No data fetched"}))
            sys.exit(1)
        data_map = _maybe_enrich_fundamentals(data_map, config)
        data_map = _maybe_enrich_events(data_map, config)

        # 2. Generate signals
        signal_map = signal_engine.generate(data_map)
        if not isinstance(signal_map, dict):
            print(json.dumps({"error": (
                f"SignalEngine.generate() must return Dict[str, pd.Series], "
                f"got {type(signal_map).__name__}. "
                "Return a dict mapping symbol codes to pandas Series of signals."
            )}))
            sys.exit(1)
        for _code, _sig in signal_map.items():
            if not isinstance(_sig, pd.Series):
                print(json.dumps({"error": (
                    f"SignalEngine.generate() returned {type(_sig).__name__} for '{_code}', "
                    "expected pd.Series. Each value must be a pandas Series with DatetimeIndex."
                )}))
                sys.exit(1)
        valid_codes = sorted(c for c in signal_map if c in data_map)
        if not valid_codes:
            print(json.dumps({"error": "No valid signals generated"}))
            sys.exit(1)

        # 3. Pre-compute target weights (with optimizer)
        opt_fn = _load_optimizer(config)
        dates, close_df, target_pos, ret_df = _align(
            data_map, signal_map, valid_codes, optimizer=opt_fn,
        )

        # Sync codes after _align may have dropped all-NaN symbols
        valid_codes = [c for c in valid_codes if c in target_pos.columns]

        # 4. Bar-by-bar execution
        self._execute_bars(dates, data_map, close_df, target_pos, valid_codes)

        # 5. Build output series
        equity_series = pd.Series(
            [s.equity for s in self.equity_snapshots],
            index=[s.timestamp for s in self.equity_snapshots],
        )
        bench_ret = ret_df.mean(axis=1) if ret_df.shape[1] > 0 else pd.Series(0.0, index=dates)
        benchmark_metadata = {}

        # ── External benchmark fetch ──────────────────────────────────────────
        bench_ticker = config.get("benchmark")
        if bench_ticker and bench_ticker != "auto":
            from backtest.benchmark import resolve_benchmark
            bench_result = resolve_benchmark(
                strategy_codes=codes,
                source=config.get("source", "yfinance"),
                start_date=config.get("start_date", ""),
                end_date=config.get("end_date", ""),
                interval=interval,
                explicit=bench_ticker,
            )
            if bench_result is not None:
                bench_ret = bench_result.ret_series.reindex(dates).fillna(0.0)
                benchmark_metadata = {
                    "benchmark_ticker": bench_result.ticker,
                    "benchmark_return": bench_result.total_ret,
                }
        # ── External benchmark fetch ──────────────────────────────────────────

        bench_equity = self.initial_capital * (1 + bench_ret).cumprod()

        # 6. Metrics
        m = calc_metrics(equity_series, self.trades, self.initial_capital, bars_per_year, bench_ret)
        m.update(benchmark_metadata)
        m["by_symbol"] = by_symbol_stats(self.trades)
        m["by_exit_reason"] = by_exit_reason_stats(self.trades)

        # 7. Validation (optional — triggered by config["validation"])
        if config.get("validation"):
            from backtest.validation import run_validation
            v_results = run_validation(
                config, equity_series, self.trades, self.initial_capital, bars_per_year,
            )
            m["validation"] = v_results
            # Write validation.json artifact
            v_path = run_dir / "artifacts" / "validation.json"
            v_path.write_text(json.dumps(v_results, indent=2, ensure_ascii=False), encoding="utf-8")

        # 8. Artifacts
        self._write_artifacts(
            run_dir, data_map, dates, equity_series, bench_equity, bench_ret,
            target_pos, m, valid_codes,
        )

        # 9. Trust Layer run card
        from backtest.run_card import write_run_card
        write_run_card(
            run_dir,
            config,
            m,
            data_sources=_run_card_data_sources(config, loader),
            strategy_path=run_dir / "code" / "signal_engine.py",
            warnings=config.get("content_filter_warnings") or None,
        )

        # Print scalar metrics (skip nested dicts for JSON compat)
        print(json.dumps({k: v for k, v in m.items() if not isinstance(v, dict)}, indent=2))
        return m

    # ── Execution loop ──

    def _execute_bars(
        self,
        dates: pd.DatetimeIndex,
        data_map: Dict[str, pd.DataFrame],
        close_df: pd.DataFrame,
        target_pos: pd.DataFrame,
        codes: List[str],
    ) -> None:
        """Bar-by-bar execution with market rule enforcement."""
        for i, ts in enumerate(dates):
            self._bar_idx = i

            # a. Per-bar hooks (funding fees, liquidation checks)
            for c in codes:
                if ts in data_map[c].index:
                    self.on_bar(c, data_map[c].loc[ts], ts)

            # b. Rebalance each symbol to target weight
            equity = self._calc_equity(close_df, ts)
            for c in codes:
                try:
                    target_w = float(target_pos.at[ts, c]) if ts in target_pos.index else 0.0
                    self._rebalance(c, target_w, data_map.get(c), ts, equity)
                except Exception as exc:
                    logger.warning("Rebalance failed for %s at %s: %s", c, ts, exc)

            # c. Record equity snapshot
            snap_equity = self._calc_equity(close_df, ts)
            total_unrealized = 0.0
            for p in self.positions.values():
                cp = self._safe_price(close_df, ts, p.symbol, p.entry_price)
                total_unrealized += self._calc_pnl(p.symbol, p.direction, p.size, p.entry_price, cp)
            self.equity_snapshots.append(EquitySnapshot(
                timestamp=ts,
                capital=self.capital,
                unrealized=total_unrealized,
                equity=snap_equity,
                positions=len(self.positions),
            ))

        # d. Force close all remaining positions
        if len(dates) > 0:
            last_ts = dates[-1]
            for c in list(self.positions.keys()):
                price = self._safe_price(close_df, last_ts, c, self.positions[c].entry_price)
                self._close_position(c, price, last_ts, "end_of_backtest")

    def _calc_equity(self, close_df: pd.DataFrame, ts: pd.Timestamp) -> float:
        """Total equity = free cash + sum(margin + unrealised) per position."""
        equity = self.capital
        for sym, pos in self.positions.items():
            cp = self._safe_price(close_df, ts, sym, pos.entry_price)
            margin = self._calc_margin(sym, pos.size, pos.entry_price, pos.leverage)
            unrealized = self._calc_pnl(sym, pos.direction, pos.size, pos.entry_price, cp)
            equity += margin + unrealized
        return equity

    def _rebalance(
        self,
        symbol: str,
        target_weight: float,
        df: Optional[pd.DataFrame],
        ts: pd.Timestamp,
        equity: float,
    ) -> None:
        """Adjust position for *symbol* toward *target_weight*."""
        self._active_symbol = symbol
        target_dir = 1 if target_weight > 1e-9 else (-1 if target_weight < -1e-9 else 0)
        current_pos = self.positions.get(symbol)

        # Nothing to do
        if current_pos is None and target_dir == 0:
            return
        if df is None or ts not in df.index:
            return

        bar = df.loc[ts]

        # Close if target is flat or direction changed
        if current_pos is not None:
            need_close = target_dir == 0 or target_dir != current_pos.direction
            if need_close:
                if self.can_execute(symbol, 0, bar):
                    open_price = float(bar.get("open", bar.get("close", 0)))
                    price = self.apply_slippage(open_price, -current_pos.direction)
                    self._close_position(symbol, price, ts, "signal")
                else:
                    return  # blocked (e.g. limit-down can't sell)

        # Open new if target non-zero and no remaining position
        if target_dir != 0 and symbol not in self.positions:
            if not self.can_execute(symbol, target_dir, bar):
                return  # blocked (e.g. A-share no-short)

            open_price = float(bar.get("open", bar.get("close", 0)))
            if open_price <= 0:
                return

            slipped = self.apply_slippage(open_price, target_dir)
            leverage = self.default_leverage
            target_notional = abs(target_weight) * equity * leverage
            raw_size = self._calc_raw_size(symbol, target_notional, slipped)
            size = self.round_size(raw_size, slipped)
            if size <= 0:
                return

            margin = self._calc_margin(symbol, size, slipped, leverage)
            comm = self.calc_commission(size, slipped, target_dir, is_open=True)

            # Capital check — reduce if insufficient
            if margin + comm > self.capital:
                available = self.capital - comm
                if available <= 0:
                    return
                size = self.round_size(
                    self._calc_raw_size(symbol, available * leverage, slipped), slipped,
                )
                if size <= 0:
                    return
                margin = self._calc_margin(symbol, size, slipped, leverage)
                comm = self.calc_commission(size, slipped, target_dir, is_open=True)

            self.capital -= (margin + comm)
            self.positions[symbol] = Position(
                symbol=symbol,
                direction=target_dir,
                entry_price=slipped,
                entry_time=ts,
                size=size,
                leverage=leverage,
                entry_bar_idx=self._bar_idx,
                entry_commission=comm,
            )

    def _close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_time: pd.Timestamp,
        reason: str,
    ) -> None:
        """Close position, record trade, return capital."""
        self._active_symbol = symbol
        pos = self.positions.pop(symbol, None)
        if pos is None:
            return

        pnl = self._calc_pnl(symbol, pos.direction, pos.size, pos.entry_price, exit_price)
        margin = self._calc_margin(symbol, pos.size, pos.entry_price, pos.leverage)
        pnl_pct = pnl / margin * 100 if margin > 1e-9 else 0.0
        exit_comm = self.calc_commission(pos.size, exit_price, pos.direction, is_open=False)

        self.capital += margin + pnl - exit_comm

        holding_bars = max(self._bar_idx - pos.entry_bar_idx, 0)

        self.trades.append(TradeRecord(
            symbol=symbol,
            direction=pos.direction,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            entry_time=pos.entry_time,
            exit_time=exit_time,
            size=pos.size,
            leverage=pos.leverage,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
            holding_bars=holding_bars,
            commission=pos.entry_commission + exit_comm,
        ))

    # ── Artifacts ──

    def _write_artifacts(
        self,
        run_dir: Path,
        data_map: Dict[str, pd.DataFrame],
        dates: pd.DatetimeIndex,
        equity_series: pd.Series,
        bench_equity: pd.Series,
        bench_ret: pd.Series,
        target_pos: pd.DataFrame,
        metrics: dict,
        codes: List[str],
    ) -> None:
        """Write CSV artifacts compatible with daily_portfolio format."""
        out = run_dir / "artifacts"
        out.mkdir(parents=True, exist_ok=True)

        # OHLCV per symbol
        for code, df in data_map.items():
            df.to_csv(out / f"ohlcv_{code}.csv")

        # Equity curve
        port_ret = equity_series.pct_change().fillna(0.0)
        peak = equity_series.cummax()
        dd = (equity_series - peak) / peak.replace(0, 1)
        eq_df = pd.DataFrame({
            "ret": port_ret,
            "equity": equity_series,
            "drawdown": dd,
            "benchmark_equity": bench_equity.reindex(dates),
            "active_ret": port_ret - bench_ret.reindex(dates).fillna(0.0),
        }, index=dates)
        eq_df.index.name = "timestamp"
        eq_df.to_csv(out / "equity.csv")

        # Position weights (target, for compatibility)
        target_pos.index.name = "timestamp"
        target_pos.to_csv(out / "positions.csv")

        # Trades (compatible format)
        trade_rows = []
        for t in self.trades:
            # Entry event
            trade_rows.append({
                "timestamp": str(t.entry_time.date()) if hasattr(t.entry_time, "date") else str(t.entry_time),
                "code": t.symbol,
                "side": "buy" if t.direction == 1 else "sell",
                "price": round(t.entry_price, 4),
                "qty": round(t.size, 6),
                "reason": "signal",
                "pnl": 0.0,
                "holding_days": 0,
                "return_pct": 0.0,
            })
            # Exit event
            try:
                hold_days = (t.exit_time - t.entry_time).days
            except Exception:
                hold_days = 0
            trade_rows.append({
                "timestamp": str(t.exit_time.date()) if hasattr(t.exit_time, "date") else str(t.exit_time),
                "code": t.symbol,
                "side": "sell" if t.direction == 1 else "buy",
                "price": round(t.exit_price, 4),
                "qty": round(t.size, 6),
                "reason": t.exit_reason,
                "pnl": round(t.pnl, 4),
                "holding_days": hold_days,
                "return_pct": round(t.pnl_pct, 2),
            })

        trade_cols = ["timestamp", "code", "side", "price", "qty", "reason", "pnl", "holding_days", "return_pct"]
        pd.DataFrame(trade_rows or [], columns=trade_cols).to_csv(out / "trades.csv", index=False)

        # Metrics
        flat_metrics = {k: v for k, v in metrics.items() if not isinstance(v, dict)}
        pd.DataFrame([flat_metrics]).to_csv(out / "metrics.csv", index=False)

    # ── Helpers ──

    @staticmethod
    def _safe_price(
        close_df: pd.DataFrame,
        ts: pd.Timestamp,
        symbol: str,
        fallback: float,
    ) -> float:
        """Get close price with fallback."""
        if ts in close_df.index and symbol in close_df.columns:
            val = close_df.at[ts, symbol]
            if pd.notna(val):
                return float(val)
        return fallback
