"""RSSHub event/sentiment provider with point-in-time safeguards.

A news / announcement / sentiment provider that runs parallel to the Tushare
fundamental layer (:mod:`backtest.loaders.tushare_fundamentals`). It pulls feeds
from a self-hosted `RSSHub <https://docs.rsshub.app>`_ instance, normalises each
item into the ``event-driven`` skill schema (``date, event_type, score, source,
summary``), and attaches a point-in-time-safe ``event_score`` column to daily
price frames.

Point-in-time discipline (mirrors the fundamentals enricher): every item is
stamped with a *knowable date* — the date a backtest could first have acted on
it (items published after the close roll to the next session) — and only items
with ``knowable_date <= as_of`` are ever returned. No feed item can leak into a
bar dated before it became knowable.

Scoring is pluggable. A deterministic, dependency-free lexicon scorer is used by
default; callers may pass any ``scorer(title, summary) -> float`` (e.g. an LLM
judge, as the ``event-driven`` skill describes) to override it.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Iterable, Mapping
from xml.etree.ElementTree import ParseError

import numpy as np
import pandas as pd
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from backtest.loaders.base import positive_env_float, retry_with_budget

logger = logging.getLogger(__name__)

RSSHUB_BASE_URL_ENV = "RSSHUB_BASE_URL"
RSSHUB_BASE_URL_PLACEHOLDERS = {"", "https://rsshub.example.com"}
RSSHUB_TIMEOUT_ENV = "RSSHUB_TIMEOUT_S"
RSSHUB_BUDGET_ENV = "RSSHUB_FETCH_BUDGET_S"
DEFAULT_TIMEOUT_S = 15.0
DEFAULT_BUDGET_S = 60.0

#: Hour (local to the feed timestamps) at/after which a publication is treated as
#: knowable only on the next calendar day, matching the event-driven skill's
#: "released after market close -> use the next trading day" rule.
DEFAULT_CLOSE_CUTOFF_HOUR = 16

#: Canonical column order for the tidy event frame.
EVENT_COLUMNS: tuple[str, ...] = (
    "ts_code",
    "knowable_date",
    "event_type",
    "score",
    "source",
    "summary",
)

ScorerFn = Callable[[str, str], float]


class EventProviderError(Exception):
    """Base error for event-provider failures."""


class UnknownFeedError(EventProviderError):
    """Raised when a requested feed name is not registered."""


#: Supported ``code_style`` values for per-symbol routes.
CODE_STYLES: frozenset[str] = frozenset({"raw", "exchange_prefix", "bare"})


def format_code_for_route(code: str, style: str) -> str:
    """Convert a backtest code (e.g. ``"600519.SH"``) to a route's expected form.

    RSSHub routes disagree on instrument formatting: some take the exchange-
    prefixed form (``SH600519``, e.g. xueqiu), some the bare number (``600519``),
    some a vendor-specific string. The backtest engine always passes the dotted
    ``"600519.SH"`` form, so a feed declares the shape its route needs.

    Args:
        code: Dotted instrument code (``"600519.SH"``); passed through if it has
            no ``.`` suffix.
        style: One of :data:`CODE_STYLES` — ``"raw"`` (unchanged), ``"bare"``
            (symbol only, ``"600519"``), or ``"exchange_prefix"`` (``"SH600519"``).

    Returns:
        The code formatted for the route.

    Raises:
        ValueError: If ``style`` is not a recognised code style.
    """
    if style not in CODE_STYLES:
        raise ValueError(f"Unknown code_style {style!r}; expected one of {sorted(CODE_STYLES)}")
    if style == "raw":
        return code
    symbol, _, suffix = code.partition(".")
    if style == "bare":
        return symbol
    return f"{suffix.upper()}{symbol}" if suffix else symbol


@dataclass(frozen=True)
class FeedSpec:
    """Machine-readable metadata for one RSSHub feed route.

    Attributes:
        name: Stable feed identifier used in configs (e.g. ``"sina_announcements"``).
        route_template: RSSHub route with a ``{code}`` placeholder, joined to the
            base URL (e.g. ``"/sina/announcement/{code}"``). Routes without a
            ``{code}`` placeholder are treated as market-wide feeds.
        event_type: Event class emitted for items from this feed; one of the
            event-driven taxonomy (``earnings``/``macro``/``policy``/
            ``sentiment``/``insider``/``technical_break``).
        code_style: How the dotted backtest code is rewritten before it is
            substituted into a per-symbol ``route_template`` — one of
            :data:`CODE_STYLES`. Ignored for market-wide routes.
    """

    name: str
    route_template: str
    event_type: str
    code_style: str = "raw"

    def __post_init__(self) -> None:
        if self.code_style not in CODE_STYLES:
            raise ValueError(
                f"FeedSpec {self.name!r}: unknown code_style {self.code_style!r}; "
                f"expected one of {sorted(CODE_STYLES)}"
            )

    @property
    def is_per_symbol(self) -> bool:
        """Whether the route is parameterised by instrument code."""
        return "{code}" in self.route_template


def feed_specs_from_config(entries: Iterable[Mapping[str, Any]]) -> list[FeedSpec]:
    """Build :class:`FeedSpec` objects from backtest-config dicts.

    Each entry must carry ``name``, ``route_template`` and ``event_type``; an
    optional ``code_style`` defaults to ``"raw"``. There is intentionally no
    built-in feed catalogue — routes evolve and silently rot, so feeds are always
    declared explicitly in config (or passed to the provider constructor).

    Args:
        entries: Iterable of mapping objects, one per feed.

    Returns:
        Parsed feed specs.

    Raises:
        ValueError: If an entry is missing a required key or has a duplicate name.
    """
    specs: list[FeedSpec] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("each event feed must be a mapping with name/route_template/event_type")
        missing = [k for k in ("name", "route_template", "event_type") if not str(entry.get(k, "")).strip()]
        if missing:
            raise ValueError(f"event feed is missing required field(s): {', '.join(missing)}")
        name = str(entry["name"]).strip()
        if name in seen:
            raise ValueError(f"duplicate event feed name: {name!r}")
        seen.add(name)
        specs.append(
            FeedSpec(
                name=name,
                route_template=str(entry["route_template"]).strip(),
                event_type=str(entry["event_type"]).strip(),
                code_style=str(entry.get("code_style", "raw")).strip() or "raw",
            )
        )
    return specs


#: No built-in feed catalogue: RSSHub routes change and break, so feeds are always
#: supplied explicitly (via config ``event_feeds`` or the provider constructor).
DEFAULT_FEEDS: tuple[FeedSpec, ...] = ()

# ── Default dependency-free lexicon scorer ───────────────────────────────────

_POSITIVE_TERMS: frozenset[str] = frozenset(
    {
        "beat",
        "beats",
        "surge",
        "surges",
        "soar",
        "record",
        "growth",
        "profit",
        "upgrade",
        "upgraded",
        "outperform",
        "bullish",
        "approval",
        "approved",
        "win",
        "wins",
        "buyback",
        "dividend",
        "expansion",
        "breakthrough",
    }
)
_NEGATIVE_TERMS: frozenset[str] = frozenset(
    {
        "miss",
        "misses",
        "plunge",
        "plunges",
        "fall",
        "falls",
        "loss",
        "losses",
        "downgrade",
        "downgraded",
        "underperform",
        "bearish",
        "fraud",
        "probe",
        "lawsuit",
        "recall",
        "default",
        "bankruptcy",
        "halt",
        "warning",
        "decline",
    }
)


def default_lexicon_scorer(title: str, summary: str) -> float:
    """Score text in ``[-1, 1]`` by net positive/negative term frequency.

    A deterministic, dependency-free baseline. It is intentionally simple — the
    provider is the data layer; richer scoring (e.g. an LLM judge) is plugged in
    via the ``scorer`` argument on :meth:`RSSHubEventProvider.query_events`.

    Args:
        title: Item headline.
        summary: Item summary/description (may be empty).

    Returns:
        Sentiment score in ``[-1.0, 1.0]``; ``0.0`` when no terms match.
    """
    tokens = f"{title} {summary}".lower().replace("/", " ").split()
    if not tokens:
        return 0.0
    pos = sum(1 for tok in tokens if tok.strip(".,;:!?\"'()") in _POSITIVE_TERMS)
    neg = sum(1 for tok in tokens if tok.strip(".,;:!?\"'()") in _NEGATIVE_TERMS)
    hits = pos + neg
    if hits == 0:
        return 0.0
    return max(-1.0, min(1.0, (pos - neg) / hits))


def _knowable_date(published: pd.Timestamp, cutoff_hour: int) -> pd.Timestamp:
    """Return the date an item becomes actionable (post-cutoff rolls to next day).

    Args:
        published: Parsed publication timestamp (tz dropped to naive local).
        cutoff_hour: Hour at/after which publication rolls to the next day.

    Returns:
        Normalised (midnight) timestamp of the knowable date.
    """
    stamp = published.tz_localize(None) if published.tzinfo is not None else published
    base = stamp.normalize()
    if stamp.hour >= cutoff_hour:
        base = base + pd.Timedelta(days=1)
    return base


def _clean_summary(text: str | None) -> str:
    """Collapse whitespace and strip commas so the value is CSV-safe."""
    if not text:
        return ""
    return " ".join(text.replace(",", " ").split())


class RSSHubEventProvider:
    """Point-in-time-safe event/sentiment provider backed by RSSHub.

    Attributes:
        base_url: Root of the RSSHub instance (no trailing slash).
        feeds: Registered feed specs keyed by name.
        close_cutoff_hour: Hour after which items roll to the next knowable day.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        feeds: Iterable[FeedSpec] | None = None,
        client: Any | None = None,
        close_cutoff_hour: int = DEFAULT_CLOSE_CUTOFF_HOUR,
    ) -> None:
        """Initialise the provider.

        Args:
            base_url: RSSHub root URL; defaults to ``$RSSHUB_BASE_URL``.
            feeds: Feed specs to register; defaults to :data:`DEFAULT_FEEDS`.
            client: Optional injected HTTP client exposing ``get(url, timeout=...)``
                that returns an object with ``.text`` and ``.raise_for_status()``
                (an ``httpx.Client``-like). Injectable for offline testing.
            close_cutoff_hour: Knowable-date roll cutoff (0-23).
        """
        resolved = (base_url if base_url is not None else os.getenv(RSSHUB_BASE_URL_ENV, "")).strip()
        self.base_url = resolved.rstrip("/")
        specs = tuple(feeds) if feeds is not None else DEFAULT_FEEDS
        self.feeds: dict[str, FeedSpec] = {spec.name: spec for spec in specs}
        self.close_cutoff_hour = close_cutoff_hour
        self._client = client

    def is_available(self) -> bool:
        """Whether a usable RSSHub base URL is configured."""
        return self.base_url not in {p.rstrip("/") for p in RSSHUB_BASE_URL_PLACEHOLDERS}

    def list_feeds(self) -> list[str]:
        """Return registered feed names in stable order."""
        return sorted(self.feeds)

    def describe_feed(self, feed: str) -> FeedSpec:
        """Return the spec for a registered feed.

        Raises:
            UnknownFeedError: If ``feed`` is not registered.
        """
        try:
            return self.feeds[feed]
        except KeyError as exc:
            raise UnknownFeedError(f"Unknown RSSHub feed: {feed}") from exc

    def query_events(
        self,
        codes: Iterable[str],
        *,
        as_of: str | pd.Timestamp,
        feeds: Iterable[str] | None = None,
        scorer: ScorerFn | None = None,
    ) -> pd.DataFrame:
        """Fetch and normalise feed items, dropping anything not yet knowable.

        Args:
            codes: Instrument codes to query.
            as_of: Point-in-time boundary; items with ``knowable_date > as_of``
                are excluded (no look-ahead).
            feeds: Feed names to query; defaults to all registered feeds.
            scorer: Optional ``scorer(title, summary) -> float`` override;
                defaults to :func:`default_lexicon_scorer`.

        Returns:
            Tidy frame with :data:`EVENT_COLUMNS`, sorted by
            ``(ts_code, knowable_date)`` and de-duplicated.
        """
        score_fn = scorer or default_lexicon_scorer
        feed_names = list(feeds) if feeds is not None else self.list_feeds()
        as_of_date = pd.Timestamp(as_of).normalize()

        code_list = list(codes)
        rows: list[dict[str, Any]] = []
        attempted = 0
        failed = 0
        for feed_name in feed_names:
            spec = self.describe_feed(feed_name)
            for code in code_list:
                attempted += 1
                xml_text = self._fetch_feed(spec, code)
                if not xml_text:
                    failed += 1
                    continue
                rows.extend(self._parse_items(xml_text, code, spec, score_fn))

        # A configured-but-fully-unreachable provider must fail loudly rather than
        # silently scoring every bar 0.0 (which reads as "sentiment considered, no
        # signal"). A reachable feed that simply returned no items is legitimate.
        if attempted and failed == attempted:
            raise EventProviderError(
                f"All {attempted} RSSHub feed fetch(es) failed for base_url "
                f"{self.base_url!r}; verify the instance is reachable and the "
                f"configured routes exist (feeds={feed_names})"
            )

        if not rows:
            return pd.DataFrame(columns=EVENT_COLUMNS)

        frame = pd.DataFrame(rows, columns=list(EVENT_COLUMNS))
        frame = frame[frame["knowable_date"] <= as_of_date]
        frame = frame.drop_duplicates(subset=["ts_code", "knowable_date", "event_type", "summary"])
        frame = frame.sort_values(["ts_code", "knowable_date"]).reset_index(drop=True)
        return frame

    def _fetch_feed(self, spec: FeedSpec, code: str) -> str:
        """Fetch raw RSS XML for one feed/code, bounded by a wall-clock budget.

        Returns the response body on success, or ``""`` when the fetch could not
        complete within the budget — the caller logs and counts that as a failed
        feed so an all-feeds-unreachable run can be surfaced loudly.
        """
        if spec.is_per_symbol:
            route = spec.route_template.format(code=format_code_for_route(code, spec.code_style))
        else:
            route = spec.route_template
        url = f"{self.base_url}{route}"
        timeout = positive_env_float(RSSHUB_TIMEOUT_ENV, DEFAULT_TIMEOUT_S)
        budget = positive_env_float(RSSHUB_BUDGET_ENV, DEFAULT_BUDGET_S)
        client = self._client or self._default_client()
        deadline = time.monotonic() + budget

        def _do() -> str:
            response = client.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text

        try:
            return retry_with_budget(
                _do,
                transient=Exception,
                deadline=deadline,
                label=f"rsshub fetch {spec.name} for {code}",
            )
        except TimeoutError:
            logger.warning(
                "RSSHub feed %r for %s unreachable within %.0fs budget (%s); "
                "no items contributed from this feed",
                spec.name,
                code,
                budget,
                url,
            )
            return ""

    @staticmethod
    def _default_client() -> Any:
        """Construct a default httpx client (imported lazily)."""
        import httpx

        return httpx.Client(follow_redirects=True)

    def _parse_items(
        self,
        xml_text: str,
        code: str,
        spec: FeedSpec,
        score_fn: ScorerFn,
    ) -> list[dict[str, Any]]:
        """Parse RSS 2.0 ``<item>`` nodes into normalised event rows.

        Uses ``defusedxml`` to neutralise XXE / entity-expansion attacks in the
        untrusted feed payload; malformed or hostile XML yields no rows.
        """
        try:
            root = ET.fromstring(xml_text)
        except (ParseError, DefusedXmlException):
            return []

        rows: list[dict[str, Any]] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            summary = _clean_summary(item.findtext("description"))
            pub_raw = item.findtext("pubDate")
            published = _parse_pubdate(pub_raw)
            if published is None:
                continue
            rows.append(
                {
                    "ts_code": code,
                    "knowable_date": _knowable_date(published, self.close_cutoff_hour),
                    "event_type": spec.event_type,
                    "score": float(score_fn(title, summary)),
                    "source": spec.name,
                    "summary": summary or title,
                }
            )
        return rows


