"""Consent backend: propose -> select -> commit state machine + invariants.

Covers (live-trading SPEC, Consent §1/§3, Mandate §2):

* PROPOSE -> SELECT -> COMMIT happy path, then the mandate loads back.
* commit-is-the-only-write: an AST + registry scan proves no agent tool / tool
  registry path reaches ``commit_mandate`` (the 命门 invariant).
* Adjust round-trip (narrowing) and reauth-seeded proposal round-trip.
* Commit rejected without ``consent_ack=true`` and once a proposal is consumed.
"""

from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path

import pytest

import src.live.paths as paths
from src.live.mandate.commit import (
    CommitError,
    DEFAULT_MANDATE_LIFETIME_DAYS,
    commit_mandate,
    save_proposal,
)
from src.live.mandate.store import load_mandate
from src.tools.propose_mandate_tool import ProposeMandateProfilesTool

pytestmark = pytest.mark.unit

AGENT_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live root at a tmp dir so tests never touch the real store."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


_CEILINGS = {
    "account_funding_usd": 5000.0,
    "max_order_usd": 1500.0,
    "max_total_exposure_usd": 5000.0,
    "daily_trade_cap": 10,
    "leverage": "none",
    "instruments": ["equity"],
    "universe": ["AAPL", "MSFT", "NVDA", "GOOGL"],
}


def _propose(broker: str = "robinhood", reauth_for=None) -> dict:
    """Run the propose tool and return the parsed proposal payload."""
    tool = ProposeMandateProfilesTool()
    raw = tool.execute(
        broker=broker,
        intent="aggressive tech, ~$5000",
        ceilings=dict(_CEILINGS),
        session_id="sess_1",
        reauth_for=reauth_for,
    )
    payload = json.loads(raw)
    assert payload.get("type") == "mandate.proposal", payload
    return payload


# ---------------------------------------------------------------------------
# PROPOSE
# ---------------------------------------------------------------------------


def test_propose_is_readonly_and_clamps_to_ceilings(live_runtime: Path) -> None:
    """The tool is read-only and every profile clamps to the ceiling."""
    assert ProposeMandateProfilesTool.is_readonly is True
    proposal = _propose()

    assert 2 <= len(proposal["profiles"]) <= 4
    for profile in proposal["profiles"]:
        assert profile["max_order_usd"] <= _CEILINGS["max_order_usd"]
        assert profile["daily_trade_cap"] <= _CEILINGS["daily_trade_cap"]
        # Cash-only ceiling => no profile may request leverage.
        assert profile["leverage"] == "none"
    assert "funding_note" in proposal and "halt_note" in proposal
    assert proposal["account"]["type"] == "cash"


def test_propose_persists_for_commit(live_runtime: Path) -> None:
    """A proposal is persisted under the broker's proposals dir (not a mandate)."""
    proposal = _propose()
    proposals_dir = paths.broker_dir("robinhood") / "proposals"
    saved = proposals_dir / f"{proposal['proposal_id']}.json"
    assert saved.is_file()
    # Persisting a proposal must NOT have written a mandate.
    assert load_mandate("robinhood") is None


# ---------------------------------------------------------------------------
# COMMIT happy path
# ---------------------------------------------------------------------------


