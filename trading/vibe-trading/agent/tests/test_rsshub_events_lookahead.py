"""No-look-ahead guarantee for RSSHub event enrichment.

Echoes the discipline of ``agent/tests/factors/test_lookahead.py``: corrupting
the future must not change the present. Here, adding a future-dated event must
not alter ``event_score`` on any earlier bar.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from backtest.loaders.rsshub_events import EVENT_COLUMNS, enrich_price_frames_with_events


class _StubProvider:
    """Returns a fixed event frame verbatim (ignores ``as_of``).

    Ignoring ``as_of`` is deliberate: it forces the *enricher's* per-bar masking
    to be the only thing standing between a future event and an earlier bar.
    """

    def __init__(self, events: pd.DataFrame) -> None:
        self._events = events

    def query_events(self, codes: Iterable[str], *, as_of, feeds=None, scorer=None) -> pd.DataFrame:
        return self._events[self._events["ts_code"].isin(list(codes))].copy()


def _events(rows: list[tuple[str, str, str, float, str, str]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=list(EVENT_COLUMNS))
    frame["knowable_date"] = pd.to_datetime(frame["knowable_date"])
    return frame


def _price_frame() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", "2024-01-31")
    n = len(dates)
    return pd.DataFrame(
        {
            "open": np.linspace(10, 20, n),
            "high": np.linspace(11, 21, n),
            "low": np.linspace(9, 19, n),
            "close": np.linspace(10, 20, n),
            "volume": np.full(n, 1e6),
        },
        index=dates,
    )


def test_future_event_does_not_leak_into_earlier_bars() -> None:
    data_map = {"AAA": _price_frame()}
    probe = pd.Timestamp("2024-01-15")

    past = _events([("AAA", "2024-01-10", "sentiment", 0.8, "news", "good")])
    past_plus_future = _events(
        [
            ("AAA", "2024-01-10", "sentiment", 0.8, "news", "good"),
            ("AAA", "2024-01-25", "sentiment", -1.0, "news", "bad future"),
        ]
    )

    base = enrich_price_frames_with_events({"AAA": _price_frame()}, _StubProvider(past), as_of=probe)
    poisoned = enrich_price_frames_with_events(
        {"AAA": _price_frame()}, _StubProvider(past_plus_future), as_of=probe
    )

    # The future (2024-01-25) event must not move the score at 2024-01-15.
    assert base["AAA"].loc[probe, "event_score"] == poisoned["AAA"].loc[probe, "event_score"]
    assert base["AAA"].loc[probe, "event_score"] > 0  # the past event does register

    # Sanity: the future event DOES register once the bar reaches it.
    late = pd.Timestamp("2024-01-26")
    assert poisoned["AAA"].loc[late, "event_score"] < base["AAA"].loc[late, "event_score"]
    assert data_map  # frame fixture used


def test_decay_is_monotonic_with_age() -> None:
    events = _events([("AAA", "2024-01-02", "sentiment", 1.0, "news", "one shot")])
    enriched = enrich_price_frames_with_events(
        {"AAA": _price_frame()}, _StubProvider(events), as_of="2024-01-31", lookback=60
    )
    score = enriched["AAA"]["event_score"]
    active = score[score > 0]
    assert active.is_monotonic_decreasing  # single event decays as bars age away


def test_empty_events_yield_zero_columns() -> None:
    empty = _events([])
    enriched = enrich_price_frames_with_events(
        {"AAA": _price_frame()}, _StubProvider(empty), as_of="2024-01-31"
    )
    assert (enriched["AAA"]["event_score"] == 0.0).all()
    assert (enriched["AAA"]["event_count"] == 0).all()
