"""
config.py — All bot settings loaded from environment variables.

Copy .env.example to .env, fill in your values, then:
    source .env && python run_bot.py
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # ── Wallet ───────────────────────────────────────────────
    # Your Polymarket trading wallet private key (hex, no 0x prefix)
    private_key: str = field(
        default_factory=lambda: os.environ.get("POLYMARKET_PRIVATE_KEY", "")
    )
    # Funder / EOA address — needed for on-chain redemption sweeps
    funder_address: str = field(
        default_factory=lambda: os.environ.get("FUNDER_ADDRESS", "")
    )
    # Polygon RPC endpoint (free: https://polygon-rpc.com)
    polygon_rpc: str = field(
        default_factory=lambda: os.environ.get(
            "POLYGON_RPC", "https://polygon-rpc.com"
        )
    )

    # ── Capital ───────────────────────────────────────────────
    # Total USDC bankroll the bot may deploy (set this to your wallet balance)
    bankroll_usdc: float = field(
        default_factory=lambda: float(os.environ.get("BANKROLL_USDC", "1000"))
    )

    # ── Sizing (reverse-engineered from target trader) ────────
    # size_usdc = slope * price + intercept  (per fragment)
    sizing_slope: float = field(
        default_factory=lambda: float(os.environ.get("SIZING_SLOPE", "26.74"))
    )
    sizing_intercept: float = field(
        default_factory=lambda: float(os.environ.get("SIZING_INTERCEPT", "-1.59"))
    )
    # Number of fragments per price level (observed: ~2)
    order_fragments: int = field(
        default_factory=lambda: int(os.environ.get("ORDER_FRAGMENTS", "2"))
    )
    min_order_usdc: float = field(
        default_factory=lambda: float(os.environ.get("MIN_ORDER_USDC", "1.0"))
    )
    max_order_usdc: float = field(
        default_factory=lambda: float(os.environ.get("MAX_ORDER_USDC", "200.0"))
    )

    # ── Market Allowlist ──────────────────────────────────────
    # Comma-separated keywords — ALL must appear in the question (case-insensitive).
    # Leave empty to trade all markets.
    # Each entry is a pipe-separated OR group, comma separates AND groups.
    # Example: "bitcoin|btc,5 min|5min" means question must contain
    # (bitcoin OR btc) AND (5 min OR 5min)
    #
    # Set in .env as:
    #   MARKET_KEYWORDS=bitcoin|btc|solana|sol|xrp|ripple
    #   MARKET_TIMEFRAMES=5 min|5min|15 min|15min|1 hour|60 min
    market_keywords: str = field(
        default_factory=lambda: os.environ.get(
            "MARKET_KEYWORDS", "bitcoin|btc|solana|sol|xrp|ripple"
        )
    )
    market_timeframes: str = field(
        default_factory=lambda: os.environ.get(
            "MARKET_TIMEFRAMES", ""
        )
    )
    # Assets to include in ephemeral up/down market fetching.
    # Pipe-separated list. Set empty to disable up/down market trading.
    # Example: "btc|xrp|sol|eth"
    updown_assets: str = field(
        default_factory=lambda: os.environ.get(
            "UPDOWN_ASSETS", "btc|xrp|sol"
        )
    )

    # ── Market Filters ────────────────────────────────────────
    # Minimum lifetime volume (volumeNum from Gamma API)
    min_market_volume_usdc: float = field(
        default_factory=lambda: float(
            os.environ.get("MIN_MARKET_VOLUME_USDC", "10000")
        )
    )
    max_spread: float = field(
        default_factory=lambda: float(os.environ.get("MAX_SPREAD", "0.05"))
    )
    # Only trade if price is in this range (avoid near-resolution extremes)
    min_price: float = field(
        default_factory=lambda: float(os.environ.get("MIN_PRICE", "0.03"))
    )
    max_price: float = field(
        default_factory=lambda: float(os.environ.get("MAX_PRICE", "0.97"))
    )

    # ── Risk Management ───────────────────────────────────────
    # Maximum % of bankroll in any single market
    max_market_exposure_pct: float = field(
        default_factory=lambda: float(
            os.environ.get("MAX_MARKET_EXPOSURE_PCT", "0.10")
        )
    )
    # Kill switch: halt if daily drawdown exceeds this fraction of bankroll
    daily_loss_limit_pct: float = field(
        default_factory=lambda: float(
            os.environ.get("DAILY_LOSS_LIMIT_PCT", "0.05")
        )
    )
    # Maximum total exposure across all markets
    max_total_exposure_pct: float = field(
        default_factory=lambda: float(
            os.environ.get("MAX_TOTAL_EXPOSURE_PCT", "0.80")
        )
    )

    # ── Execution ─────────────────────────────────────────────
    # Seconds between trade bursts (matched to original wallet: 2s)
    scan_interval_sec: int = field(
        default_factory=lambda: int(os.environ.get("SCAN_INTERVAL_SEC", "2"))
    )
    # Seconds between full Gamma API market-list refreshes (slow scan)
    # Trade loop runs every scan_interval_sec against the cached list.
    market_rescan_sec: int = field(
        default_factory=lambda: int(os.environ.get("MARKET_RESCAN_SEC", "30"))
    )
    # Seconds between individual order placements in live mode (rate limiting).
    # Paper mode ignores this — all fills are instant.
    order_delay_sec: float = field(
        default_factory=lambda: float(os.environ.get("ORDER_DELAY_SEC", "0.1"))
    )
    # Automatically exit a position when its token price reaches this level
    take_profit_price: float = field(
        default_factory=lambda: float(os.environ.get("TAKE_PROFIT_PRICE", "0.98"))
    )

    # ── Mode ──────────────────────────────────────────────────
    # "paper" = simulate only, "live" = real orders
    mode: str = field(
        default_factory=lambda: os.environ.get("BOT_MODE", "paper")
    )

    # ── Logging ───────────────────────────────────────────────
    log_file: str = field(
        default_factory=lambda: os.environ.get("LOG_FILE", "bot_trades.csv")
    )
    log_level: str = field(
        default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO")
    )

    def validate(self) -> None:
        if self.mode == "live" and not self.private_key:
            raise ValueError(
                "POLYMARKET_PRIVATE_KEY must be set in environment for live mode."
            )
        if self.bankroll_usdc <= 0:
            raise ValueError("BANKROLL_USDC must be > 0")
        if self.mode not in ("paper", "live"):
            raise ValueError("BOT_MODE must be 'paper' or 'live'")

    def summary(self) -> str:
        return (
            f"\n{'='*55}\n"
            f"  Polymarket LP Bot — {self.mode.upper()} MODE\n"
            f"{'='*55}\n"
            f"  Bankroll:          ${self.bankroll_usdc:,.2f} USDC\n"
            f"  Sizing rule:       size = {self.sizing_slope}×price + {self.sizing_intercept}\n"
            f"  Order fragments:   {self.order_fragments} per price level\n"
            f"  Min order:         ${self.min_order_usdc}\n"
            f"  Market filter:     vol>${self.min_market_volume_usdc:,.0f}, spread<{self.max_spread}\n"
            f"  Coins:             {self.market_keywords}\n"
            f"  Timeframes:        {self.market_timeframes}\n"
            f"  Up/down assets:    {self.updown_assets}\n"
            f"  Price range:       [{self.min_price}, {self.max_price}]\n"
            f"  Max per market:    {self.max_market_exposure_pct*100:.0f}% of bankroll\n"
            f"  Daily loss limit:  {self.daily_loss_limit_pct*100:.0f}% of bankroll\n"
            f"  Trade interval:    {self.scan_interval_sec}s  (market rescan every {self.market_rescan_sec}s)\n"
            f"  Take profit:       {self.take_profit_price:.2f}\n"
            f"  Log file:          {self.log_file}\n"
            f"{'='*55}"
        )
