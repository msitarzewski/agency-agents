"""
bot.py — Main async bot loop.

Orchestrates: scan → signal → risk check → execute → log → settle → dashboard
"""

import asyncio
import json
import logging
import time
from typing import Optional, Union

import httpx

from .config import Config
from .market_scanner import Market, fetch_markets, GAMMA_API
from .monitor import Monitor
from .paper_trader import FillResult, PaperTrader
from .risk import RiskState
from .sizer import OrderIntent, build_order_intents, total_intent_usdc

logger = logging.getLogger(__name__)

_SETTLE_TIMEOUT = httpx.Timeout(10.0)


class PolymarketLPBot:
    """
    LP Seeding Bot that replicates the reverse-engineered strategy:
      1. Scan all active markets passing the liquidity filter
      2. For each market, generate two-sided BUY intents (Up + Down)
         using the price-proportional sizing rule
      3. Check risk gates before each order
      4. Execute orders (paper or live)
      5. Settle resolved positions (check Gamma API for outcomes)
      6. Log fills and print dashboard
    """

    def __init__(
        self,
        cfg: Config,
        executor: Union[PaperTrader, "LiveExecutor"],  # noqa: F821
        risk: RiskState,
        monitor: Monitor,
    ) -> None:
        self.cfg      = cfg
        self.executor = executor
        self.risk     = risk
        self.monitor  = monitor
        self._running = False
        # {condition_id: {"retry_at": float, "token_id": str, "side": str}}
        self._redeem_queue: dict = {}
        self._last_settle_check = 0.0
        # Market cache: refreshed every market_rescan_sec, traded every scan_interval_sec
        self._cached_markets: list[Market] = []
        self._last_full_scan: float = 0.0

    async def _refresh_market_cache(self) -> None:
        """
        Fetch the full qualifying market list from Gamma API and cache it.
        Called at startup and every market_rescan_sec thereafter.
        The heavy paginated scan only runs here — the trade loop uses the cache.
        """
        try:
            markets = await fetch_markets(self.cfg)
            self._cached_markets = markets
            self._last_full_scan = time.time()
            logger.info("Market rescan: %d qualifying markets cached", len(markets))
        except Exception as exc:
            logger.error("Market rescan failed: %s", exc)
            # Keep the old cache if available

    async def run_once(self) -> tuple[int, int, int, dict]:
        """
        Execute one trade burst against the cached market list.
        Matches the original wallet's 2-second burst cadence:
          • No per-call delay (fills are instant in paper mode)
          • Re-enters every qualifying market regardless of existing exposure
            (exposure cap still enforced by can_trade, but re-entry is not
            gated by the scan cycle — same market hit every burst)
        Returns (markets_cached, intents_generated, fills_executed, market_prices).
        """
        markets = self._cached_markets
        if not markets:
            return 0, 0, 0, {}

        intents_generated = 0
        fills_executed    = 0
        market_prices: dict[str, dict[str, float]] = {}

        for market in markets:
            if self.risk.halted:
                logger.warning("Bot halted — skipping remaining markets")
                break

            market_prices[market.id] = {
                "Up":   market.up_price,
                "Down": market.down_price,
            }

            intents = build_order_intents(
                market=market,
                cfg=self.cfg,
                exposure_up_usdc=self.risk.exposure_for(market.id, "Up"),
                exposure_down_usdc=self.risk.exposure_for(market.id, "Down"),
            )

            if not intents:
                continue

            intents_generated += len(intents)
            fills = await self._execute_intents(intents)
            fills_executed += len([f for f in fills if f.success])
            self.monitor.log_fills(fills)

        return len(markets), intents_generated, fills_executed, market_prices

    async def _execute_intents(self, intents: list[OrderIntent]) -> list[FillResult]:
        fills = []
        for intent in intents:
            if self.risk.halted:
                break
            fill = await self.executor.execute_buy(intent)
            fills.append(fill)
        return fills

    async def _check_take_profits(self, market_prices: dict[str, dict[str, float]]) -> int:
        """
        Exit any open position whose current token price has reached TAKE_PROFIT_PRICE.
        Uses market prices already fetched in run_once() — no extra API calls.
        Logs each exit as WIN if pnl > 0, LOSS otherwise.
        Returns number of take-profit exits executed.
        """
        tp = self.cfg.take_profit_price
        taken = 0

        for market_id, outcome_prices in market_prices.items():
            if market_id not in self.risk.positions:
                continue
            for outcome, current_price in outcome_prices.items():
                rec = self.risk.positions[market_id].get(outcome)
                if rec is None or rec.tokens_held <= 0:
                    continue
                if current_price < tp:
                    continue

                question = self.risk.market_questions.get(market_id, "")
                # Capture cost-per-token before sell modifies the position
                cost_per_token = rec.cost_basis_usdc / rec.tokens_held
                tokens = rec.tokens_held

                logger.info(
                    "TAKE PROFIT | %s | %s | price=%.4f ≥ %.2f",
                    market_id[:16], outcome, current_price, tp,
                )

                fill = await self.executor.execute_sell(
                    market_id=market_id,
                    question=question,
                    outcome=outcome,
                    tokens=tokens,
                    price=current_price,
                )
                fill.side = "TP"
                fill.pnl_usdc = fill.size_usdc - (cost_per_token * fill.tokens)
                won = fill.pnl_usdc > 0
                logger.info(
                    "TP %s | %s | %s | pnl=$%+.2f",
                    "WIN" if won else "LOSS", market_id[:16], outcome, fill.pnl_usdc,
                )
                self.monitor.log_fill(fill)
                taken += 1

        return taken

    async def _settle_closed_positions(self) -> int:
        """
        Check ALL open positions for settlement.
        Primary: market end_time elapsed + Gamma API resolved.
        Fallback: CLOB price ≥ 0.95 (same logic as copytrader.py).
        After settlement, queue on-chain redemption (live mode only).
        Returns number of positions settled.
        """
        now = time.time()
        # Throttle to once per 5 s — tight enough to catch 5-min market resolutions
        if now - self._last_settle_check < 5:
            return 0
        self._last_settle_check = now

        settled_count = 0
        to_remove: list[str] = []

        # Gather all markets that have open positions
        candidates: set[str] = set()
        for market_id, outcomes in self.risk.positions.items():
            if any(r.tokens_held > 0 for r in outcomes.values()):
                candidates.add(market_id)

        for market_id in candidates:
            end_time = self.risk.market_end_times.get(market_id, 0)
            # Skip markets that haven't reached end_time yet (with 10s grace),
            # unless we have no end_time (then always check)
            if end_time and end_time > now - 10:
                continue

            winner = await self._fetch_market_outcome(market_id)
            if winner is None:
                continue

            question = self.risk.market_questions.get(market_id, "")
            for outcome, rec in list(self.risk.positions[market_id].items()):
                if rec.tokens_held <= 0:
                    continue

                won = (
                    (outcome == "Up"   and winner in ("Yes", "Up",   "YES", "UP"))   or
                    (outcome == "Down" and winner in ("No",  "Down", "NO",  "DOWN"))
                )
                payout_price = 1.0 if won else 0.0
                pnl_sign     = "+" if won else ""
                pnl_val      = rec.tokens_held * payout_price - rec.cost_basis_usdc

                logger.info(
                    "SETTLE %s | %s | %s | pnl: %s$%.2f",
                    market_id[:16], outcome, "WIN" if won else "LOSS",
                    pnl_sign, pnl_val,
                )

                fill = await self.executor.settle_position(
                    market_id=market_id,
                    question=question,
                    outcome=outcome,
                    tokens=rec.tokens_held,
                    payout_price=payout_price,
                )
                fill.market_end_ts = end_time or now
                self.monitor.log_fill(fill)
                settled_count += 1

                # Queue on-chain redemption for winning positions (live only)
                if won and self.cfg.mode == "live":
                    token_id = rec.token_id or self.risk.market_token_ids.get(market_id, {}).get(outcome, "")
                    if token_id:
                        self._redeem_queue[market_id] = {
                            "retry_at": now + 180,   # 3-min delay for oracle resolution
                            "token_id": token_id,
                            "side":     outcome,
                        }
                        logger.info("Queued redemption in 3 min | %s...", market_id[:16])

            to_remove.append(market_id)

        for mid in to_remove:
            self.risk.market_end_times.pop(mid, None)

        # ── Process redeem queue ─────────────────────────────────────────────
        if self.cfg.mode == "live" and hasattr(self.executor, "redeem_position"):
            for cid in list(self._redeem_queue):
                entry = self._redeem_queue[cid]
                if now < entry["retry_at"]:
                    continue
                ok = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda c=cid, e=entry: self.executor.redeem_position(
                        c, e["token_id"], e["side"]
                    ),
                )
                if ok:
                    del self._redeem_queue[cid]
                    logger.info("Redemption complete | %s", cid[:16])
                else:
                    entry["retry_at"] = now + 300  # retry in 5 min
                    logger.warning("Redemption retry in 5 min | %s...", cid[:16])

        return settled_count

    async def _fetch_market_outcome(self, market_id: str) -> Optional[str]:
        """
        Determine the winning outcome for a market.
        1. Check CLOB live prices — if an outcome token trades ≥ $0.95 it has resolved.
        2. Query Gamma API for resolved/closed state and winner field.
        Returns the winner string ("Up", "Down", "Yes", "No") or None if unresolved.
        """
        try:
            async with httpx.AsyncClient(timeout=_SETTLE_TIMEOUT) as client:
                # ── 1. CLOB price check (fast path, same as copytrader.py) ──
                token_ids = self.risk.market_token_ids.get(market_id, {})
                for outcome, token_id in token_ids.items():
                    if not token_id:
                        continue
                    try:
                        resp = await client.get(
                            "https://clob.polymarket.com/price",
                            params={"token_id": token_id, "side": "SELL"},
                        )
                        if resp.status_code == 200:
                            price = float(resp.json().get("price", 0))
                            if price >= 0.95:
                                logger.info(
                                    "CLOB price=%.4f ≥ 0.95 for %s %s → settled",
                                    price, market_id[:16], outcome,
                                )
                                return outcome
                    except Exception:
                        pass

                # ── 2. Gamma API resolution check ──────────────────────────
                resp = await client.get(
                    f"{GAMMA_API}/markets",
                    params={"id": market_id},
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                raw = data[0] if isinstance(data, list) and data else data
                if not isinstance(raw, dict):
                    return None

                is_resolved = raw.get("resolved", False) or not raw.get("active", True)
                if not is_resolved:
                    return None

                # resolutionIndex takes priority
                res_idx = raw.get("resolutionIndex")
                if res_idx is not None:
                    outcomes_raw = raw.get("outcomes", ["Up", "Down"])
                    if isinstance(outcomes_raw, str):
                        outcomes_raw = json.loads(outcomes_raw)
                    if int(res_idx) < len(outcomes_raw):
                        return str(outcomes_raw[int(res_idx)])

                winner = raw.get("winner") or raw.get("outcome")
                if winner:
                    return str(winner)

                # Fallback to outcome prices
                outcome_prices = raw.get("outcomePrices", [])
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)
                outcomes_raw = raw.get("outcomes", ["Up", "Down"])
                if isinstance(outcomes_raw, str):
                    outcomes_raw = json.loads(outcomes_raw)
                for i, p in enumerate(outcome_prices):
                    if float(p) >= 0.99 and i < len(outcomes_raw):
                        return str(outcomes_raw[i])

        except Exception as exc:
            logger.debug("Outcome fetch failed for %s: %s", market_id, exc)
        return None

    async def run(self) -> None:
        """Main loop: rescan markets every market_rescan_sec, trade every scan_interval_sec."""
        self._running = True
        logger.info("Bot started in %s mode", self.cfg.mode.upper())

        # Initial market load before entering the loop
        await self._refresh_market_cache()

        while self._running:
            if self.risk.halted:
                logger.critical("Bot halted. Stopping loop.")
                break

            # Refresh market list on schedule (slow scan, every market_rescan_sec)
            if time.time() - self._last_full_scan >= self.cfg.market_rescan_sec:
                await self._refresh_market_cache()

            markets_scanned, intents_gen, fills_exec, prices = await self.run_once()

            # Take-profit exits (checked every cycle)
            tp_taken = await self._check_take_profits(prices)
            if tp_taken:
                logger.info("Take-profit exits: %d position(s) this cycle", tp_taken)

            # Settle any positions whose markets have now closed
            settled = await self._settle_closed_positions()
            if settled:
                logger.info("Settled %d position(s) this cycle", settled)

            self.monitor.print_dashboard(
                markets_scanned=markets_scanned,
                intents_generated=intents_gen,
                fills_this_cycle=fills_exec,
                market_prices=prices,
            )

            await asyncio.sleep(self.cfg.scan_interval_sec)

    def stop(self) -> None:
        self._running = False
