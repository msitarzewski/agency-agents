"""Unit tests for the RSSHub event/sentiment provider (no network)."""

from __future__ import annotations

import pandas as pd
import pytest

from backtest.loaders.rsshub_events import (
    DEFAULT_FEEDS,
    DEFAULT_TIMEOUT_S,
    EVENT_COLUMNS,
    EventProviderError,
    FeedSpec,
    RSSHubEventProvider,
    UnknownFeedError,
    default_lexicon_scorer,
    feed_specs_from_config,
    format_code_for_route,
)

_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title>Company beats earnings</title>
    <description>Q4 revenue surges on strong demand</description>
    <pubDate>Mon, 15 Jan 2024 09:00:00 +0000</pubDate>
  </item>
  <item>
    <title>Regulator opens probe</title>
    <description>probe into accounting, shares plunge</description>
    <pubDate>Tue, 16 Jan 2024 18:30:00 +0000</pubDate>
  </item>
</channel></rss>"""

# A billion-laughs payload: must be neutralised by defusedxml, never expanded.
_HOSTILE = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<rss version="2.0"><channel><item><title>&lol3;</title>
<pubDate>Mon, 15 Jan 2024 09:00:00 +0000</pubDate></item></channel></rss>"""


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeClient:
    """Minimal httpx.Client stand-in returning a fixed payload."""

    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls: list[str] = []
        self.timeouts: list[float | None] = []

    def get(self, url: str, timeout: float | None = None) -> _FakeResponse:
        self.calls.append(url)
        self.timeouts.append(timeout)
        return _FakeResponse(self.payload)


def _provider(payload: str = _RSS) -> RSSHubEventProvider:
    return RSSHubEventProvider(
        "https://rsshub.local",
        feeds=[FeedSpec("news", "/stock/news/{code}", "sentiment")],
        client=_FakeClient(payload),
    )


def test_is_available_true_with_base_url() -> None:
    assert _provider().is_available() is True


@pytest.mark.parametrize("base", ["", "https://rsshub.example.com", "   "])
def test_is_available_false_without_real_base_url(base: str) -> None:
    assert RSSHubEventProvider(base, client=_FakeClient(_RSS)).is_available() is False


def test_query_events_schema_and_scoring() -> None:
    frame = _provider().query_events(["AAA"], as_of="2024-01-31")
    assert list(frame.columns) == list(EVENT_COLUMNS)
    assert set(frame["ts_code"]) == {"AAA"}
    assert (frame["event_type"] == "sentiment").all()

    by_summary = {row.summary: row.score for row in frame.itertuples()}
    bullish = next(s for t, s in by_summary.items() if "revenue" in t)
    bearish = next(s for t, s in by_summary.items() if "probe" in t)
    assert bullish > 0
    assert bearish < 0


def test_after_close_publication_rolls_to_next_day() -> None:
    frame = _provider().query_events(["AAA"], as_of="2024-01-31")
    dates = dict(zip(frame["summary"], frame["knowable_date"]))
    intraday = next(v for k, v in dates.items() if "revenue" in k)  # 09:00 -> same day
    after_close = next(v for k, v in dates.items() if "probe" in k)  # 18:30 -> next day
    assert intraday == pd.Timestamp("2024-01-15")
    assert after_close == pd.Timestamp("2024-01-17")


def test_point_in_time_filter_excludes_future_items() -> None:
    frame = _provider().query_events(["AAA"], as_of="2024-01-15")
    assert (frame["knowable_date"] <= pd.Timestamp("2024-01-15")).all()
    assert len(frame) == 1  # only the 09:00 item is knowable by the 15th


def test_duplicate_items_are_deduplicated() -> None:
    items = _RSS.split("<channel>")[1].split("</channel>")[0]
    doubled = f'<?xml version="1.0"?><rss version="2.0"><channel>{items}{items}</channel></rss>'
    frame = _provider(doubled).query_events(["AAA"], as_of="2024-01-31")
    assert len(frame) == 2  # 4 items in, 2 unique out
    assert frame.duplicated(subset=["ts_code", "knowable_date", "event_type", "summary"]).sum() == 0


def test_hostile_xml_is_neutralised() -> None:
    frame = _provider(_HOSTILE).query_events(["AAA"], as_of="2024-01-31")
    assert frame.empty


def test_unknown_feed_raises() -> None:
    with pytest.raises(UnknownFeedError):
        _provider().query_events(["AAA"], as_of="2024-01-31", feeds=["does_not_exist"])


def test_custom_scorer_override() -> None:
    frame = _provider().query_events(["AAA"], as_of="2024-01-31", scorer=lambda t, s: 0.5)
    assert (frame["score"] == 0.5).all()


def test_default_lexicon_scorer_bounds() -> None:
    assert default_lexicon_scorer("", "") == 0.0
    assert default_lexicon_scorer("neutral filler text", "") == 0.0
    assert -1.0 <= default_lexicon_scorer("loss plunge fraud", "") <= 0.0
    assert 0.0 <= default_lexicon_scorer("beat surge record", "") <= 1.0


