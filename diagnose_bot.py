"""
diagnose_bot.py — Diagnoses why the bot is taking 0 trades.

Run this first:
    python diagnose_bot.py

It will show you:
  1. Raw Gamma API response (first market)
  2. How many markets pass each filter stage
  3. Sample order intents that would be generated
  4. Any errors in parsing
"""

import asyncio
import json
import httpx

def parse_prices(raw_prices):
    if isinstance(raw_prices, str):
        return json.loads(raw_prices)
    return raw_prices or []

GAMMA_API = "https://gamma-api.polymarket.com"


async def main():
    print("=" * 60)
    print("STEP 1 — Raw Gamma API response (first 2 markets)")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GAMMA_API}/markets",
            params={"active": "true", "closed": "false", "limit": 5},
        )
        print(f"HTTP status: {resp.status_code}")
        data = resp.json()

    if not data:
        print("ERROR: API returned empty response!")
        return

    print(f"Total markets returned in batch: {len(data)}")
    print(f"\nFirst market raw keys: {list(data[0].keys())}")
    print(f"\nFirst market raw JSON:")
    print(json.dumps(data[0], indent=2, default=str)[:3000])

    print("\n" + "=" * 60)
    print("STEP 2 — Filter diagnostics across 100 markets")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GAMMA_API}/markets",
            params={"active": "true", "closed": "false", "limit": 100},
        )
        all_markets = resp.json()

    total         = len(all_markets)
    has_prices    = 0
    active        = 0
    vol_pass      = 0
    spread_pass   = 0
    price_pass    = 0
    all_pass      = 0

    MIN_VOL    = 10_000
    MAX_SPREAD = 0.05
    MIN_PRICE  = 0.03
    MAX_PRICE  = 0.97

    for m in all_markets:
        prices = parse_prices(m.get("outcomePrices", []))
        if prices and len(prices) >= 2:
            has_prices += 1
        else:
            continue

        if not m.get("active", True):
            continue
        active += 1

        # Volume — use volumeNum (lifetime total)
        vol = float(m.get("volumeNum") or m.get("volume") or 0)
        if vol >= MIN_VOL:
            vol_pass += 1
        else:
            continue

        # Spread — use spread field directly if available
        yes_price = float(prices[0])
        no_price  = float(prices[1])
        if m.get("spread") is not None:
            spread = float(m["spread"])
        else:
            best_ask = m.get("bestAsk")
            best_bid = m.get("bestBid")
            if best_ask and best_bid:
                spread = float(best_ask) - float(best_bid)
            else:
                spread = abs(yes_price - (1.0 - no_price))
        if spread <= MAX_SPREAD:
            spread_pass += 1
        else:
            continue

        # Price range
        if MIN_PRICE <= yes_price <= MAX_PRICE:
            price_pass += 1
            all_pass += 1

    print(f"Total markets in batch:         {total}")
    print(f"  Have outcomePrices:           {has_prices}")
    print(f"  Active:                       {active}")
    print(f"  Pass vol > ${MIN_VOL:,}:         {vol_pass}")
    print(f"  Pass spread < {MAX_SPREAD}:        {spread_pass}")
    print(f"  Pass price [{MIN_PRICE},{MAX_PRICE}]:    {price_pass}")
    print(f"\n  >>> MARKETS THAT WOULD BE TRADED: {all_pass} <<<")

    # Show volume distribution
    vols = []
    for m in all_markets:
        vol = float(m.get("volume") or m.get("volumeNum") or m.get("volume24hr") or 0)
        vols.append(vol)
    vols.sort(reverse=True)
    print(f"\nVolume distribution (top 10): {[round(v) for v in vols[:10]]}")
    print(f"Median volume: {sorted(vols)[len(vols)//2]:.0f}")
    print(f"Markets with vol > $10k: {sum(1 for v in vols if v > 10_000)}")
    print(f"Markets with vol > $1k:  {sum(1 for v in vols if v > 1_000)}")
    print(f"Markets with vol > $100: {sum(1 for v in vols if v > 100)}")

    print("\n" + "=" * 60)
    print("STEP 3 — BTC/XRP/SOL deep search (events + slug + all pages)")
    print("=" * 60)

    COIN_TERMS = ["bitcoin", "btc", "xrp", "ripple", "solana", "sol",
                  "crypto", "eth", "ethereum"]

    all_found: dict = {}  # id -> market dict

    def _add(markets_list):
        for m in markets_list:
            mid = m.get("id") or m.get("conditionId") or str(m)
            if mid not in all_found:
                all_found[mid] = m

    _add(all_markets)

    async with httpx.AsyncClient(timeout=30) as client:

        # 1. Paginate /markets without active filter (include everything)
        print("  Scanning /markets (no active filter, up to 1000)...")
        for offset in range(0, 1000, 100):
            try:
                r = await client.get(f"{GAMMA_API}/markets",
                    params={"limit": 100, "offset": offset})
                if r.status_code != 200 or not r.json():
                    break
                _add(r.json())
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"    offset {offset} error: {e}"); break

        # 2. Try /events endpoint — groups of related markets
        print("  Scanning /events endpoint...")
        for offset in range(0, 300, 50):
            try:
                r = await client.get(f"{GAMMA_API}/events",
                    params={"active": "true", "closed": "false",
                            "limit": 50, "offset": offset})
                if r.status_code != 200:
                    print(f"    /events status: {r.status_code}"); break
                events = r.json()
                if not events:
                    break
                for ev in events:
                    # events contain nested markets[]
                    for m in (ev.get("markets") or []):
                        m.setdefault("question", ev.get("title", ""))
                        _add([m])
                    # also check event title itself
                    ev_q = (ev.get("title") or ev.get("question") or "").lower()
                    if any(t in ev_q for t in COIN_TERMS):
                        print(f"    EVENT: [{ev.get('id')}] {ev.get('title','')}")
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"    /events error: {e}"); break

        # 3. Direct slug lookups for known Polymarket crypto price markets
        print("  Trying known crypto price-feed slugs...")
        slugs = [
            "btc-price-5min", "bitcoin-price-5min", "btc-5-minute",
            "btc-above-", "will-btc-", "will-bitcoin-",
            "xrp-price", "will-xrp-", "solana-price", "will-sol-",
            "btc-end-of-day", "btc-eod", "crypto-price",
            "bitcoin-above", "btc-close", "bitcoin-close",
        ]
        for slug in slugs:
            try:
                r = await client.get(f"{GAMMA_API}/markets",
                    params={"slug": slug, "limit": 20})
                if r.status_code == 200 and r.json():
                    _add(r.json())
                    for m in r.json():
                        print(f"    SLUG HIT [{slug}]: {m.get('question','')}")
            except Exception:
                pass

        # 4. Try /markets with tag/category filter
        print("  Trying tag/category filters...")
        for tag in ["crypto", "cryptocurrency", "bitcoin", "price"]:
            try:
                r = await client.get(f"{GAMMA_API}/markets",
                    params={"tag": tag, "limit": 50})
                if r.status_code == 200 and r.json():
                    _add(r.json())
                    print(f"    tag={tag}: {len(r.json())} results")
            except Exception:
                pass

    print(f"\nTotal unique markets scanned: {len(all_found)}")

    coin_matches = [
        m for m in all_found.values()
        if any(t in (m.get("question") or "").lower() for t in COIN_TERMS)
    ]
    print(f"Markets mentioning BTC/XRP/SOL/ETH/crypto: {len(coin_matches)}")

    if coin_matches:
        print("\nAll crypto-related markets found (sorted by volume):")
        for m in sorted(coin_matches,
                        key=lambda x: float(x.get("volumeNum") or x.get("volume") or 0),
                        reverse=True)[:50]:
            vol  = float(m.get("volumeNum") or m.get("volume") or 0)
            sprd = m.get("spread", "?")
            yes  = float((parse_prices(m.get("outcomePrices", [])) or [0])[0])
            act  = "ACTIVE  " if m.get("active") else "inactive"
            print(f"  [{act} | {vol:>12,.0f} vol | sprd={sprd} | yes={yes:.2f}] {m.get('question', '')}")
    else:
        print("\nNO crypto markets found. Printing 10 sample market questions to verify API:")
        for m in list(all_found.values())[:10]:
            print(f"  {m.get('question', m.get('id', '?'))}")

    print("\n" + "=" * 60)
    print("STEP 4 — Volume field names actually present")
    print("=" * 60)
    vol_fields = ["volume", "volumeNum", "volume24hr", "volumeClob", "usdcSize"]
    for field in vol_fields:
        count = sum(1 for m in all_markets if m.get(field) is not None)
        if count > 0:
            sample = [
                round(float(m[field]), 2)
                for m in all_markets[:5]
                if m.get(field) is not None
            ]
            print(f"  '{field}' present in {count}/{total} markets  — samples: {sample}")
        else:
            print(f"  '{field}' NOT FOUND")


if __name__ == "__main__":
    asyncio.run(main())
