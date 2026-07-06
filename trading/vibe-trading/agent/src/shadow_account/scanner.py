"""Shadow Account — today signals scanner.

Deterministic research scanner: evaluate each Shadow rule against injected
recent OHLCV bars. The scanner never fabricates matches when data is absent.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

import pandas as pd

from src.shadow_account.backtester import _LIQUID_BASKETS, SUPPORTED_MARKETS
from src.shadow_account.models import ShadowProfile, ShadowRule

PriceFetcher = Callable[..., pd.DataFrame | None]

_RSI_PERIOD = 14


def scan_today_signals(
    profile: ShadowProfile,
    *,
    target_date: str | date | None = None,
    per_market: int = 3,
    price_frames: dict[str, pd.DataFrame] | None = None,
    fetcher: PriceFetcher | None = None,
) -> list[dict[str, Any]]:
    """Return a list of {symbol, market, rule_id, reason} matches.

    Args:
        profile: ShadowProfile holding the rules.
        target_date: ISO "YYYY-MM-DD" string, date object, or None (today).
        per_market: Cap per market bucket.
        price_frames: Optional symbol -> OHLCV frame injection for tests or
            callers that already have market data.
        fetcher: Optional callable used when ``price_frames`` has no symbol.
            It may accept ``(symbol, market, target_date)`` or fewer args.

    Returns:
        Possibly-empty list of matched candidates. Always research-only —
        callers should surface the disclaimer from the skill.
    """
    if target_date is None:
        d = date.today()
    elif isinstance(target_date, date):
        d = target_date
    else:
        d = datetime.strptime(str(target_date), "%Y-%m-%d").date()

    matches: list[dict[str, Any]] = []
    for rule in profile.rules:
        market = rule.entry_condition.get("market", "other")
        if market not in SUPPORTED_MARKETS:
            continue
        basket = _LIQUID_BASKETS.get(market, [])
        lo, hi = rule.holding_days_range
        reason = f"{rule.rule_id} price features matched (hold {lo}-{hi}d)"
        market_count = 0
        for symbol in basket:
            if market_count >= max(0, per_market):
                break
            frame = _get_price_frame(symbol, market, d, price_frames, fetcher)
            if frame is None or not _entry_condition_matches(frame, rule, d):
                continue
            matches.append({
                "symbol": symbol,
                "market": market,
                "rule_id": rule.rule_id,
                "reason": reason,
            })
            market_count += 1
    return matches


def _get_price_frame(
    symbol: str,
    market: str,
    target: date,
    price_frames: dict[str, pd.DataFrame] | None,
    fetcher: PriceFetcher | None,
) -> pd.DataFrame | None:
    """Return injected or fetched bars for ``symbol`` without raising."""
    if price_frames and symbol in price_frames:
        return price_frames[symbol]
    if fetcher is None:
        return None

    for args in ((symbol, market, target), (symbol, market), (symbol,)):
        try:
            return fetcher(*args)
        except TypeError:
            continue
        except Exception:
            return None
    return None


def _entry_condition_matches(frame: pd.DataFrame, rule: ShadowRule, target: date) -> bool:
    """Evaluate deterministic price features against a Shadow rule."""
    bars = _normalize_bars(frame, target)
    if bars is None:
        return False

    features = _compute_features(bars, rule)
    if features is None:
        return False

    checked = False
    for key, condition in rule.entry_condition.items():
        feature_name = _feature_for_condition_key(key)
        if feature_name is None:
            continue
        if feature_name not in features:
            return False
        checked = True
        if not _compare(features[feature_name], condition):
            return False

    if checked:
        return True

    if features["momentum"] <= 0 or not features["price_above_ma"]:
        return False
    if "volume_ratio" in features and features["volume_ratio"] <= 1:
        return False
    return True


def _normalize_bars(frame: pd.DataFrame, target: date) -> pd.DataFrame | None:
    """Normalize OHLCV columns and keep bars up to ``target``."""
    if frame is None or frame.empty:
        return None

    bars = frame.copy()
    bars.columns = [str(c).strip().lower() for c in bars.columns]
    rename_map = {
        "vol": "volume",
        "amount": "volume",
        "trade_date": "date",
        "datetime": "date",
        "timestamp": "date",
    }
    bars = bars.rename(columns={k: v for k, v in rename_map.items() if k in bars.columns})
    if "close" not in bars.columns:
        return None

    if "date" in bars.columns:
        dates = pd.to_datetime(bars["date"], errors="coerce")
        bars = bars.loc[dates.notna()].copy()
        bars.index = dates.loc[dates.notna()]
    elif not isinstance(bars.index, pd.DatetimeIndex):
        converted = pd.to_datetime(bars.index, errors="coerce")
        bars = bars.loc[converted.notna()].copy()
        bars.index = converted[converted.notna()]

    if isinstance(bars.index, pd.DatetimeIndex):
        bars = bars.sort_index()
        bars = bars.loc[bars.index.date <= target]

    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    bars = bars.dropna(subset=["close"])
    if "volume" in bars.columns:
        bars["volume"] = pd.to_numeric(bars["volume"], errors="coerce")
    return bars if len(bars) >= 2 else None


def _compute_features(bars: pd.DataFrame, rule: ShadowRule) -> dict[str, float | bool] | None:
    """Compute recent return, moving-average position, and volume expansion."""
    close = bars["close"]
    if close.iloc[-1] <= 0:
        return None

    momentum_window = _window_from_rule(rule, default=5)
    lookback = min(momentum_window, len(close) - 1)
    prior = close.iloc[-lookback - 1]
    if prior == 0:
        return None

    ma_window = min(_int_condition_value(rule.entry_condition.get("ma_window"), 20), len(close))
    moving_average = close.tail(ma_window).mean()
    features: dict[str, float | bool] = {
        "momentum": float(close.iloc[-1] / prior - 1),
        "price_above_ma": bool(close.iloc[-1] > moving_average),
    }

    if "volume" in bars.columns:
        volume = bars["volume"].dropna()
        if len(volume) >= 2 and volume.iloc[-1] > 0:
            volume_window = min(_int_condition_value(rule.entry_condition.get("volume_window"), 5), len(volume) - 1)
            baseline = volume.iloc[-volume_window - 1:-1].mean()
            if baseline > 0:
                features["volume_ratio"] = float(volume.iloc[-1] / baseline)

    if len(close) >= _RSI_PERIOD:
        rsi = _compute_rsi(close).iloc[-1]
        if pd.notna(rsi):
            features["entry_rsi14"] = float(rsi)
    return features


def _compute_rsi(close: pd.Series, period: int = _RSI_PERIOD) -> pd.Series:
    """Causal Wilder-EWM RSI.

    Mirrors ``_compute_rsi`` in ``extractor.py`` so the scanner evaluates the
    same RSI that produced the extracted ``entry_rsi14`` bounds. Causal by
    construction: ``RSI[t]`` depends only on closes dated ``<= t``.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def _window_from_rule(rule: ShadowRule, default: int) -> int:
    """Infer a recent-return window from common condition keys."""
    for key, value in rule.entry_condition.items():
        key_lower = str(key).lower()
        if "return" in key_lower or "momentum" in key_lower:
            parts = key_lower.replace("-", "_").split("_")
            for part in parts:
                if part.endswith("d") and part[:-1].isdigit():
                    return max(1, int(part[:-1]))
            return max(1, _int_condition_value(value, default))
    return default