# ── No-default-catalogue + per-symbol code formatting + loud failures ─────────


class _FailingClient:
    """Client whose every request raises a transient error."""

    def get(self, url: str, timeout: float | None = None) -> _FakeResponse:
        raise ConnectionError(f"unreachable: {url}")


def test_no_builtin_feed_catalogue() -> None:
    # Routes rot as RSSHub evolves, so feeds are always declared explicitly.
    assert DEFAULT_FEEDS == ()


@pytest.mark.parametrize(
    "code,style,expected",
    [
        ("600519.SH", "raw", "600519.SH"),
        ("600519.SH", "bare", "600519"),
        ("600519.SH", "exchange_prefix", "SH600519"),
        ("000001.SZ", "exchange_prefix", "SZ000001"),
        ("AAPL", "exchange_prefix", "AAPL"),  # no exchange suffix -> symbol only
    ],
)
def test_format_code_for_route(code: str, style: str, expected: str) -> None:
    assert format_code_for_route(code, style) == expected


def test_format_code_for_route_rejects_unknown_style() -> None:
    with pytest.raises(ValueError):
        format_code_for_route("600519.SH", "nope")


def test_feedspec_rejects_unknown_code_style() -> None:
    with pytest.raises(ValueError):
        FeedSpec("x", "/x/{code}", "earnings", code_style="bogus")


def test_per_symbol_route_applies_code_style() -> None:
    client = _FakeClient(_RSS)
    provider = RSSHubEventProvider(
        "https://rsshub.local",
        feeds=[FeedSpec("xq", "/xueqiu/stock/{code}", "earnings", code_style="exchange_prefix")],
        client=client,
    )
    provider.query_events(["600519.SH"], as_of="2024-01-31")
    assert client.calls == ["https://rsshub.local/xueqiu/stock/SH600519"]


def test_feed_specs_from_config_parses_and_validates() -> None:
    specs = feed_specs_from_config(
        [
            {"name": "a", "route_template": "/x/{code}", "event_type": "earnings"},
            {"name": "b", "route_template": "/y", "event_type": "macro", "code_style": "bare"},
        ]
    )
    assert [s.name for s in specs] == ["a", "b"]
    assert specs[1].code_style == "bare"
    assert specs[0].code_style == "raw"  # default


@pytest.mark.parametrize(
    "bad",
    [
        [{"name": "", "route_template": "/x", "event_type": "earnings"}],  # blank name
        [{"route_template": "/x", "event_type": "earnings"}],  # missing name
        [{"name": "a", "route_template": "/x"}],  # missing event_type
        [
            {"name": "a", "route_template": "/x", "event_type": "e"},
            {"name": "a", "route_template": "/y", "event_type": "e"},  # duplicate name
        ],
        ["not-a-mapping"],
    ],
)
def test_feed_specs_from_config_rejects_bad(bad: list) -> None:
    with pytest.raises(ValueError):
        feed_specs_from_config(bad)


def test_all_feeds_unreachable_raises(monkeypatch) -> None:
    # A configured-but-fully-unreachable provider must fail loudly, never score
    # every bar 0.0 silently. Zero budget makes the retry abort immediately.
    monkeypatch.setenv("RSSHUB_FETCH_BUDGET_S", "0")
    provider = RSSHubEventProvider(
        "https://rsshub.local",
        feeds=[FeedSpec("news", "/stock/news/{code}", "sentiment")],
        client=_FailingClient(),
    )
    with pytest.raises(EventProviderError):
        provider.query_events(["AAA"], as_of="2024-01-31")


def test_malformed_timeout_env_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RSSHUB_TIMEOUT_S", "not-a-float")
    client = _FakeClient(_RSS)
    provider = RSSHubEventProvider(
        "https://rsshub.local",
        feeds=[FeedSpec("news", "/stock/news/{code}", "sentiment")],
        client=client,
    )

    frame = provider.query_events(["AAA"], as_of="2024-01-31")

    assert not frame.empty
    assert client.timeouts == [DEFAULT_TIMEOUT_S]


def test_malformed_budget_env_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RSSHUB_FETCH_BUDGET_S", "not-a-float")
    client = _FakeClient(_RSS)
    provider = RSSHubEventProvider(
        "https://rsshub.local",
        feeds=[FeedSpec("news", "/stock/news/{code}", "sentiment")],
        client=client,
    )

    frame = provider.query_events(["AAA"], as_of="2024-01-31")

    assert not frame.empty
    assert client.timeouts == [DEFAULT_TIMEOUT_S]


def test_reachable_but_empty_feed_does_not_raise() -> None:
    # A feed that fetched fine but had no <item>s is legitimate, not an error.
    empty_rss = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
    frame = _provider(empty_rss).query_events(["AAA"], as_of="2024-01-31")
    assert frame.empty
