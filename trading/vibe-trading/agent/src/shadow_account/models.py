"""Shadow Account data contracts (frozen dataclasses).

See `docs/shadow-account-spec.md` for the full contract. These types are the
stable boundary between extractor / codegen / backtester / reporter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

#: Deterministic price-context feature names shared across the pipeline.
#: The extractor computes these as-of ``buy_dt``, codegen flattens their
#: ``{min,max}`` bounds into the template, and the scanner evaluates them in
#: real time. Defining the names here — on the stable data-contract boundary —
#: keeps the three modules from drifting apart.
PRICE_FEATURES: tuple[str, ...] = ("entry_rsi14", "prior_5d_return")


@dataclass(frozen=True)
class ShadowRule:
    """One human-readable if-then rule distilled from profitable roundtrips.

    Attributes:
        rule_id: Stable ID like "R1", "R2".
        human_text: Chinese natural-language description (<=30 chars).
        entry_condition: Structured condition dict for codegen. Keys are
            feature names (e.g. "prior_5d_return", "market"); values are
            either scalars or (op, value) tuples (e.g. ("<=", -0.08)).
        exit_condition: Structured exit condition dict.
        holding_days_range: (min, max) integer days.
        support_count: Number of profitable roundtrips supporting this rule.
        coverage_rate: Fraction of all profitable roundtrips this rule covers.
        sample_trades: Representative "<symbol>@<date>" strings.
        weight: Signal weight for codegen (default 1.0).
    """

    rule_id: str
    human_text: str
    entry_condition: dict[str, Any]
    exit_condition: dict[str, Any]
    holding_days_range: tuple[int, int]
    support_count: int
    coverage_rate: float
    sample_trades: tuple[str, ...]
    weight: float = 1.0


@dataclass(frozen=True)
class ShadowProfile:
    """User's extracted trading shadow.

    Attributes:
        shadow_id: "shadow_<8-hex>" unique ID.
        created_at: ISO8601 UTC timestamp.
        journal_hash: SHA1 of the source journal content for idempotency.
        source_market: Primary market from the journal ("china_a" etc.).
        profitable_roundtrips: Number of roundtrips used for extraction.
        total_roundtrips: Total roundtrips in journal.
        date_range: (start_iso, end_iso) of the journal.
        profile_text: One-paragraph Chinese portrait for Section 1.
        rules: Tuple of 3-5 ShadowRule.
        preferred_markets: Markets the user actually traded, frequency-sorted.
        typical_holding_days: (median, p75) in days.
    """

    shadow_id: str
    created_at: str
    journal_hash: str
    source_market: str
    profitable_roundtrips: int
    total_roundtrips: int
    date_range: tuple[str, str]
    profile_text: str
    rules: tuple[ShadowRule, ...]
    preferred_markets: tuple[str, ...]
    typical_holding_days: tuple[float, float]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-safe dict."""
        return asdict(self)


@dataclass(frozen=True)
class AttributionBreakdown:
    """Delta PnL attribution between user's realized trades and shadow.

    All PnL fields are in the journal's account currency.
    """

    missed_signals_pnl: float
    noise_trades_pnl: float
    early_exit_pnl: float
    late_exit_pnl: float
    overtrading_pnl: float
    counterfactual_trades: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ShadowBacktestResult:
    """Output of multi-market shadow backtest + attribution."""

    shadow_id: str
    per_market: dict[str, dict[str, float]]
    combined: dict[str, float]
    equity_curves: dict[str, list[tuple[str, float]]]
    attribution: AttributionBreakdown
    shadow_total_pnl: float
    real_total_pnl: float
    delta_pnl: float
