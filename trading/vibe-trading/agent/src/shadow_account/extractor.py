"""Shadow Account — strategy extraction from profitable roundtrips.

Pipeline:
    trades_df → FIFO pair → filter (pnl > 0) → feature engineer
    → KMeans cluster (k auto 2-5) → per-cluster decision tree (max_depth=3)
    → path extraction → structured entry_condition dict
    → LLM-light natural-language translation (template fallback if no LLM)

Design constraints:
    * No *mandatory* external price-data calls. Journal-derived features
      (holding_days, pnl_pct, entry hour/weekday, market) always work offline.
      Price-context features (entry_rsi14, prior_5d_return) are read as-of the
      buy date via the backtest loader registry and degrade to NaN — dropped
      from the feature matrix — whenever price data is unavailable.
    * Must survive tiny samples: <5 profitable roundtrips → explicit error.
      <2 clusters → degrade to a single-cluster heuristic rule.
    * Rules are immutable ShadowRule objects — codegen's only input.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.shadow_account.models import PRICE_FEATURES, ShadowProfile, ShadowRule
from src.shadow_account.storage import hash_journal, new_shadow_id, now_iso
from src.tools.trade_journal_parsers import parse_file, records_to_dataframe
from src.tools.trade_journal_tool import pair_trades_fifo

logger = logging.getLogger(__name__)

MIN_PROFITABLE_ROUNDTRIPS = 5
DEFAULT_MAX_RULES = 5
DEFAULT_MIN_SUPPORT = 3
_NUMERIC_FEATURES = ("holding_days", "pnl_pct", "entry_hour", "entry_weekday")
_CATEGORICAL_FEATURES = ("market",)

# Price-context features attached as-of buy_dt (NaN when price data unavailable).
# Names live on the data-contract boundary (models.PRICE_FEATURES) so the
# extractor, codegen, and scanner cannot drift; aliased here for local use.
_PRICE_FEATURES = PRICE_FEATURES
_RSI_PERIOD = 14
_PRIOR_RETURN_WINDOW = 5
# Calendar buffer added before the earliest buy_dt so the RSI warmup has enough
# trading bars even across weekends/holidays.
_PRICE_LOOKBACK_DAYS = 40

# Journal market label → backtest loader-registry market key. Labels with no
# mapping (e.g. "other") skip the price fetch and degrade to NaN.
_MARKET_KEY_MAP = {
    "china_a": "a_share",
    "us": "us_equity",
    "hk": "hk_equity",
    "crypto": "crypto",
}


# ---------------- Public API ----------------

def extract_shadow_profile(
    journal_path: str | Path,
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
    max_rules: int = DEFAULT_MAX_RULES,
    llm_translator: Any | None = None,
) -> ShadowProfile:
    """Extract a ShadowProfile from a broker journal file.

    Args:
        journal_path: CSV/Excel exported from a supported broker.
        min_support: Minimum profitable roundtrips backing any single rule.
        max_rules: Cap on the number of rules returned.
        llm_translator: Optional callable (dict) -> str for translating
            structured entry_condition into natural-language text. If None,
            a deterministic f-string fallback is used.

    Returns:
        ShadowProfile (not yet persisted — caller decides whether to save).

    Raises:
        ValueError: Fewer than MIN_PROFITABLE_ROUNDTRIPS profitable roundtrips.
    """
    path = Path(journal_path)
    fmt, records = parse_file(path)
    if not records:
        raise ValueError(f"No trade records parsed from {path} (format={fmt})")
    trades_df = records_to_dataframe(records)

    roundtrips = pair_trades_fifo(trades_df)
    total = len(roundtrips)
    if total == 0:
        raise ValueError("No complete buy→sell roundtrips found in journal.")

    profitable = [rt for rt in roundtrips if rt["pnl"] > 0]
    if len(profitable) < MIN_PROFITABLE_ROUNDTRIPS:
        raise ValueError(
            f"Insufficient profitable roundtrips: {len(profitable)} "
            f"(need ≥{MIN_PROFITABLE_ROUNDTRIPS}).",
        )

    features_df = _compute_features(profitable, trades_df)
    rules = _extract_rules(
        features_df,
        min_support=min_support,
        max_rules=max_rules,
        llm_translator=llm_translator,
    )

    source_market = _dominant(trades_df["market"])
    preferred_markets = tuple(trades_df["market"].value_counts().index.tolist())
    hold = features_df["holding_days"].dropna()
    typical_holding = (
        round(float(hold.median()), 2) if len(hold) else 0.0,
        round(float(hold.quantile(0.75)), 2) if len(hold) else 0.0,
    )
    date_range = (
        str(trades_df["datetime"].min()),
        str(trades_df["datetime"].max()),
    )
    profile_text = _render_profile_text(
        total_profitable=len(profitable),
        total_all=total,
        typical_holding=typical_holding,
        source_market=source_market,
        preferred_markets=preferred_markets,
    )

    return ShadowProfile(
        shadow_id=new_shadow_id(),
        created_at=now_iso(),
        journal_hash=hash_journal(path),
        source_market=source_market,
        profitable_roundtrips=len(profitable),
        total_roundtrips=total,
        date_range=date_range,
        profile_text=profile_text,
        rules=tuple(rules),
        preferred_markets=preferred_markets,
        typical_holding_days=typical_holding,
    )


# ---------------- Feature engineering ----------------

def _compute_rsi(close: pd.Series, period: int = _RSI_PERIOD) -> pd.Series:
    """Causal Wilder-EWM RSI.

    Mirrors the shape of ``compute_rsi`` in
    ``agent/src/skills/technical-basic/example_signal_engine.py:13`` — that
    module lives under a hyphenated (non-importable) skills directory, so the
    formula is re-implemented here rather than imported. Causal by construction:
    ``RSI[t]`` depends only on closes dated ``<= t``.

    Args:
        close: Close-price series indexed by date.
        period: RSI lookback period.

    Returns:
        RSI series (0-100), NaN for the warmup window.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def _fetch_price_history(
    symbol: str,
    market: str,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame | None:
    """Fetch daily OHLCV for one symbol via the backtest loader registry.

    Uses the same access path as the backtest runner (``resolve_loader`` +
    the loader ``fetch`` protocol). Any failure — unmapped market, no available
    source, empty result, symbol absent from the returned map — degrades to
    ``None`` so the caller can drop the price features rather than raise.

    Args:
        symbol: Journal symbol, passed to the loader as-is (no cross-market
            normalization in v1).
        market: Journal market label (e.g. ``"china_a"``).
        start: Inclusive fetch start (already buffered for indicator warmup).
        end: Inclusive fetch end — never later than the roundtrip's buy_dt, so
            look-ahead is structurally impossible.

    Returns:
        A ``trade_date``-indexed OHLCV frame, or ``None`` when unavailable.
    """
    market_key = _MARKET_KEY_MAP.get(market)
    if market_key is None:
        return None
    try:
        from backtest.loaders.base import NoAvailableSourceError
        from backtest.loaders.registry import resolve_loader

        loader = resolve_loader(market_key)
        data_map = loader.fetch(
            [symbol],
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
            interval="1D",
        )
    except NoAvailableSourceError as exc:
        logger.debug("No price source for %s (%s): %s", symbol, market, exc)
        return None
    except Exception as exc:  # pragma: no cover — loader/network edge cases
        logger.debug("Price fetch failed for %s (%s): %s", symbol, market, exc)
        return None

    frame = data_map.get(symbol)
    if frame is None or frame.empty or "close" not in frame.columns:
        return None
    return frame


def _as_of_index(frame: pd.DataFrame, buy_dt: pd.Timestamp) -> pd.DataFrame:
    """Slice a price frame to bars dated on or before *buy_dt*.

    The loader frame is indexed by a tz-naive ``DatetimeIndex`` at day
    granularity; ``buy_dt`` carries a time-of-day and may be tz-aware. Normalize
    to a tz-naive date before slicing, otherwise the ``.loc`` comparison raises.
    """
    as_of = pd.Timestamp(buy_dt)
    if as_of.tzinfo is not None:
        as_of = as_of.tz_localize(None)
    as_of = as_of.normalize()
    return frame.loc[:as_of]


def _price_features_as_of(
    frame: pd.DataFrame | None,
    buy_dt: pd.Timestamp,
) -> dict[str, float]:
    """Compute price-context features as-of *buy_dt* from a price frame.

    Every value is read from bars dated ``<= buy_dt`` only; bars in the
    ``(buy_dt, sell_dt]`` exit window are never consulted. Insufficient history
    leaves the affected feature as ``NaN``.
    """
    out: dict[str, float] = {name: float("nan") for name in _PRICE_FEATURES}
    if frame is None:
        return out

    history = _as_of_index(frame, buy_dt)
    close = history["close"].dropna()
    if close.empty:
        return out

    if len(close) >= _RSI_PERIOD:
        rsi = _compute_rsi(close).iloc[-1]
        out["entry_rsi14"] = float(rsi) if pd.notna(rsi) else float("nan")

    if len(close) >= _PRIOR_RETURN_WINDOW + 1:
        ret = close.pct_change(_PRIOR_RETURN_WINDOW).iloc[-1]
        out["prior_5d_return"] = float(ret) if pd.notna(ret) else float("nan")

    return out


def _attach_price_features(
    rows: list[dict[str, Any]],
) -> None:
    """Attach price-context features in place, batching one fetch per symbol.

    Groups roundtrips by symbol, fetches each symbol's price window once over
    ``[min(buy_dt) - buffer, max(buy_dt)]``, then reads each roundtrip's
    features as-of its own buy_dt. Mutates each row dict with the price-feature
    keys (NaN when unavailable).
    """
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_symbol.setdefault(row["symbol"], []).append(row)

    for symbol, sym_rows in by_symbol.items():
        market = sym_rows[0]["market"]
        buy_dts = [pd.Timestamp(r["buy_dt"]) for r in sym_rows]
        end = max(buy_dts)
        start = min(buy_dts) - pd.Timedelta(days=_PRICE_LOOKBACK_DAYS)
        if end.tzinfo is not None:
            end = end.tz_localize(None)
        if start.tzinfo is not None:
            start = start.tz_localize(None)
        frame = _fetch_price_history(symbol, market, start=start, end=end)
        for row in sym_rows:
            row.update(_price_features_as_of(frame, pd.Timestamp(row["buy_dt"])))


def _compute_features(
    roundtrips: list[dict[str, Any]],
    trades_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute a features row per profitable roundtrip.

    Columns: symbol, market, holding_days, pnl, pnl_pct, entry_hour,
    entry_weekday, buy_dt, sell_dt, plus price-context features (entry_rsi14,
    prior_5d_return) read as-of buy_dt — NaN when price data is unavailable.
    """
    market_by_symbol = (
        trades_df.drop_duplicates("symbol").set_index("symbol")["market"].to_dict()
    )
    rows: list[dict[str, Any]] = []
    for rt in roundtrips:
        buy_dt = pd.Timestamp(rt["buy_dt"])
        sell_dt = pd.Timestamp(rt["sell_dt"])
        rows.append({
            "symbol": rt["symbol"],
            "market": market_by_symbol.get(rt["symbol"], "other"),
            "holding_days": float(rt["hold_days"]),
            "pnl": float(rt["pnl"]),
            "pnl_pct": float(rt["pnl_pct"]),
            "entry_hour": int(buy_dt.hour),
            "entry_weekday": int(buy_dt.weekday()),
            "buy_dt": buy_dt,
            "sell_dt": sell_dt,
        })
    _attach_price_features(rows)
    return pd.DataFrame(rows)


# ---------------- Cluster + decision-tree rule extraction ----------------

def _promoted_numeric_features(
    features_df: pd.DataFrame,
    *,
    min_support: int,
) -> tuple[str, ...]:
    """Return the numeric feature set used for clustering.

    Always includes the journal-derived ``_NUMERIC_FEATURES``. A price feature
    joins only when it is present (non-NaN) for at least ``min_support`` rows —
    too-sparse price features are excluded so clustering behaves exactly as the
    journal-only baseline when price data is largely unavailable.
    """
    promoted = list(_NUMERIC_FEATURES)
    for name in _PRICE_FEATURES:
        if name in features_df.columns and features_df[name].notna().sum() >= min_support:
            promoted.append(name)
    return tuple(promoted)


def _extract_rules(
    features_df: pd.DataFrame,
    *,
    min_support: int,
    max_rules: int,
    llm_translator: Any | None,
) -> list[ShadowRule]:
    """Cluster profitable roundtrips, derive one rule per dense cluster."""
    available_price_features = tuple(
        f for f in _PRICE_FEATURES if f in features_df.columns
    )
    if len(features_df) < min_support:
        return [
            _heuristic_single_rule(
                features_df,
                min_support,
                llm_translator,
                price_features=available_price_features,
            )
        ]

    numeric_features = _promoted_numeric_features(features_df, min_support=min_support)
    promoted_price_features = tuple(
        f for f in numeric_features if f in _PRICE_FEATURES
    )
    cluster_labels = _auto_cluster(
        features_df, max_k=min(max_rules, 5), numeric_features=numeric_features,
    )
    rules: list[ShadowRule] = []
    total_profitable = len(features_df)
    used_markets: set[str] = set()

    for cluster_id in sorted(set(cluster_labels)):
        cluster_mask = cluster_labels == cluster_id
        cluster_df = features_df[cluster_mask]
        if len(cluster_df) < min_support:
            continue
        rule = _cluster_to_rule(
            cluster_df=cluster_df,
            rule_index=len(rules) + 1,
            total_profitable=total_profitable,
            llm_translator=llm_translator,
            price_features=promoted_price_features,
        )
        # Deduplicate near-identical rules (same market + same holding band)
        key = (rule.entry_condition.get("market"), rule.holding_days_range)
        if key in used_markets:
            continue
        used_markets.add(key)
        rules.append(rule)
        if len(rules) >= max_rules:
            break

    if not rules:
        rules = [
            _heuristic_single_rule(
                features_df,
                min_support,
                llm_translator,
                price_features=promoted_price_features,
            )
        ]
    return rules


def _auto_cluster(
    features_df: pd.DataFrame,
    *,
    max_k: int,
    numeric_features: tuple[str, ...] = _NUMERIC_FEATURES,
) -> np.ndarray:
    """Pick a cluster count via simple silhouette heuristic (fallback k=2).

    Uses the supplied numeric features; scales by z-score to avoid any single
    feature dominating. Promoted price features may carry NaNs for rows whose
    price data was unavailable; those are median-imputed so the KMeans input is
    complete and stays row-aligned with ``features_df`` (StandardScaler/KMeans
    reject NaN). Imputation only affects *grouping* — ``_cluster_to_rule`` never
    reads price features — so a neutral median cannot distort rule bounds.
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    numeric_df = features_df[list(numeric_features)].astype(float)
    numeric_df = numeric_df.fillna(numeric_df.median(numeric_only=True))
    # A feature that is all-NaN stays NaN after median fill — drop such columns.
    numeric_df = numeric_df.dropna(axis=1, how="all")
    numeric = numeric_df.to_numpy()
    if len(numeric) <= 2 or max_k < 2 or numeric.shape[1] == 0:
        return np.zeros(len(numeric), dtype=int)
    scaled = StandardScaler().fit_transform(numeric)

    best_k, best_score = 2, -1.0
    try:
        from sklearn.metrics import silhouette_score
        for k in range(2, min(max_k, len(numeric) - 1) + 1):
            labels = KMeans(n_clusters=k, n_init=5, random_state=42).fit_predict(scaled)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(scaled, labels)
            if score > best_score:
                best_k, best_score = k, score
    except Exception as exc:  # pragma: no cover — sklearn edge cases
        logger.debug("silhouette selection failed, fallback k=2: %s", exc)

    return KMeans(n_clusters=best_k, n_init=5, random_state=42).fit_predict(scaled)


def _cluster_to_rule(
    *,
    cluster_df: pd.DataFrame,
    rule_index: int,
    total_profitable: int,
    llm_translator: Any | None,
    price_features: tuple[str, ...] = (),
) -> ShadowRule:
    """Summarize a cluster as one ShadowRule.

    Entry condition uses p10–p90 numeric bounds + dominant market. This is
    lighter than a decision tree and stays interpretable with tiny samples;
    we can swap to DecisionTreeClassifier in v2 when features widen.
    """
    market = _dominant(cluster_df["market"])
    hold_days = cluster_df["holding_days"]
    hold_lo = max(1, int(round(float(hold_days.quantile(0.10)))))
    hold_hi = max(hold_lo, int(round(float(hold_days.quantile(0.90)))))
    hours = cluster_df["entry_hour"]
    hour_lo = int(round(float(hours.quantile(0.10))))
    hour_hi = int(round(float(hours.quantile(0.90))))

    entry_condition: dict[str, Any] = {
        "market": market,
        "entry_hour": {"min": hour_lo, "max": hour_hi},
    }
    for feature in price_features:
        if feature in cluster_df.columns:
            series = cluster_df[feature].dropna()
            if len(series) >= 2:
                # 4 decimals: RSI bounds tolerate it and return-type features
                # (prior_5d_return ~ ±0.0x) would lose meaningful precision at 2.
                lo = float(round(series.quantile(0.10), 4))
                hi = float(round(series.quantile(0.90), 4))
                entry_condition[feature] = {"min": lo, "max": hi}
    exit_condition: dict[str, Any] = {
        "holding_days": {"min": hold_lo, "max": hold_hi},
    }

    samples = tuple(
        f"{row.symbol}@{pd.Timestamp(row.buy_dt).date().isoformat()}"
        for row in cluster_df.head(3).itertuples(index=False)
    )
    support = int(len(cluster_df))
    coverage = round(support / max(total_profitable, 1), 3)

    human = _translate_rule(
        entry_condition=entry_condition,
        exit_condition=exit_condition,
        holding_range=(hold_lo, hold_hi),
        translator=llm_translator,
    )

    return ShadowRule(
        rule_id=f"R{rule_index}",
        human_text=human,
        entry_condition=entry_condition,
        exit_condition=exit_condition,
        holding_days_range=(hold_lo, hold_hi),
        support_count=support,
        coverage_rate=coverage,
        sample_trades=samples,
    )


def _heuristic_single_rule(
    features_df: pd.DataFrame,
    min_support: int,
    llm_translator: Any | None,
    *,
    price_features: tuple[str, ...] = (),
) -> ShadowRule:
    """Degenerate fallback when clustering/tree yield nothing usable.

    Forwards ``price_features`` so the single-rule path carries the same
    RSI/return bounds as the multi-cluster path; ``_cluster_to_rule`` already
    guards on column presence and ``len(series) >= 2``, so sparse data simply
    yields a behavior-only rule.
    """
    return _cluster_to_rule(
        cluster_df=features_df,
        rule_index=1,
        total_profitable=max(len(features_df), min_support),
        llm_translator=llm_translator,
        price_features=price_features,
    )


# ---------------- Natural-language translation ----------------

_MARKET_LABELS = {
    "china_a": "China A-share",
    "us": "US equity",
    "hk": "HK equity",
    "crypto": "Crypto",
    "other": "Other",
}

RULE_TEXT_MAX = 80


def _translate_rule(
    *,
    entry_condition: dict[str, Any],
    exit_condition: dict[str, Any],
    holding_range: tuple[int, int],
    translator: Any | None,
) -> str:
    """Turn a structured rule dict into a concise English sentence (<=80 chars)."""
    if translator is not None:
        try:
            text = translator({
                "entry_condition": entry_condition,
                "exit_condition": exit_condition,
                "holding_range": holding_range,
            })
            if isinstance(text, str) and text.strip():
                return text.strip()[:RULE_TEXT_MAX]
        except Exception as exc:  # pragma: no cover — LLM failure, fallback
            logger.warning("LLM rule translator failed, falling back: %s", exc)

    market_label = _MARKET_LABELS.get(entry_condition.get("market", "other"), "Other")
    hour_range = entry_condition.get("entry_hour", {})
    hour_text = ""
    if hour_range:
        lo, hi = hour_range.get("min"), hour_range.get("max")
        hour_text = f" at {lo}:00" if lo == hi else f" between {lo}:00-{hi}:00"
    hold_lo, hold_hi = holding_range
    hold_text = f"hold {hold_lo}-{hold_hi}d" if hold_lo != hold_hi else f"hold {hold_lo}d"
    entry_text = f"Enter {market_label}{hour_text}"
    return f"{entry_text}, {hold_text}"[:RULE_TEXT_MAX]


# ---------------- Utilities ----------------

def _dominant(series: pd.Series) -> str:
    """Most frequent value in a series, or the first if tied."""
    if series.empty:
        return "other"
    return str(series.value_counts().idxmax())


def _render_profile_text(
    *,
    total_profitable: int,
    total_all: int,
    typical_holding: tuple[float, float],
    source_market: str,
    preferred_markets: tuple[str, ...],
) -> str:
    """Build the Section 1 one-paragraph portrait (English)."""
    median, p75 = typical_holding
    markets_label = ", ".join(_MARKET_LABELS.get(m, m) for m in preferred_markets[:3])
    source_label = _MARKET_LABELS.get(source_market, source_market)
    return (
        f"{total_profitable} of your {total_all} closed roundtrips were profitable. "
        f"Primary market: {source_label} (also active in {markets_label}). "
        f"Median holding period {median:.1f}d; most positions closed within {p75:.1f}d."
    )
