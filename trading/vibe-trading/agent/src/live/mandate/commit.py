"""The single mandate writer — the COMMIT half of the consent state machine.

This module is deliberately **not** a tool and **not** importable/registerable
through the agent tool registry (``src.tools.__init__`` only discovers
:class:`~src.agent.tools.BaseTool` subclasses; nothing here subclasses it). It
is a plain function the API surface (``POST /mandate/commit``) calls when a user
picks a profile. The agent loop has no reference to :func:`commit_mandate`, so
even a compromised/hallucinating model cannot self-authorize a mandate — the
only code path that writes one requires the surface-originated ``consent_ack``
the model never produces (see the live-trading SPEC §3 trust invariant,
Consent §1, Mandate §2). This is the 命门 invariant: a structural guarantee,
not a prompt-level one.

The companion :func:`save_proposal` persists the read-only proposals the
``propose_mandate_profiles`` tool synthesizes (Consent PROPOSE state). A proposal
is *not* a mandate — persisting it grants no authority — so the tool may write
proposals; only :func:`commit_mandate` writes the mandate, and only after
re-validating that the committed profile still fits the ceilings the user saw.

Storage layout (under :func:`src.live.paths.live_root`)::

    <runtime_root>/live/<broker>/mandate.json        # 0600, committed mandate
    <runtime_root>/live/<broker>/proposals/<id>.json # 0600, pending proposals
    <runtime_root>/live/<broker>/consent/<id>.json   # 0600, consent records
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from src.live.mandate.model import MANDATE_SCHEMA_VERSION
from src.live.paths import broker_dir

logger = logging.getLogger(__name__)

#: Default mandate lifetime when a commit does not override it (SPEC §9 dec. 2).
DEFAULT_MANDATE_LIFETIME_DAYS = 30

_MANDATE_FILENAME = "mandate.json"
_PROPOSALS_DIRNAME = "proposals"
_CONSENT_DIRNAME = "consent"
_PROPOSAL_ID_RE = re.compile(r"^mp_[0-9a-f]{32}$")

#: Maps every accepted alias of a clamped limit to its CANONICAL name. The
#: proposal profile, the ceiling snapshot, and the clamp in
#: ``propose_mandate_tool`` all use slightly different human-vs-schema spellings
#: for the same limit (e.g. the profile stores ``max_order_usd`` while a ceiling
#: snapshot may key it ``max_order_notional_usd``). Comparing raw key names would
#: silently skip a limit whenever the two sides disagree on spelling — turning
#: the commit-time ceiling re-check into a NO-OP for that field (audit H9). Both
#: sides are normalized through this map before comparison so the re-check covers
#: exactly the four fields ``propose_mandate_profiles`` clamps: order notional,
#: daily trade cap, leverage, and instruments.
_CEILING_ALIASES: dict[str, str] = {
    # order notional
    "max_order_usd": "max_order_notional_usd",
    "max_order_notional_usd": "max_order_notional_usd",
    # daily trade cap
    "daily_trade_cap": "max_trades_per_day",
    "max_trades_per_day": "max_trades_per_day",
    # leverage (single spelling, mapped for completeness)
    "leverage": "leverage",
    "max_leverage": "leverage",
    # instrument whitelist
    "instruments": "allowed_instruments",
    "allowed_instruments": "allowed_instruments",
}


def _normalize_limits(source: Mapping[str, Any]) -> dict[str, Any]:
    """Project ``source`` onto canonical limit names for ceiling comparison.

    Only the keys that name a clamped limit (those in :data:`_CEILING_ALIASES`)
    are carried through; everything else is dropped because it is not a limit the
    commit-time re-check bounds. When both an alias and its canonical name are
    present, the canonical name wins (it is the authoritative spelling), so a
    profile cannot smuggle a wider value past the check under a second spelling.

    Args:
        source: A profile or ceiling snapshot keyed by human/schema field names.

    Returns:
        A dict keyed by canonical limit names (a subset of the four clamped
        limits present in ``source``).
    """
    normalized: dict[str, Any] = {}
    for raw_key, value in source.items():
        canonical = _CEILING_ALIASES.get(raw_key)
        if canonical is None:
            continue
        # Canonical spelling is authoritative; do not let an alias overwrite it.
        if canonical == raw_key or canonical not in normalized:
            normalized[canonical] = value
    return normalized


class CommitError(ValueError):
    """Raised when a commit request is invalid or its proposal is not live.

    The API layer maps this to a 4xx response. It is a ``ValueError`` subclass
    so existing ``except ValueError`` handlers keep working.
    """


def _utcnow() -> datetime:
    """Return the current UTC time (seam for tests)."""
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    """Return a short, sortable-enough opaque id with a typed prefix."""
    return f"{prefix}_{uuid.uuid4().hex}"


def _proposals_dir(broker: str) -> Path:
    """Return the per-broker pending-proposals directory."""
    return broker_dir(broker) / _PROPOSALS_DIRNAME


def _consent_dir(broker: str) -> Path:
    """Return the per-broker consent-records directory."""
    return broker_dir(broker) / _CONSENT_DIRNAME


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write ``payload`` as JSON to ``path`` atomically with 0600 perms.

    The parent directory is created 0700 and the file is written via a
    same-directory temp file + ``os.replace`` so a partial write can never leave
    a corrupt record a concurrent reader would misread.

    Args:
        path: Destination file path.
        payload: JSON-serializable mapping to persist.
    """
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        # Best-effort on platforms without POSIX perms (e.g. Windows).
        pass
    os.replace(tmp, path)