def _feature_for_condition_key(key: str) -> str | None:
    """Map sparse/free-form entry condition keys to scanner features."""
    key_lower = str(key).lower()
    if key_lower in {"market", "ma_window", "volume_window"}:
        return None
    if "rsi" in key_lower:
        return "entry_rsi14"
    if "above_ma" in key_lower or "price_above" in key_lower or "close_gt_ma" in key_lower:
        return "price_above_ma"
    if "volume" in key_lower or "turnover" in key_lower:
        return "volume_ratio"
    if "return" in key_lower or "momentum" in key_lower or "roc" in key_lower:
        return "momentum"
    return None


def _compare(value: float | bool, condition: Any) -> bool:
    """Compare a feature value against scalar or ``(op, threshold)`` rules."""
    if isinstance(value, bool):
        if isinstance(condition, (tuple, list)) and len(condition) >= 2:
            condition = condition[1]
        if isinstance(condition, str):
            return value == (condition.strip().lower() not in {"false", "0", "no"})
        return value == bool(condition)

    if isinstance(condition, dict):
        lo, hi = _to_float(condition.get("min")), _to_float(condition.get("max"))
        if lo is not None and value < lo:
            return False
        if hi is not None and value > hi:
            return False
        return True

    if isinstance(condition, (tuple, list)) and len(condition) >= 2:
        op, threshold = str(condition[0]), _to_float(condition[1])
    else:
        op, threshold = ">=", _to_float(condition)

    if threshold is None:
        return True
    if op in {">", "gt"}:
        return value > threshold
    if op in {">=", "gte", "ge"}:
        return value >= threshold
    if op in {"<", "lt"}:
        return value < threshold
    if op in {"<=", "lte", "le"}:
        return value <= threshold
    if op in {"==", "=", "eq"}:
        return value == threshold
    if op in {"!=", "<>", "ne"}:
        return value != threshold
    return True


def _int_condition_value(condition: Any, default: int) -> int:
    """Extract a positive integer from a scalar or tuple condition."""
    if isinstance(condition, (tuple, list)) and len(condition) >= 2:
        condition = condition[1]
    try:
        return max(1, int(condition))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any) -> float | None:
    """Best-effort numeric parsing for rule thresholds."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
