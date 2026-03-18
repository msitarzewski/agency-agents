"""
executor.py — Live order execution via the Polymarket CLOB API.

Requires:
    pip install py-clob-client

Official docs: https://github.com/Polymarket/py-clob-client

The ClobClient handles:
  - EIP-712 order signing with your private key
  - Submission to the Polymarket CLOB
  - Order status polling

Set BOT_MODE=live in .env to activate this executor.
ALWAYS paper trade first.
"""

import asyncio
import logging
import time as _time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .config import Config
from .paper_trader import FillResult
from .risk import RiskState
from .sizer import OrderIntent

logger = logging.getLogger(__name__)

# ── Conditional import (py-clob-client may not be installed) ──────────────────
try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import (
        ApiCreds,
        MarketOrderArgs,
        OrderArgs,
        OrderType,
    )
    from py_clob_client.constants import POLYGON
    _CLOB_AVAILABLE = True
except ImportError:
    _CLOB_AVAILABLE = False
    logger.warning(
        "py-clob-client not installed. Live trading unavailable. "
        "Run: pip install py-clob-client"
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LiveExecutor:
    """
    Submits real limit orders to the Polymarket CLOB.
    Requires a funded Polygon wallet with USDC approved to the CTF Exchange.
    """

    def __init__(self, cfg: Config, risk: RiskState) -> None:
        if not _CLOB_AVAILABLE:
            raise RuntimeError(
                "py-clob-client is not installed. "
                "Install it with: pip install py-clob-client"
            )
        if not cfg.private_key:
            raise ValueError("POLYMARKET_PRIVATE_KEY is not set.")

        self.cfg  = cfg
        self.risk = risk

        # Initialise CLOB client
        # The client signs orders with your private key using EIP-712
        self._client = ClobClient(
            host="https://clob.polymarket.com",
            chain_id=POLYGON,
            key=cfg.private_key,
        )
        # Derive API credentials from the wallet (creates them on first call)
        try:
            self._creds: ApiCreds = self._client.create_or_derive_api_creds()
            self._client.set_api_creds(self._creds)
            logger.info("CLOB client authenticated: %s", self._creds.api_key[:8] + "…")
        except Exception as exc:
            raise RuntimeError(f"CLOB authentication failed: {exc}") from exc

    async def execute_buy(self, intent: OrderIntent) -> FillResult:
        """Submit a BUY limit order to the Polymarket CLOB."""
        allowed, reason = self.risk.can_trade(
            intent.market_id, intent.outcome, intent.size_usdc
        )
        if not allowed:
            logger.warning("Live BUY blocked: %s", reason)
            return self._rejected(intent, "BUY", reason)

        # Convert USDC size to token count at limit price
        token_amount = int((intent.size_usdc / intent.price) * 1_000_000)  # micro-USDC

        # Resolve the token ID — prefer intent-supplied, fallback to stored or lookup
        token_id = (
            getattr(intent, "token_id", "")
            or self._resolve_token_id(intent.market_id, intent.outcome)
        )

        try:
            order_args = OrderArgs(
                price=intent.price,
                size=token_amount,
                side="BUY",
                token_id=token_id,
            )
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.create_and_post_order(order_args),
            )
            order_id = resp.get("orderID", "unknown")
            logger.info(
                "[LIVE ] BUY  %-8s  %-55s  price=%.4f  $%.2f  order_id=%s",
                intent.outcome, intent.question[:55],
                intent.price, intent.size_usdc, order_id,
            )
            self.risk.record_buy(
                intent.market_id, intent.outcome, intent.size_usdc, intent.price,
                end_time=getattr(intent, "end_time", None),
                question=intent.question,
                token_id=token_id,
            )
            return FillResult(
                success=True,
                market_id=intent.market_id,
                outcome=intent.outcome,
                price=intent.price,
                size_usdc=intent.size_usdc,
                tokens=token_amount / 1_000_000,
                fill_price=intent.price,
                side="BUY",
                timestamp=_now(),
            )
        except Exception as exc:
            logger.error("Live BUY failed: %s", exc)
            return self._rejected(intent, "BUY", str(exc))

    async def execute_sell(
        self,
        market_id: str,
        question: str,
        outcome: str,
        tokens: float,
        price: float,
    ) -> FillResult:
        """Submit a SELL limit order to the Polymarket CLOB."""
        token_amount = int(tokens * 1_000_000)
        size_usdc    = tokens * price

        try:
            order_args = OrderArgs(
                price=price,
                size=token_amount,
                side="SELL",
                token_id=self._resolve_token_id(market_id, outcome),
            )
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.create_and_post_order(order_args),
            )
            order_id = resp.get("orderID", "unknown")
            logger.info(
                "[LIVE ] SELL %-8s  %-55s  price=%.4f  $%.2f  order_id=%s",
                outcome, question[:55], price, size_usdc, order_id,
            )
            self.risk.record_sell(market_id, outcome, size_usdc, price)
            return FillResult(
                success=True,
                market_id=market_id,
                outcome=outcome,
                price=price,
                size_usdc=size_usdc,
                tokens=tokens,
                fill_price=price,
                side="SELL",
                timestamp=_now(),
            )
        except Exception as exc:
            logger.error("Live SELL failed: %s", exc)
            return FillResult(
                success=False,
                market_id=market_id,
                outcome=outcome,
                price=price,
                size_usdc=size_usdc,
                tokens=tokens,
                fill_price=price,
                side="SELL",
                timestamp=_now(),
                reason=str(exc),
            )

    def _resolve_token_id(self, market_id: str, outcome: str) -> str:
        """Return cached token_id from risk state, or empty string if unknown."""
        return (
            self.risk.market_token_ids
            .get(market_id, {})
            .get(outcome, "")
        )

    def redeem_position(self, condition_id: str, token_id: str, side: str) -> bool:
        """
        Claim winning tokens on-chain after market resolution.
        Ported from copytrader.py — 3-step process:
          1. Transfer winning tokens from EOA wallet → Safe (proxy wallet)
          2. Call redeem_position on the CTF exchange from the Safe
          3. Sweep USDC.e proceeds back from Safe → EOA

        Only runs in live mode. Returns True on success.
        """
        if not condition_id or not token_id:
            logger.warning("redeem_position: missing condition_id or token_id — skipping")
            return False
        try:
            from polymarket_apis.clients.web3_client import PolymarketWeb3Client
            from web3 import Web3
        except ImportError:
            logger.warning(
                "polymarket_apis / web3 not installed — cannot redeem on-chain. "
                "Run: pip install polymarket-apis web3"
            )
            return False

        try:
            RPC       = "https://polygon.drpc.org"
            EOA_ADDR  = Web3.to_checksum_address(self.cfg.funder_address)
            eoa_client  = PolymarketWeb3Client(self.cfg.private_key, signature_type=0, rpc_url=RPC)
            safe_client = PolymarketWeb3Client(self.cfg.private_key, signature_type=2, rpc_url=RPC)
            SAFE_ADDR   = safe_client.address

            # ── Step 1: Transfer winning tokens EOA → Safe ─────────────────
            eoa_bal  = eoa_client.get_token_balance(token_id)
            safe_bal = eoa_client.get_token_balance(token_id, SAFE_ADDR)
            if eoa_bal > 0:
                logger.info("Transferring %.4f tokens EOA → Safe...", eoa_bal)
                r = eoa_client.transfer_token(token_id, SAFE_ADDR, eoa_bal)
                if r.status != 1:
                    logger.warning("Token transfer FAILED | tx: %s", r.tx_hash)
                    return False
                logger.info("Transfer confirmed ✓ | tx: %s...", r.tx_hash[:20])
                _time.sleep(3)
            elif safe_bal > 0:
                logger.info("Tokens already in Safe (%.4f) — skipping transfer", safe_bal)
            else:
                logger.info("No winning tokens found in EOA or Safe — already redeemed?")
                return True

            # ── Step 2: Redeem from Safe ────────────────────────────────────
            logger.info("Redeeming from Safe | condition: %s...", condition_id[:16])
            r = safe_client.redeem_position(condition_id=condition_id, amounts=[0, 0], neg_risk=False)
            if r.status != 1:
                logger.warning("Safe redemption FAILED | tx: %s", r.tx_hash)
                return False
            logger.info("Redemption confirmed ✓ | tx: %s...", r.tx_hash[:20])
            _time.sleep(3)

            # ── Step 3: Sweep USDC.e Safe → EOA ────────────────────────────
            safe_usdc = safe_client.get_usdc_balance()
            if safe_usdc > 0:
                logger.info("Sweeping $%.4f USDC.e Safe → EOA...", safe_usdc)
                r = safe_client.transfer_usdc(EOA_ADDR, safe_usdc)
                if r.status == 1:
                    logger.info(
                        "Sweep confirmed ✓ | $%.4f USDC.e returned | tx: %s...",
                        safe_usdc, r.tx_hash[:20],
                    )
                else:
                    logger.warning("Sweep FAILED — funds in Safe, run withdraw_to_wallet.py manually")
            else:
                logger.warning("No USDC.e in Safe after redemption — may still be processing")
            return True
        except Exception as exc:
            logger.error("Redemption error: %s\n%s", exc, traceback.format_exc())
            return False

    def _rejected(self, intent: OrderIntent, side: str, reason: str) -> FillResult:
        return FillResult(
            success=False,
            market_id=intent.market_id,
            outcome=intent.outcome,
            price=intent.price,
            size_usdc=intent.size_usdc,
            tokens=0.0,
            fill_price=intent.price,
            side=side,
            timestamp=_now(),
            reason=reason,
        )