def test_propose_select_commit_activates_mandate(live_runtime: Path) -> None:
    """End-to-end: propose -> pick ordinal 2 -> commit -> mandate loads back."""
    proposal = _propose()
    result = commit_mandate(
        proposal_id=proposal["proposal_id"],
        ordinal=2,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
        account_ref="rh_acct_opaque",
        session_id="sess_1",
    )
    assert result["mandate_id"].startswith("mandate_")
    assert result["consent_record_id"].startswith("cr_")
    assert result["broker"] == "robinhood"

    mandate = load_mandate("robinhood")
    assert mandate is not None
    picked = next(p for p in proposal["profiles"] if p["ordinal"] == 2)
    assert mandate.hard_caps.max_order_notional_usd == picked["max_order_usd"]
    assert mandate.hard_caps.max_trades_per_day == picked["daily_trade_cap"]
    assert mandate.consent.account_ref == "rh_acct_opaque"
    # 30-day default lifetime.
    created = datetime.fromisoformat(mandate.consent.created_at.replace("Z", "+00:00"))
    expires = datetime.fromisoformat(mandate.consent.expires_at.replace("Z", "+00:00"))
    assert (expires - created).days == DEFAULT_MANDATE_LIFETIME_DAYS

    # A consent record was written before the mandate could be used.
    consent_dir = paths.broker_dir("robinhood") / "consent"
    records = list(consent_dir.glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["proposal_id"] == proposal["proposal_id"]
    assert record["selected_ordinal"] == 2
    assert record["consent_ack"] is True


def test_commit_consumes_proposal_no_replay(live_runtime: Path) -> None:
    """A committed proposal is invalidated and cannot be committed again."""
    proposal = _propose()
    commit_mandate(
        proposal_id=proposal["proposal_id"],
        ordinal=1,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
    )
    with pytest.raises(CommitError, match="not live"):
        commit_mandate(
            proposal_id=proposal["proposal_id"],
            ordinal=1,
            adjustments=None,
            consent_ack=True,
            broker="robinhood",
        )


# ---------------------------------------------------------------------------
# consent_ack gate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ack", [False, None, 0, "", "true"])
def test_commit_rejected_without_consent_ack(live_runtime: Path, ack) -> None:
    """Only a strict boolean True authorizes a commit (no truthy coercion)."""
    proposal = _propose()
    with pytest.raises(CommitError, match="consent_ack"):
        commit_mandate(
            proposal_id=proposal["proposal_id"],
            ordinal=1,
            adjustments=None,
            consent_ack=ack,  # type: ignore[arg-type]
            broker="robinhood",
        )
    # Failed commit wrote no mandate (fail-closed) and left the proposal live.
    assert load_mandate("robinhood") is None
    assert (paths.broker_dir("robinhood") / "proposals" / f"{proposal['proposal_id']}.json").is_file()


# ---------------------------------------------------------------------------
# ADJUST + REAUTH
# ---------------------------------------------------------------------------


def test_adjust_narrowing_round_trip(live_runtime: Path) -> None:
    """Adjust narrows a limit; the narrowed value is what gets committed."""
    proposal = _propose()
    picked = next(p for p in proposal["profiles"] if p["ordinal"] == 3)
    narrower_daily = max(1, picked["daily_trade_cap"] - 1)
    commit_mandate(
        proposal_id=proposal["proposal_id"],
        ordinal=3,
        adjustments={"daily_trade_cap": narrower_daily},
        consent_ack=True,
        broker="robinhood",
    )
    mandate = load_mandate("robinhood")
    assert mandate is not None
    assert mandate.hard_caps.max_trades_per_day == narrower_daily


def test_adjust_widening_rejected(live_runtime: Path) -> None:
    """An adjustment that widens a rendered limit is rejected (must re-propose)."""
    proposal = _propose()
    picked = next(p for p in proposal["profiles"] if p["ordinal"] == 1)
    with pytest.raises(CommitError, match="widen"):
        commit_mandate(
            proposal_id=proposal["proposal_id"],
            ordinal=1,
            adjustments={"daily_trade_cap": picked["daily_trade_cap"] + 99},
            consent_ack=True,
            broker="robinhood",
        )


def test_reauth_seeded_proposal_round_trip(live_runtime: Path) -> None:
    """A breach-seeded proposal carries reauth_for and still clamps to ceiling."""
    proposal = _propose(
        reauth_for={"breach_id": "be_1", "limit": "max_order_notional_usd", "attempted_value": 1200.0}
    )
    assert proposal["reauth_for"]["breach_id"] == "be_1"
    for profile in proposal["profiles"]:
        assert profile["max_order_usd"] <= _CEILINGS["max_order_usd"]

    # The widened proposal commits exactly like any other proposal.
    result = commit_mandate(
        proposal_id=proposal["proposal_id"],
        ordinal=3,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
    )
    assert result["mandate_id"]
    assert load_mandate("robinhood") is not None


# ---------------------------------------------------------------------------
# H9: commit-time ceiling re-check is alias-robust (no silent NO-OP)
# ---------------------------------------------------------------------------


def _save_handcrafted_proposal(
    broker: str,
    profile: dict,
    ceilings: dict,
) -> str:
    """Persist a proposal with an arbitrary single profile + ceiling snapshot.

    Lets a test exercise commit-time validation against a profile the clamping
    proposer would never emit (e.g. one that breaches an alias-keyed ceiling).
    """
    proposal_id = "mp_" + "9" * 32
    save_proposal(
        {
            "type": "mandate.proposal",
            "proposal_id": proposal_id,
            "account": {"broker": broker, "type": "cash", "funded_by": "user"},
            "ceilings_ref": "caps_h9",
            "ceilings": ceilings,
            "profiles": [profile],
        }
    )
    return proposal_id


def test_commit_rejects_profile_over_alias_keyed_order_ceiling(live_runtime: Path) -> None:
    """H9: an order notional over an ALIAS-keyed ceiling is rejected at commit.

    The profile stores the limit as ``max_order_usd`` while the ceiling snapshot
    keys it ``max_order_notional_usd`` (the schema spelling). Before the fix the
    re-check only compared identically-named keys, so it never saw this field and
    the over-ceiling profile committed silently. After normalization both sides
    map to the canonical name and the breach is caught.
    """
    profile = {
        "ordinal": 1,
        "label": "rogue",
        "max_order_usd": 999_999.0,  # human/profile spelling
        "max_total_exposure_usd": 5000.0,
        "daily_trade_cap": 2,
        "leverage": "none",
        "instruments": ["equity"],
    }
    ceilings = {
        "account_funding_usd": 5000.0,
        "max_order_notional_usd": 100.0,  # schema/alias spelling, far below profile
        "max_total_exposure_usd": 5000.0,
        "max_trades_per_day": 10,
        "leverage": "none",
        "allowed_instruments": ["equity"],
    }
    proposal_id = _save_handcrafted_proposal("robinhood", profile, ceilings)

    with pytest.raises(CommitError, match="exceeds the account ceilings"):
        commit_mandate(
            proposal_id=proposal_id,
            ordinal=1,
            adjustments=None,
            consent_ack=True,
            broker="robinhood",
        )
    # Fail-closed: no mandate written.
    assert load_mandate("robinhood") is None


def test_commit_rejects_profile_over_alias_keyed_daily_cap(live_runtime: Path) -> None:
    """H9 (daily cap): profile ``daily_trade_cap`` over ceiling ``max_trades_per_day``."""
    profile = {
        "ordinal": 1,
        "label": "rogue",
        "max_order_usd": 50.0,
        "max_total_exposure_usd": 5000.0,
        "daily_trade_cap": 500,  # human spelling, way over
        "leverage": "none",
        "instruments": ["equity"],
    }
    ceilings = {
        "account_funding_usd": 5000.0,
        "max_order_notional_usd": 5000.0,
        "max_total_exposure_usd": 5000.0,
        "max_trades_per_day": 3,  # schema spelling
        "leverage": "none",
        "allowed_instruments": ["equity"],
    }
    proposal_id = _save_handcrafted_proposal("robinhood", profile, ceilings)

    with pytest.raises(CommitError, match="exceeds the account ceilings"):
        commit_mandate(
            proposal_id=proposal_id,
            ordinal=1,
            adjustments=None,
            consent_ack=True,
            broker="robinhood",
        )
    assert load_mandate("robinhood") is None


def test_commit_accepts_within_alias_keyed_ceiling(live_runtime: Path) -> None:
    """A profile that fits an alias-keyed ceiling still commits (no over-rejection)."""
    profile = {
        "ordinal": 1,
        "label": "fits",
        "max_order_usd": 90.0,
        "max_total_exposure_usd": 5000.0,
        "daily_trade_cap": 2,
        "leverage": "none",
        "instruments": ["equity"],
    }
    ceilings = {
        "account_funding_usd": 5000.0,
        "max_order_notional_usd": 100.0,
        "max_total_exposure_usd": 5000.0,
        "max_trades_per_day": 10,
        "leverage": "none",
        "allowed_instruments": ["equity"],
    }
    proposal_id = _save_handcrafted_proposal("robinhood", profile, ceilings)
    result = commit_mandate(
        proposal_id=proposal_id,
        ordinal=1,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
    )
    assert result["mandate_id"]
    assert load_mandate("robinhood") is not None


# ---------------------------------------------------------------------------
# M3: per-mandate flatten_on_halt flag is proposed + persisted on commit
# ---------------------------------------------------------------------------


def test_propose_defaults_flatten_on_halt_false(live_runtime: Path) -> None:
    """Every proposed profile carries flatten_on_halt=False by default (cancel-only)."""
    proposal = _propose()
    for profile in proposal["profiles"]:
        assert profile["flatten_on_halt"] is False


def test_propose_opt_in_flatten_on_halt_stamps_profiles(live_runtime: Path) -> None:
    """An explicit opt-in stamps flatten_on_halt=True onto every profile."""
    tool = ProposeMandateProfilesTool()
    payload = json.loads(
        tool.execute(
            broker="robinhood",
            ceilings=dict(_CEILINGS),
            flatten_on_halt=True,
        )
    )
    for profile in payload["profiles"]:
        assert profile["flatten_on_halt"] is True


def test_commit_persists_flatten_on_halt_from_profile(live_runtime: Path) -> None:
    """An opted-in proposal commits a mandate.json carrying flatten_on_halt=True."""
    tool = ProposeMandateProfilesTool()
    payload = json.loads(
        tool.execute(broker="robinhood", ceilings=dict(_CEILINGS), flatten_on_halt=True)
    )
    commit_mandate(
        proposal_id=payload["proposal_id"],
        ordinal=2,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
    )
    doc = json.loads((paths.broker_dir("robinhood") / "mandate.json").read_text(encoding="utf-8"))
    assert doc["flatten_on_halt"] is True
    # And the consent record records the same decision for audit.
    record_path = next((paths.broker_dir("robinhood") / "consent").glob("*.json"))
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["flatten_on_halt"] is True


def test_commit_defaults_flatten_on_halt_false_for_cancel_only(live_runtime: Path) -> None:
    """A plain proposal (no opt-in) commits flatten_on_halt=False (cancel-only)."""
    proposal = _propose()
    commit_mandate(
        proposal_id=proposal["proposal_id"],
        ordinal=1,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
    )
    doc = json.loads((paths.broker_dir("robinhood") / "mandate.json").read_text(encoding="utf-8"))
    assert doc["flatten_on_halt"] is False


def test_commit_explicit_flatten_param_overrides_profile(live_runtime: Path) -> None:
    """An explicit flatten_on_halt param overrides the selected profile's flag."""
    proposal = _propose()  # profiles default flatten_on_halt=False
    commit_mandate(
        proposal_id=proposal["proposal_id"],
        ordinal=1,
        adjustments=None,
        consent_ack=True,
        broker="robinhood",
        flatten_on_halt=True,
    )
    doc = json.loads((paths.broker_dir("robinhood") / "mandate.json").read_text(encoding="utf-8"))
    assert doc["flatten_on_halt"] is True


# ---------------------------------------------------------------------------
# 命门 INVARIANT: commit is unreachable from the agent loop / tool registry
# ---------------------------------------------------------------------------


def test_propose_tool_is_a_basetool_but_commit_is_not() -> None:
    """The proposer is a registerable tool; the committer is a plain function."""
    from src.agent.tools import BaseTool
    import src.live.mandate.commit as commit_mod

    assert issubclass(ProposeMandateProfilesTool, BaseTool)
    # No BaseTool subclass lives in the commit module — it can never be
    # auto-discovered by the registry.
    for value in vars(commit_mod).values():
        if isinstance(value, type) and issubclass(value, BaseTool):
            pytest.fail(f"{value!r} in commit.py is a BaseTool — commit must not be a tool")


def test_no_registered_tool_references_commit_mandate() -> None:
    """Build the real registry; assert no tool module imports commit_mandate.

    The mandate writer must be structurally unreachable from anything the agent
    loop can call. We AST-scan every tool source file (plus the loop/worker) for
    an import of or call to ``commit_mandate`` / ``save_proposal``-as-mandate.
    Importing ``save_proposal`` is allowed (a proposal grants no authority); a
    reference to ``commit_mandate`` from a tool/loop module is a hard failure.
    """
    suspect_files = list((AGENT_DIR / "src" / "tools").glob("*.py"))
    suspect_files += [
        AGENT_DIR / "src" / "agent" / "loop.py",
        AGENT_DIR / "src" / "swarm" / "worker.py",
    ]
    offenders: list[str] = []
    for path in suspect_files:
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("mandate.commit"):
                names = {alias.name for alias in node.names}
                if "commit_mandate" in names or "CommitError" in names:
                    offenders.append(f"{path.name} imports commit_mandate")
            if isinstance(node, ast.Name) and node.id == "commit_mandate":
                offenders.append(f"{path.name} references commit_mandate")
            if isinstance(node, ast.Attribute) and node.attr == "commit_mandate":
                offenders.append(f"{path.name} references .commit_mandate")
    assert not offenders, f"commit_mandate is reachable from the agent surface: {offenders}"


def test_registry_has_propose_tool_but_no_mandate_writer() -> None:
    """The assembled registry exposes propose_mandate_profiles, no commit tool."""
    from src.tools import build_registry

    registry = build_registry()
    names = set(registry.tool_names)
    assert "propose_mandate_profiles" in names
    for forbidden in ("commit_mandate", "set_mandate", "write_mandate", "authorize_live"):
        assert forbidden not in names, f"{forbidden} must not be a registered tool"
