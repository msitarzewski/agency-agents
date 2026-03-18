"""
market_scanner.py — Polls the Polymarket Gamma API for active markets
and returns those that pass the liquidity / spread filter.

Supports two market types:
  1. Standard long-form markets — fetched via paginated /markets endpoint
  2. Ephemeral up/down markets — fetched by timestamp-based slug
     e.g. btc-updown-5m-1773792600  (new market every 5 minutes)
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .config import Config

logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"
_TIMEOUT  = httpx.Timeout(15.0)

# Supported assets for ephemeral up/down markets
_UPDOWN_ASSETS = ["btc", "xrp", "sol", "eth"]
# How many seconds in one up/down window
_UPDOWN_WINDOW_SEC = 300  # 5 minutes


@dataclass
class Market:
    id: str
    question: str
    category: str
    yes_price: float      # price of the "Up" / YES token
    no_price: float       # price of the "Down" / NO token
    spread: float         # best_ask_yes - best_bid_yes (approx)
    volume_usdc: float
    liquidity_usdc: float
    active: bool
    clob_token_ids: list = None   # [yes_token_id, no_token_id]

    @property
    def up_price(self) -> float:
        return self.yes_price

    @property
    def down_price(self) -> float:
        # Down price is complement in binary market
        return round(1.0 - self.yes_price, 6)


def _parse_market(raw: dict) -> Optional[Market]:
    """Parse a raw Gamma API market dict into a Market object."""
    try:
        outcome_prices = raw.get("outcomePrices", [])
        # API returns outcomePrices as a JSON string e.g. '["0.42", "0.58"]'
        if isinstance(outcome_prices, str):
            outcome_prices = json.loads(outcome_prices)
        if not outcome_prices or len(outcome_prices) < 2:
            return None

        yes_price = float(outcome_prices[0])
        no_price  = float(outcome_prices[1])

        # Use spread field directly (present in API), fallback to bid/ask diff
        if raw.get("spread") is not None:
            spread = float(raw["spread"])
        elif raw.get("bestAsk") and raw.get("bestBid"):
            spread = float(raw["bestAsk"]) - float(raw["bestBid"])
        else:
            spread = abs(yes_price - (1.0 - no_price))

        volume    = float(raw.get("volumeNum",    raw.get("volume",    0)) or 0)
        liquidity = float(raw.get("liquidityNum", raw.get("liquidity", 0)) or 0)

        # Parse clobTokenIds (also a JSON string in the API)
        clob_token_ids = raw.get("clobTokenIds", "[]")
        if isinstance(clob_token_ids, str):
            clob_token_ids = json.loads(clob_token_ids)

        return Market(
            id=raw["id"],
            question=raw.get("question", raw.get("title", "")),
            category=raw.get("category", "unknown"),
            yes_price=yes_price,
            no_price=no_price,
            spread=spread,
            volume_usdc=volume,
            liquidity_usdc=liquidity,
            active=bool(raw.get("active", True)),
            clob_token_ids=clob_token_ids,
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Failed to parse market %s: %s", raw.get("id", "?"), exc)
        return None


def _current_updown_timestamps() -> list[int]:
    """
    Return the Unix timestamps for the current and next 5-minute windows.
    Up/down market slugs use the window-open timestamp rounded to 300s.
    We try both current and next window to handle near-boundary timing.
    """
    now = int(time.time())
    current = (now // _UPDOWN_WINDOW_SEC) * _UPDOWN_WINDOW_SEC
    return [current, current + _UPDOWN_WINDOW_SEC]


async def fetch_updown_markets(
    cfg: Config,
    client: httpx.AsyncClient,
) -> list[Market]:
    """
    Fetch the current ephemeral up/down markets by constructing their
    timestamp-based slugs (e.g. btc-updown-5m-1773792600).

    These markets are too short-lived to appear in paginated /markets results,
    so they must be fetched directly by slug. Volume filters are relaxed
    because a brand-new 5-minute market has minimal lifetime volume.
    """
    assets = [a.strip().lower() for a in cfg.updown_assets.split("|") if a.strip()]
    if not assets:
        return []

    timestamps = _current_updown_timestamps()
    found: list[Market] = []
    seen_ids: set[str] = set()

    for asset in assets:
        for ts in timestamps:
            slug = f"{asset}-updown-5m-{ts}"
            try:
                resp = await client.get(
                    f"{GAMMA_API}/markets",
                    params={"slug": slug},
                )
                if resp.status_code != 200:
                    continue
                batch = resp.json()
                if not batch:
                    continue
                for raw in batch:
                    mkt = _parse_market(raw)
                    if mkt and mkt.id not in seen_ids:
                        if _passes_updown_filter(mkt, cfg):
                            seen_ids.add(mkt.id)
                            found.append(mkt)
                            logger.info(
                                "Up/down market found: %s (price=%.3f spread=%.4f)",
                                slug, mkt.yes_price, mkt.spread,
                            )
            except httpx.HTTPError as exc:
                logger.debug("Up/down slug fetch failed [%s]: %s", slug, exc)

    return found


async def fetch_markets(cfg: Config) -> list[Market]:
    """
    Fetch active markets from Gamma API and return those passing
    the volume and spread filters defined in cfg.

    Also fetches ephemeral up/down markets by timestamp slug.
    """
    markets: list[Market] = []
    offset = 0
    limit  = 100

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        while True:
            try:
                resp = await client.get(
                    f"{GAMMA_API}/markets",
                    params={
                        "active":  "true",
                        "closed":  "false",
                        "limit":   limit,
                        "offset":  offset,
                    },
                )
                resp.raise_for_status()
                batch = resp.json()
            except httpx.HTTPError as exc:
                logger.warning("Gamma API error (offset=%d): %s", offset, exc)
                break

            if not batch:
                break

            for raw in batch:
                mkt = _parse_market(raw)
                if mkt and _passes_filter(mkt, cfg):
                    markets.append(mkt)

            if len(batch) < limit:
                break
            offset += limit
            await asyncio.sleep(0.2)   # be polite to the API

        # Also fetch ephemeral up/down markets by timestamp slug
        updown = await fetch_updown_markets(cfg, client)
        existing_ids = {m.id for m in markets}
        for mkt in updown:
            if mkt.id not in existing_ids:
                markets.append(mkt)

    logger.info("Scanner found %d qualifying markets", len(markets))
    return markets


def _passes_filter(mkt: Market, cfg: Config) -> bool:
    if not mkt.active:
        return False
    if mkt.volume_usdc < cfg.min_market_volume_usdc:
        return False
    if mkt.spread > cfg.max_spread:
        return False
    if not (cfg.min_price <= mkt.yes_price <= cfg.max_price):
        return False
    if not _passes_keyword_filter(mkt.question, cfg):
        return False
    return True


def _passes_updown_filter(mkt: Market, cfg: Config) -> bool:
    """
    Relaxed filter for ephemeral up/down markets.
    Skips lifetime volume check (these markets are brand-new).
    Still enforces spread and price range.
    """
    if not mkt.active:
        return False
    if mkt.spread > cfg.max_spread:
        return False
    if not (cfg.min_price <= mkt.yes_price <= cfg.max_price):
        return False
    return True


def _passes_keyword_filter(question: str, cfg: Config) -> bool:
    """
    Require the question to match the coin allowlist AND timeframe allowlist.
    Each config value is a pipe-separated list of OR alternatives.
    Both must match (AND logic between the two groups).
    Empty string = no filter (allow all).
    """
    q = (question or "").lower()

    if cfg.market_keywords:
        coin_terms = [t.strip().lower() for t in cfg.market_keywords.split("|") if t.strip()]
        if coin_terms and not any(t in q for t in coin_terms):
            return False

    if cfg.market_timeframes:
        tf_terms = [t.strip().lower() for t in cfg.market_timeframes.split("|") if t.strip()]
        if tf_terms and not any(t in q for t in tf_terms):
            return False

    return True
