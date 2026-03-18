"""
monitor.py — Trade logging and real-time P&L dashboard.

Writes every fill to a CSV log file and prints a status dashboard
to stdout on each scan cycle.
"""

import csv
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from .config import Config
from .paper_trader import FillResult
from .risk import RiskState

logger = logging.getLogger(__name__)

_CSV_FIELDS = [
    "timestamp", "mode", "market_id", "question", "outcome",
    "side", "price", "fill_price", "size_usdc", "tokens",
    "market_end_ts", "pnl_usdc", "success", "reason",
]


class Monitor:
    def __init__(self, cfg: Config, risk: RiskState) -> None:
        self.cfg  = cfg
        self.risk = risk
        self._log_path    = cfg.log_file
        self._cycle_count = 0
        self._start_time  = datetime.now(timezone.utc)
        self._reset_log_file()

    def _reset_log_file(self) -> None:
        """Always start fresh — truncate and write header."""
        with open(self._log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            writer.writeheader()
        logger.info("Trade log reset: %s", self._log_path)

    def log_fill(self, fill: FillResult) -> None:
        """Append a fill (or rejection) to the CSV trade log."""
        with open(self._log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            writer.writerow({
                "timestamp":     fill.timestamp,
                "mode":          self.cfg.mode,
                "market_id":     fill.market_id,
                "question":      fill.question,
                "outcome":       fill.outcome,
                "side":          fill.side,
                "price":         fill.price,
                "fill_price":    fill.fill_price,
                "size_usdc":     fill.size_usdc,
                "tokens":        fill.tokens,
                "market_end_ts": fill.market_end_ts,
                "pnl_usdc":      fill.pnl_usdc,
                "success":       fill.success,
                "reason":        fill.reason,
            })

    def log_fills(self, fills: list[FillResult]) -> None:
        for fill in fills:
            self.log_fill(fill)

    def print_dashboard(
        self,
        markets_scanned: int,
        intents_generated: int,
        fills_this_cycle: int,
        market_prices: Optional[dict] = None,
    ) -> None:
        """Print a status dashboard to stdout."""
        self._cycle_count += 1
        elapsed = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        hrs = elapsed / 3600

        unreal = 0.0
        if market_prices:
            unreal = self.risk.unrealised_pnl(market_prices)

        total_exp   = self.risk.total_exposure_usdc()
        pct_deployed = total_exp / self.cfg.bankroll_usdc * 100

        print(
            f"\n{'─'*60}\n"
            f"  Polymarket LP Bot — {self.cfg.mode.upper()}  "
            f"  Cycle #{self._cycle_count}  "
            f"  Runtime: {hrs:.1f}h\n"
            f"{'─'*60}\n"
            f"  Markets scanned:    {markets_scanned}\n"
            f"  Intents this cycle: {intents_generated}\n"
            f"  Fills  this cycle:  {fills_this_cycle}\n"
            f"{'─'*60}\n"
            + self.risk.summary() + "\n"
            f"  Unrealised PnL:  ${unreal:,.2f} USDC  (mark-to-market)\n"
            f"  % Deployed:      {pct_deployed:.1f}%\n"
            f"{'─'*60}"
        )

        if self.risk.halted:
            print(f"\n  🛑  BOT HALTED: {self.risk.halt_reason}\n")