def _proposal_path(broker: str, proposal_id: str) -> Path:
    """Return the contained proposal path for a valid opaque proposal id."""
    if not _PROPOSAL_ID_RE.fullmatch(proposal_id):
        raise ValueError("proposal_id must be a bare mp_<32 hex> identifier")
    base = _proposals_dir(broker).resolve()
    path = (base / f"{proposal_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:  # pragma: no cover - regex is the primary guard
        raise ValueError("proposal_id escapes the proposals directory") from exc
    return path


# ---------------------------------------------------------------------------
# PROPOSE state — proposal persistence (read-only; grants no authority)
# ---------------------------------------------------------------------------


def save_proposal(proposal: Mapping[str, Any]) -> None:
    """Persist a synthesized proposal so a later commit can re-validate it.

    Called by the read-only ``propose_mandate_profiles`` tool. Writing a
    proposal is NOT a mandate write — it confers no trading authority; the
    proposal is merely the menu of clamped options the user picks from. The
    proposal record carries the ``ceilings_ref`` snapshot and the resolved
    limits of every profile, so :func:`commit_mandate` can verify the selected
    ordinal still fits the ceilings the user actually saw.

    Args:
        proposal: The ``mandate.proposal`` payload (must contain
            ``proposal_id``, ``account.broker``, ``ceilings_ref``, and
            ``profiles``).

    Raises:
        ValueError: If required keys are missing or the broker key is invalid.
    """
    proposal_id = str(proposal.get("proposal_id") or "").strip()
    if not proposal_id:
        raise ValueError("proposal must carry a proposal_id")
    broker = str((proposal.get("account") or {}).get("broker") or "").strip()
    if not broker:
        raise ValueError("proposal must carry account.broker")
    path = _proposal_path(broker, proposal_id)
    _atomic_write_json(path, dict(proposal))


def _load_proposal(broker: str, proposal_id: str) -> dict[str, Any] | None:
    """Load a persisted proposal, or ``None`` when absent/unreadable."""
    try:
        path = _proposal_path(broker, proposal_id)
    except ValueError as exc:
        logger.warning("proposal %s for %s is invalid: %s", proposal_id, broker, exc)
        return None
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("proposal %s for %s is unreadable: %s", proposal_id, broker, exc)
        return None
    return raw if isinstance(raw, dict) else None


def _invalidate_proposal(broker: str, proposal_id: str) -> None:
    """Delete a proposal so it can never be committed twice (idempotency)."""
    try:
        _proposal_path(broker, proposal_id).unlink()
    except (FileNotFoundError, ValueError):
        pass


# ---------------------------------------------------------------------------
# COMMIT state — the single mandate write
# ---------------------------------------------------------------------------


def _resolve_profile(
    proposal: Mapping[str, Any],
    ordinal: int,
    adjustments: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the selected profile, applying any per-commit adjustments.

    Adjustments may only *narrow* limits relative to the rendered profile;
    anything that would widen a limit is rejected (a commit may never authorize
    more than the user saw — widening goes back through PROPOSE, Consent §3).

    Args:
        proposal: The persisted proposal record.
        ordinal: 1-based ordinal of the selected profile.
        adjustments: Optional narrowing overrides keyed by profile field.

    Returns:
        The resolved profile dict.

    Raises:
        CommitError: If the ordinal is out of range or an adjustment widens a
            limit.
    """
    profiles = proposal.get("profiles") or []
    match = next((p for p in profiles if int(p.get("ordinal", -1)) == ordinal), None)
    if match is None:
        raise CommitError(f"selected_ordinal {ordinal} is not in proposal {proposal.get('proposal_id')!r}")

    resolved = dict(match)
    if adjustments:
        for key, value in adjustments.items():
            if key not in resolved:
                raise CommitError(f"adjustment {key!r} is not a field of the selected profile")
            current = resolved[key]
            if isinstance(current, (int, float)) and isinstance(value, (int, float)):
                if value > current:
                    raise CommitError(
                        f"adjustment {key!r}={value} widens the rendered limit {current}; "
                        "widening must go through a fresh proposal"
                    )
            resolved[key] = value
    return resolved


def _profile_fits_ceilings(profile: Mapping[str, Any], ceilings: Mapping[str, Any]) -> bool:
    """Return whether every clamped limit in ``profile`` is within ``ceilings``.

    Both sides are first normalized to canonical limit names (see
    :func:`_normalize_limits`) so the comparison is robust to alias spellings.
    Without this the check only compared keys that happened to share an IDENTICAL
    name on both sides — so a profile keyed ``max_order_usd`` against a ceiling
    keyed ``max_order_notional_usd`` was never checked at all, and an over-ceiling
    order notional committed silently (audit H9). After normalization a ceiling
    that does not bound a given field still imposes no constraint on it, but every
    field the propose step clamps IS re-checked here regardless of spelling. A
    cash-only ceiling (``leverage == "none"``) is enforced structurally: a profile
    may not request leverage the ceiling forbids.

    Args:
        profile: The resolved profile.
        ceilings: The ceiling snapshot recorded at propose time.

    Returns:
        ``True`` when the profile fits the ceilings.
    """
    prof = _normalize_limits(profile)
    caps = _normalize_limits(ceilings)
    for key, ceiling_value in caps.items():
        if key not in prof:
            continue
        prof_value = prof[key]
        if isinstance(ceiling_value, (int, float)) and isinstance(prof_value, (int, float)):
            if prof_value > ceiling_value:
                return False
        elif key == "leverage":
            # Cash-only ceiling forbids any leverage other than "none".
            if ceiling_value == "none" and prof_value not in ("none", None, 1, 1.0):
                return False
    return True


def commit_mandate(
    proposal_id: str,
    ordinal: int,
    adjustments: Mapping[str, Any] | None,
    consent_ack: bool,
    *,
    broker: str,
    account_ref: str = "",
    session_id: str | None = None,
    ceilings_ref: Mapping[str, Any] | None = None,
    lifetime_days: int = DEFAULT_MANDATE_LIFETIME_DAYS,
    flatten_on_halt: bool | None = None,
) -> dict[str, Any]:
    """Write a mandate — the ONLY code path that activates live-trading authority.

    Re-validates that ``proposal_id`` is live and that the resolved profile
    still fits the ceiling snapshot the user saw, then writes
    ``<runtime_root>/live/<broker>/mandate.json`` (0600) plus an immutable
    consent record. The committed proposal is invalidated so it can never be
    replayed. ``ConsentMeta.expires_at`` defaults to ``created_at + 30 days``.

    This function MUST stay unreachable from the agent loop / tool registry; it
    is invoked only by the surface commit endpoint, which supplies the
    surface-originated ``consent_ack`` (Consent §1 / §3).

    Args:
        proposal_id: Id of the proposal the user selected from.
        ordinal: 1-based ordinal of the chosen profile.
        adjustments: Optional narrowing overrides (Consent §3 adjust path).
        consent_ack: Explicit affirmative the surface sets on user action.
            **Must be ``True``** — a falsy value rejects the commit.
        broker: Broker key, e.g. ``"robinhood"``.
        account_ref: Opaque broker account identifier (never credentials).
        session_id: Originating session id, recorded in the consent record.
        ceilings_ref: Optional ceiling snapshot to validate against. When
            omitted, the snapshot stored on the proposal record is used (the
            authoritative one the user saw).
        lifetime_days: Mandate lifetime in days (default 30).
        flatten_on_halt: Whether a kill-switch trip flattens open positions
            (vs. cancel-only). ``None`` (the default — keeps this param
            backward-compatible for the surface endpoint) defers to the selected
            profile's ``flatten_on_halt`` field, which itself defaults to
            ``False`` (cancel-only, the safe default). An explicit bool overrides
            the profile. Persisted on the mandate and read on a halt trip by
            ``src.live.runtime.flatten`` (SPEC §7.5 #6).

    Returns:
        ``{"mandate_id", "consent_record_id", "broker", "expires_at",
        "resolved_profile"}``.

    Raises:
        CommitError: If ``consent_ack`` is not ``True``, the proposal is not
            live, the ordinal is invalid, an adjustment widens a limit, or the
            resolved profile exceeds the ceilings.
    """
    if consent_ack is not True:
        raise CommitError("commit requires an explicit consent_ack=true")

    proposal = _load_proposal(broker, proposal_id)
    if proposal is None:
        raise CommitError(f"proposal {proposal_id!r} is not live (already committed, expired, or unknown)")

    resolved = _resolve_profile(proposal, ordinal, adjustments)

    ceilings = dict(ceilings_ref) if ceilings_ref is not None else dict(proposal.get("ceilings") or {})
    if ceilings and not _profile_fits_ceilings(resolved, ceilings):
        raise CommitError("resolved profile exceeds the account ceilings — refusing to commit")

    created = _utcnow()
    expires = created + timedelta(days=max(1, int(lifetime_days)))
    created_iso = created.isoformat().replace("+00:00", "Z")
    expires_iso = expires.isoformat().replace("+00:00", "Z")

    # An explicit param wins; otherwise defer to the profile, which defaults to
    # cancel-only (the safe default) when it carries no flatten_on_halt field.
    do_flatten_on_halt = (
        bool(flatten_on_halt)
        if flatten_on_halt is not None
        else bool(resolved.get("flatten_on_halt", False))
    )

    mandate_id = _new_id("mandate")
    consent_record_id = _new_id("cr")

    # The consent token binds this mandate file to the exact human approval.
    token_material = f"{proposal_id}|{ordinal}|{consent_record_id}|{created_iso}"
    consent_token_sha256 = hashlib.sha256(token_material.encode("utf-8")).hexdigest()

    mandate_doc = {
        "schema_version": MANDATE_SCHEMA_VERSION,
        "mandate_id": mandate_id,
        "hard_caps": _profile_to_hard_caps(resolved),
        "universe": _profile_to_universe(resolved),
        # Top-level halt-behavior policy (not a quantitative ceiling): read by
        # the read-only loader onto Mandate.flatten_on_halt; absent => False.
        "flatten_on_halt": do_flatten_on_halt,
        "consent": {
            "created_at": created_iso,
            "consent_token_sha256": consent_token_sha256,
            "broker": broker,
            "account_ref": account_ref,
            "expires_at": expires_iso,
        },
    }
    _atomic_write_json(broker_dir(broker) / _MANDATE_FILENAME, mandate_doc)

    consent_record = {
        "consent_record_id": consent_record_id,
        "mandate_id": mandate_id,
        "proposal_id": proposal_id,
        "selected_ordinal": ordinal,
        "adjustments": dict(adjustments) if adjustments else None,
        "consent_ack": True,
        "session_id": session_id,
        "broker": broker,
        "account_ref": account_ref,
        "resolved_profile": resolved,
        "flatten_on_halt": do_flatten_on_halt,
        "ceilings_ref": proposal.get("ceilings_ref"),
        "created_at": created_iso,
        "expires_at": expires_iso,
    }
    _atomic_write_json(_consent_dir(broker) / f"{consent_record_id}.json", consent_record)

    # One-shot: the proposal can never be committed again.
    _invalidate_proposal(broker, proposal_id)

    logger.warning(
        "live mandate committed (broker=%s, mandate_id=%s, consent=%s, ordinal=%s)",
        broker,
        mandate_id,
        consent_record_id,
        ordinal,
    )
    return {
        "mandate_id": mandate_id,
        "consent_record_id": consent_record_id,
        "broker": broker,
        "expires_at": expires_iso,
        "resolved_profile": resolved,
    }


def _profile_to_hard_caps(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Map a clamped proposal profile to the mandate ``hard_caps`` section.

    The proposal profile uses the human-facing field names from the consent
    payload (``max_order_usd``, ``daily_trade_cap``, ``leverage``,
    ``instruments``); this normalizes them to the persisted mandate schema the
    read-only store/gate expect.

    Args:
        profile: The resolved proposal profile.

    Returns:
        A ``hard_caps`` dict in the persisted mandate schema.
    """
    leverage_raw = profile.get("leverage", "none")
    max_leverage = 1.0 if leverage_raw in ("none", None) else float(leverage_raw)
    instruments = list(profile.get("instruments") or ["equity"])
    funding = float(profile.get("account_funding_usd", profile.get("max_total_exposure_usd", 0.0)) or 0.0)
    max_order = float(profile.get("max_order_usd", 0.0) or 0.0)
    max_exposure = float(profile.get("max_total_exposure_usd", funding or max_order) or max_order)
    return {
        "account_funding_usd": funding or max_exposure,
        "max_order_notional_usd": max_order,
        "max_total_exposure_usd": max_exposure,
        "max_leverage": max_leverage,
        "allowed_instruments": instruments,
        "max_trades_per_day": int(profile.get("daily_trade_cap", 0) or 0),
    }


def _profile_to_universe(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Map a clamped proposal profile to the mandate ``universe`` section.

    Args:
        profile: The resolved proposal profile.

    Returns:
        A ``universe`` dict in the persisted mandate schema.
    """
    return {
        "asset_classes": list(profile.get("asset_classes") or ["us_equity"]),
        "min_market_cap_usd": profile.get("min_market_cap_usd"),
        "min_avg_daily_volume_usd": profile.get("min_avg_daily_volume_usd"),
        "exclude_symbols": list(profile.get("exclude_symbols") or []),
    }