def _parse_pubdate(value: str | None) -> pd.Timestamp | None:
    """Parse an RFC-822 (RSS) or ISO ``pubDate`` into a Timestamp, or None."""
    if not value or not value.strip():
        return None
    try:
        return pd.Timestamp(parsedate_to_datetime(value))
    except (TypeError, ValueError):
        pass
    try:
        return pd.Timestamp(value)
    except (TypeError, ValueError):
        return None


def enrich_price_frames_with_events(
    data_map: dict[str, pd.DataFrame],
    provider: RSSHubEventProvider,
    *,
    as_of: str | pd.Timestamp,
    feeds: Iterable[str] | None = None,
    decay_lambda: float = 0.1,
    lookback: int = 30,
    min_abs_score: float = 0.0,
    scorer: ScorerFn | None = None,
) -> dict[str, pd.DataFrame]:
    """Attach a point-in-time-safe ``event_score`` column to price frames.

    For each bar ``t`` the score aggregates only events whose ``knowable_date``
    falls in ``(t - lookback, t]``, exponentially decayed by age — the same
    formula as the ``event-driven`` skill — so no future item can influence an
    earlier bar. Two columns are added: ``event_score`` (decayed sum, clipped to
    ``[-1, 1]``) and ``event_count`` (events in the window).

    Args:
        data_map: Mapping ``{code: OHLCV DataFrame}`` (DatetimeIndex).
        provider: Configured :class:`RSSHubEventProvider`.
        as_of: Point-in-time boundary passed through to the provider.
        feeds: Feed names to query; defaults to all registered feeds.
        decay_lambda: Exponential decay per day (higher decays faster).
        lookback: Window in days; older events are excluded.
        min_abs_score: Drop events with ``|score|`` below this threshold.
        scorer: Optional scoring override forwarded to the provider.

    Returns:
        A new mapping with the same frames plus ``event_score``/``event_count``.
    """
    if not data_map:
        return data_map

    codes = list(data_map)
    events = provider.query_events(codes, as_of=as_of, feeds=feeds, scorer=scorer)
    enriched = {code: frame.copy() for code, frame in data_map.items()}
    if events.empty:
        for frame in enriched.values():
            frame["event_score"] = 0.0
            frame["event_count"] = 0
        return enriched

    if min_abs_score > 0.0:
        events = events[events["score"].abs() >= min_abs_score]

    for code, frame in enriched.items():
        rows = events[events["ts_code"] == code]
        bar_dates = pd.DatetimeIndex(pd.to_datetime(frame.index)).normalize()
        scores = pd.Series(0.0, index=frame.index)
        counts = pd.Series(0, index=frame.index)
        if not rows.empty and len(frame) > 0:
            ev_dates = rows["knowable_date"].to_numpy(dtype="datetime64[ns]")
            ev_scores = rows["score"].to_numpy(dtype=float)
            window = np.timedelta64(lookback, "D")
            for pos, bar in enumerate(bar_dates):
                bar64 = np.datetime64(bar, "ns")
                mask = (ev_dates <= bar64) & (ev_dates > bar64 - window)
                if not mask.any():
                    continue
                ages = (bar64 - ev_dates[mask]) / np.timedelta64(1, "D")
                decayed = float((ev_scores[mask] * np.exp(-decay_lambda * ages)).sum())
                scores.iloc[pos] = max(-1.0, min(1.0, decayed))
                counts.iloc[pos] = int(mask.sum())
        frame["event_score"] = scores
        frame["event_count"] = counts
    return enriched
