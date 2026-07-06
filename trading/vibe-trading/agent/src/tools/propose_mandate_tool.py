"""``propose_mandate_profiles`` — the read-only PROPOSE half of consent.

The agent calls this tool when the user expresses a live-trading intent (or when
a mandate breach needs widening options). It synthesizes 2-4 numbered candidate
mandate profiles, **every one clamped to the account ceilings** so even the most
aggressive option can never request more than the broker allows, persists the
proposal so the surface commit endpoint can re-validate it, and returns the
``mandate.proposal`` payload (Consent §1 shape).

It is read-only by design: it writes a *proposal* (a menu of clamped options),
never a mandate. Persisting a proposal grants zero trading authority — only the
surface-side :func:`src.live.mandate.commit.commit_mandate` (unreachable from the
agent loop) writes a mandate, and only after re-validating the selected profile
still fits the ceilings the user saw. This is the structural "agent proposes,
user disposes" guarantee (live-trading SPEC §3, Consent §1).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from src.agent.tools import BaseTool
from src.live.mandate.commit import _normalize_limits, save_proposal

#: Ordered profile templates synthesized when the caller gives no explicit
#: profiles. Each is a fraction of the funded ceiling so they always clamp down.
_PROFILE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {"ordinal": 1, "label": "稳健", "order_fraction": 0.05, "daily_trade_cap": 2,
     "notes": "Smallest clips, fewest trades — capital-preservation tilt."},
    {"ordinal": 2, "label": "均衡", "order_fraction": 0.15, "daily_trade_cap": 5,
     "notes": "Moderate sizing, cash-only."},
    {"ordinal": 3, "label": "激进", "order_fraction": 0.30, "daily_trade_cap": 10,
     "notes": "Largest clips this account allows — still cash-only."},
)


class ProposeMandateProfilesTool(BaseTool):
    """Synthesize clamped bounded-autonomy mandate profiles for the user to pick.

    Read-only: returns a ``mandate.proposal`` payload and persists it for later
    commit. Never writes a mandate.
    """

    name = "propose_mandate_profiles"
    description = (
        "Propose 2-4 numbered bounded-autonomy live-trading mandate profiles for "
        "the user to pick from, each clamped to the account's hard ceilings. "
        "READ-ONLY: it returns options and does NOT activate any mandate — the "
        "user must explicitly commit one through the surface. Call this when the "
        "user expresses a live-trading intent, or (with reauth_for set) when an "
        "order breached the active mandate and the user may want to widen it."
    )
    parameters = {
        "type": "object",
        "properties": {
            "broker": {
                "type": "string",
                "description": "Broker key, e.g. 'robinhood'.",
            },
            "intent": {
                "type": "string",
                "description": "Normalized user intent, e.g. 'aggressive tech, ~$5000'.",
            },
            "ceilings": {
                "type": "object",
                "description": (
                    "Account hard-ceiling snapshot the profiles are clamped to "
                    "(e.g. account_funding_usd, max_total_exposure_usd, leverage, "
                    "instruments). Every proposed profile is bounded by these; the "
                    "tool can only clamp DOWN, never up."
                ),
            },
            "session_id": {
                "type": "string",
                "description": "Originating session id (echoed into the payload).",
            },
            "reauth_for": {
                "type": "object",
                "description": (
                    "Optional breach seed: when an order breached a quantitative "
                    "limit, pass {'breach_id', 'limit', 'attempted_value'} to bias "
                    "the proposed widening options. Still clamped to ceilings."
                ),
            },
            "flatten_on_halt": {
                "type": "boolean",
                "description": (
                    "Per-mandate opt-in: when true, a kill-switch trip flattens "
                    "open positions (submits closing orders) in addition to "
                    "cancelling resting orders. Defaults to false (cancel-only — "
                    "the safe default). Stamped onto every proposed profile so the "
                    "user's choice is carried through to commit (SPEC §7.5 #6)."
                ),
            },
        },
        "required": ["broker", "ceilings"],
    }
    repeatable = True
    is_readonly = True

    def execute(self, **kwargs: Any) -> str:
        """Synthesize, persist, and return a ``mandate.proposal`` payload.

        Args:
            **kwargs: ``broker`` and ``ceilings`` required; optional ``intent``,
                ``session_id``, ``reauth_for``, ``flatten_on_halt``.

        Returns:
            JSON string of the ``mandate.proposal`` payload, or an error
            envelope.
        """
        broker = str(kwargs.get("broker") or "").strip().lower()
        if not broker:
            return json.dumps({"status": "error", "error": "broker is required"}, ensure_ascii=False)
        ceilings = kwargs.get("ceilings")
        if not isinstance(ceilings, dict):
            return json.dumps(
                {"status": "error", "error": "ceilings (object) is required"},
                ensure_ascii=False,
            )

        intent = str(kwargs.get("intent") or "").strip()
        session_id = kwargs.get("session_id")
        reauth_for = kwargs.get("reauth_for") if isinstance(kwargs.get("reauth_for"), dict) else None
        flatten_on_halt = bool(kwargs.get("flatten_on_halt", False))

        try:
            profiles = self._synthesize_profiles(ceilings, reauth_for, flatten_on_halt)
        except (TypeError, ValueError) as exc:
            return json.dumps(
                {"status": "error", "error": f"invalid ceilings: {exc}"},
                ensure_ascii=False,
            )

        proposal_id = f"mp_{uuid.uuid4().hex}"
        payload: dict[str, Any] = {
            "type": "mandate.proposal",
            "proposal_id": proposal_id,
            "session_id": session_id,
            "intent_normalized": intent,
            "account": {
                "broker": broker,
                "type": self._account_type(ceilings),
                "funded_by": "user",
            },
            "ceilings_ref": str(ceilings.get("ceilings_ref") or f"caps_{uuid.uuid4().hex}"),
            # The full snapshot is stored on the record so commit re-validates
            # the resolved profile against exactly what the user saw.
            "ceilings": dict(ceilings),
            "profiles": profiles,
            "funding_note": (
                "Funding is set by YOU inside the broker's dedicated trading "
                "account; the agent cannot move money."
            ),
            "halt_note": "随时一句『停』= kill switch, halts everything instantly.",
        }
        if reauth_for is not None:
            payload["reauth_for"] = reauth_for

        try:
            save_proposal(payload)
        except ValueError as exc:
            return json.dumps(
                {"status": "error", "error": f"could not persist proposal: {exc}"},
                ensure_ascii=False,
            )

        return json.dumps(payload, ensure_ascii=False)

    def _synthesize_profiles(
        self,
        ceilings: dict[str, Any],
        reauth_for: dict[str, Any] | None,
        flatten_on_halt: bool = False,
    ) -> list[dict[str, Any]]:
        """Build 2-4 numbered profiles, every limit clamped to ``ceilings``.

        Args:
            ceilings: The account hard-ceiling snapshot.
            reauth_for: Optional breach seed biasing the widening options.
            flatten_on_halt: Per-mandate flatten opt-in stamped onto every
                profile (default ``False`` == cancel-only).

        Returns:
            A list of clamped profile dicts (Consent §1 shape).
        """
        # Read the four clamped limits through the SAME canonical-alias map the
        # commit-time ceiling re-check uses, so propose and commit agree on which
        # ceiling bounds which field regardless of the snapshot's spelling
        # (max_order_usd vs max_order_notional_usd, daily_trade_cap vs
        # max_trades_per_day, instruments vs allowed_instruments). Without this,
        # propose could clamp against one spelling while commit re-checked a
        # different one — the audit H9 mismatch.
        canon = _normalize_limits(ceilings)
        funding = float(ceilings.get("account_funding_usd", ceilings.get("max_total_exposure_usd", 0.0)) or 0.0)
        ceil_order = canon.get("max_order_notional_usd")
        ceil_order = float(ceil_order) if ceil_order is not None else None
        ceil_exposure = ceilings.get("max_total_exposure_usd")
        ceil_exposure = float(ceil_exposure) if ceil_exposure is not None else funding
        ceil_daily = canon.get("max_trades_per_day")
        ceil_daily = int(ceil_daily) if ceil_daily is not None else None
        instruments = list(canon.get("allowed_instruments") or ["equity"])
        universe = ceilings.get("universe") or ["AAPL", "MSFT", "NVDA", "GOOGL"]
        # Leverage is always clamped to the ceiling; default cash-only.
        leverage = canon.get("leverage", "none")

        # A reauth seed nudges the top option toward the breached level, still
        # clamped: we never propose past the ceiling.
        bias = 1.0
        if reauth_for is not None:
            attempted = reauth_for.get("attempted_value")
            if isinstance(attempted, (int, float)) and ceil_order:
                bias = min(1.0, max(bias, float(attempted) / ceil_order))

        profiles: list[dict[str, Any]] = []
        for tpl in _PROFILE_TEMPLATES:
            raw_order = funding * tpl["order_fraction"] * bias
            max_order = round(raw_order, 2)
            if ceil_order is not None:
                max_order = min(max_order, ceil_order)
            daily = tpl["daily_trade_cap"]
            if ceil_daily is not None:
                daily = min(daily, ceil_daily)
            profile = {
                "ordinal": tpl["ordinal"],
                "label": tpl["label"],
                "universe": universe,
                "max_order_usd": max_order,
                "max_total_exposure_usd": ceil_exposure,
                "daily_trade_cap": daily,
                "leverage": leverage,
                "instruments": instruments,
                "flatten_on_halt": flatten_on_halt,
                "notes": tpl["notes"],
            }
            profiles.append(profile)
        return profiles

    @staticmethod
    def _account_type(ceilings: dict[str, Any]) -> str:
        """Return the account type label ('cash' unless ceilings allow leverage)."""
        leverage = ceilings.get("leverage", "none")
        return "cash" if leverage in ("none", None, 1, 1.0) else "margin"
