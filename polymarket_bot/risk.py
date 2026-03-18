"""
risk.py — Position tracking and risk management.

Enforces:
  • Per-market exposure cap (default 10% of bankroll)
  • Total portfolio exposure cap (default 80% of bankroll)
  • Daily loss limit kill switch (default 5% of bankroll)
  • Minimum remaining bankroll guard
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class PositionRecord:
    market_id:      str
    outcome:        str           # "Up" or "Down"
    tokens_held:    float = 0.0
    cost_basis_usdc: float = 0.0  # total USDC spent buying
    realised_pnl:   float = 0.0  # USDC from sells minus cost of those tokens
    token_id:       str = ""      # ERC-1155 token ID for on-chain redemption


@dataclass
class RiskState:
    cfg: Config

    # market_id → {outcome → PositionRecord}
    positions: dict[str, dict[str, PositionRecord]] = field(default_factory=dict)

    # Total USDC spent today (resets at UTC midnight)
    _day_start_equity: float = 0.0
    _today: date = field(default_factory=lambda: datetime.now(timezone.utc).date())
    _daily_realised_pnl: float = 0.0

    # Cumulative deployed capital (total BUY spend since bot start)
    total_deployed_usdc: float = 0.0
    # Cumulative retrieved capital (total SELL proceeds since bot start)
    total_retrieved_usdc: float = 0.0

    # Kill switch flag
    halted: bool = False
    halt_reason: str = ""

    # Market metadata for settlement tracking
    market_end_times: dict = field(default_factory=dict)   # market_id → end_time (float)
    market_questions: dict = field(default_factory=dict)   # market_id → question (str)
    market_token_ids: dict = field(default_factory=dict)   # market_id → {outcome → token_id}

    # ── Accessors ────────────────────────────────────────────

    def exposure_for(self, market_id: str, outcome: str) -> float:
        """USDC cost basis for one side of one market."""
        return (
            self.positions
            .get(market_id, {})
            .get(outcome, PositionRecord(market_id, outcome))
            .cost_basis_usdc
        )

    def total_exposure_usdc(self) -> float:
        """Sum of all open cost bases across all markets and outcomes."""
        total = 0.0
        for outcomes in self.positions.values():
            for rec in outcomes.values():
                total += rec.cost_basis_usdc
        return total

    def unrealised_pnl(self, market_prices: dict[str, dict[str, float]]) -> float:
        """
        Estimate unrealised P&L using current market prices.
        market_prices: {market_id: {"Up": price, "Down": price}}
        """
        pnl = 0.0
        for mid, outcomes in self.positions.items():
            prices = market_prices.get(mid, {})
            for outcome, rec in outcomes.items():
                current_price = prices.get(outcome, 0.0)
                market_value  = rec.tokens_held * current_price
                pnl += market_value - rec.cost_basis_usdc
        return pnl

    # ── Checks ───────────────────────────────────────────────

    def check_daily_reset(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today != self._today:
            logger.info("New UTC day — resetting daily P&L tracker")
            self._today = today
            self._daily_realised_pnl = 0.0

    def can_trade(self, market_id: str, outcome: str, size_usdc: float) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        Checks all risk gates before allowing an order.
        """
        self.check_daily_reset()

        if self.halted:
            return False, f"Bot halted: {self.halt_reason}"

        # 1. Daily loss limit
        daily_loss_limit = self.cfg.bankroll_usdc * self.cfg.daily_loss_limit_pct
        if self._daily_realised_pnl < -daily_loss_limit:
            self._trigger_halt(
                f"Daily loss limit hit: ${-self._daily_realised_pnl:.2f} "
                f"> ${daily_loss_limit:.2f}"
            )
            return False, self.halt_reason

        # 2. Per-market exposure cap
        current_mkt_exp = self.exposure_for(market_id, outcome)
        mkt_cap = self.cfg.bankroll_usdc * self.cfg.max_market_exposure_pct
        if current_mkt_exp + size_usdc > mkt_cap:
            return (
                False,
                f"Market exposure cap: {market_id[:16]}… {outcome} "
                f"would be ${current_mkt_exp + size_usdc:.2f} > ${mkt_cap:.2f}",
            )

        # 3. Total portfolio exposure cap
        total_cap = self.cfg.bankroll_usdc * self.cfg.max_total_exposure_pct
        if self.total_exposure_usdc() + size_usdc > total_cap:
            return (
                False,
                f"Portfolio exposure cap: total would exceed ${total_cap:.2f}",
            )

        return True, ""

    # ── Updates ──────────────────────────────────────────────

    def record_buy(
        self,
        market_id: str,
        outcome: str,
        size_usdc: float,
        price: float,
        end_time: Optional[float] = None,
        question: str = "",
        token_id: str = "",
    ) -> None:
        tokens = size_usdc / price if price > 0 else 0.0
        if market_id not in self.positions:
            self.positions[market_id] = {}
        if outcome not in self.positions[market_id]:
            self.positions[market_id][outcome] = PositionRecord(market_id, outcome)
        rec = self.positions[market_id][outcome]
        rec.tokens_held     += tokens
        rec.cost_basis_usdc += size_usdc
        self.total_deployed_usdc += size_usdc
        if end_time:
            self.market_end_times[market_id] = end_time
        if question:
            self.market_questions[market_id] = question
        if token_id:
            rec.token_id = token_id
            if market_id not in self.market_token_ids:
                self.market_token_ids[market_id] = {}
            self.market_token_ids[market_id][outcome] = token_id
        logger.debug(
            "BUY  %s %s  price=%.4f  size=$%.4f  tokens=%.2f",
            market_id[:16], outcome, price, size_usdc, tokens,
        )

    def record_sell(self, market_id: str, outcome: str, size_usdc: float, price: float) -> None:
        tokens_sold = size_usdc / price if price > 0 else 0.0
        if market_id not in self.positions or outcome not in self.positions[market_id]:
            logger.warning("Sell recorded for unknown position: %s %s", market_id, outcome)
            return
        rec = self.positions[market_id][outcome]
        # Cost of the tokens we're selling (proportional)
        if rec.tokens_held > 0:
            cost_per_token = rec.cost_basis_usdc / rec.tokens_held
            cost_of_sold   = cost_per_token * tokens_sold
        else:
            cost_of_sold = 0.0
        pnl = size_usdc - cost_of_sold
        rec.tokens_held      = max(0.0, rec.tokens_held - tokens_sold)
        rec.cost_basis_usdc  = max(0.0, rec.cost_basis_usdc - cost_of_sold)
        rec.realised_pnl    += pnl
        self._daily_realised_pnl += pnl
        self.total_retrieved_usdc += size_usdc
        logger.debug(
            "SELL %s %s  price=%.4f  size=$%.4f  pnl=$%.4f",
            market_id[:16], outcome, price, size_usdc, pnl,
        )

    def _trigger_halt(self, reason: str) -> None:
        self.halted      = True
        self.halt_reason = reason
        logger.critical("🛑 KILL SWITCH TRIGGERED: %s", reason)

    # ── Summary ──────────────────────────────────────────────

    def summary(self) -> str:
        open_positions = sum(
            1
            for outcomes in self.positions.values()
            for rec in outcomes.values()
            if rec.tokens_held > 0
        )
        return (
            f"  Deployed:  ${self.total_deployed_usdc:,.2f} USDC\n"
            f"  Retrieved: ${self.total_retrieved_usdc:,.2f} USDC\n"
            f"  Net open:  ${self.total_exposure_usdc():,.2f} USDC\n"
            f"  Open legs: {open_positions}\n"
            f"  Daily PnL: ${self._daily_realised_pnl:,.2f} USDC\n"
            f"  Halted:    {self.halted}"
        )
