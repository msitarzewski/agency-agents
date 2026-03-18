#!/usr/bin/env python3
"""
run_bot.py — CLI entry point for the Polymarket LP Seeding Bot.

Usage:
    # Paper trade (safe, no real money):
    BOT_MODE=paper BANKROLL_USDC=1000 python run_bot.py

    # Live trade (requires funded wallet + private key):
    BOT_MODE=live POLYMARKET_PRIVATE_KEY=<hex_key> BANKROLL_USDC=500 python run_bot.py

    # Or load from .env:
    source .env && python run_bot.py
"""

import asyncio
import logging
import signal
import sys

# Auto-load .env file — works on Windows CMD without needing `source .env`
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on env vars being set manually

from polymarket_bot.config import Config
from polymarket_bot.monitor import Monitor
from polymarket_bot.paper_trader import PaperTrader
from polymarket_bot.risk import RiskState
from polymarket_bot.bot import PolymarketLPBot


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log"),
        ],
    )
    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def main() -> None:
    cfg = Config()

    try:
        cfg.validate()
    except ValueError as exc:
        print(f"\n❌  Configuration error: {exc}")
        print("    Check your environment variables or .env file.\n")
        sys.exit(1)

    setup_logging(cfg.log_level)
    logger = logging.getLogger("run_bot")

    print(cfg.summary())

    # Build components
    risk    = RiskState(cfg=cfg)
    monitor = Monitor(cfg=cfg, risk=risk)

    if cfg.mode == "paper":
        executor = PaperTrader(cfg=cfg, risk=risk)
        logger.info("Paper trading mode active — no real orders will be placed.")
    else:
        # Live mode: import here so paper mode works without py-clob-client installed
        from polymarket_bot.executor import LiveExecutor
        try:
            executor = LiveExecutor(cfg=cfg, risk=risk)
        except (RuntimeError, ValueError) as exc:
            print(f"\n❌  Live executor setup failed: {exc}\n")
            sys.exit(1)
        print("\n⚠️   LIVE TRADING MODE — real USDC will be deployed.\n"
              "    Press Ctrl+C within 5 seconds to abort...\n")
        await asyncio.sleep(5)

    bot = PolymarketLPBot(cfg=cfg, executor=executor, risk=risk, monitor=monitor)

    # Graceful shutdown — add_signal_handler is Unix-only, use signal.signal on Windows
    def _shutdown(signum, frame) -> None:
        logger.info("Shutting down gracefully…")
        bot.stop()

    signal.signal(signal.SIGINT,  _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    await bot.run()

    # Final summary
    print("\n" + "=" * 55)
    print("  Bot stopped. Final risk state:")
    print(risk.summary())
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
