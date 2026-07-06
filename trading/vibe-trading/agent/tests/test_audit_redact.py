"""Tests for the live-action audit ledger (src/live/audit.py, SPEC Consent §5).

Focus: every record is redacted BEFORE it touches the ledger or the SSE bus, the
ledger is append-only, and the accountability refs (mandate/consent) survive
redaction so the chain back to the authorizing user click stays intact.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.live import audit
from src.live import paths
from src.live.audit import LiveActionEvent, write_live_action


@pytest.fixture
def live_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the live runtime root at an isolated tmp dir."""
    monkeypatch.setattr(paths, "get_runtime_root", lambda: tmp_path)
    return tmp_path


def _read_ledger() -> list[dict]:
    lines = audit.audit_ledger_path().read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_credentials_redacted_before_write(live_runtime: Path) -> None:
    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        remote_tool="place_order",
        intent_normalized="buy 3 NVDA @ market",
        mandate_snapshot_ref="mandate_01",
        consent_record_ref="cr_01",
        broker_request={
            "symbol": "NVDA",
            "qty": 3,
            "authorization": "Bearer super-secret-jwt",
            "access_token": "rh-oauth-token-xyz",
            "api_key": "ak_live_123",
        },
        broker_response={"order_id": "rh_1", "state": "accepted"},
    )
    returned = write_live_action(event)
    written = _read_ledger()
    assert len(written) == 1
    rec = written[0]

    # The function returns exactly what it wrote (for the SSE emit).
    assert returned == rec

    req = rec["broker_request"]
    # Credential-class keys are scrubbed (authorization / *_token / api_key).
    assert req["authorization"] == "[redacted]"
    assert req["access_token"] == "[redacted]"
    assert req["api_key"] == "[redacted]"
    # Non-sensitive order fields are preserved.
    assert req["symbol"] == "NVDA"
    assert req["qty"] == 3

    # The accountability chain survives redaction.
    assert rec["mandate_snapshot_ref"] == "mandate_01"
    assert rec["consent_record_ref"] == "cr_01"
    assert rec["intent_normalized"] == "buy 3 NVDA @ market"
    assert rec["server"] == "robinhood"
    assert rec["remote_tool"] == "place_order"


def test_event_not_mutated_by_redaction(live_runtime: Path) -> None:
    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        broker_request={"token": "leak-me"},
    )
    write_live_action(event)
    # The frozen event's original payload is untouched; only the written record
    # is redacted.
    assert event.broker_request == {"token": "leak-me"}


def test_ledger_is_append_only(live_runtime: Path) -> None:
    for i in range(3):
        write_live_action(
            LiveActionEvent(
                kind="order_placed",
                session_id="s1",
                outcome="accepted",
                server="robinhood",
                intent_normalized=f"order {i}",
            )
        )
    written = _read_ledger()
    assert len(written) == 3
    assert [r["intent_normalized"] for r in written] == ["order 0", "order 1", "order 2"]


def test_auto_ids_and_timestamp(live_runtime: Path) -> None:
    write_live_action(
        LiveActionEvent(
            kind="halt_tripped",
            session_id="s1",
            outcome="blocked",
            server="robinhood",
        )
    )
    rec = _read_ledger()[0]
    assert rec["audit_id"].startswith("la_")
    # ms-precision UTC ISO-8601.
    assert rec["ts"].endswith("+00:00") or rec["ts"].endswith("Z")
    assert "." in rec["ts"]


def test_directory_created_on_first_write(live_runtime: Path) -> None:
    assert not audit.audit_ledger_path().exists()
    write_live_action(
        LiveActionEvent(
            kind="mandate_committed",
            session_id="s1",
            outcome="accepted",
            server="robinhood",
        )
    )
    assert audit.audit_ledger_path().exists()


def test_account_number_and_pii_redacted_but_provenance_kept(live_runtime: Path) -> None:
    """H1: account numbers / SSN inside broker payloads are scrubbed, while the
    opaque ``account_ref`` provenance (mandate→consent chain, SPEC §5) survives.

    Pre-fix this FAILS — ``redact_payload`` only scrubbed credential markers, so
    ``account_number`` / ``ssn`` / ``routing_number`` passed through RAW.
    """
    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        remote_tool="place_order",
        broker_request={
            "symbol": "NVDA",
            "qty": 3,
            "account_number": "5XX111222",
            "routing_number": "021000021",
        },
        broker_response={
            "order_id": "rh_1",
            "state": "accepted",
            "account_id": "acct-abc-123",
            "account_url": "https://api.robinhood.com/accounts/5XX111222/",
            "ssn": "123-45-6789",
            "tax_id": "98-7654321",
            # An opaque per-record broker reference kept for traceability.
            "account_ref": "rh_ref_opaque_keepme",
        },
    )
    rec = write_live_action(event)

    req = rec["broker_request"]
    assert req["account_number"] == "[redacted]"
    assert req["routing_number"] == "[redacted]"
    assert req["symbol"] == "NVDA"  # benign field preserved
    assert req["qty"] == 3

    resp = rec["broker_response"]
    assert resp["account_id"] == "[redacted]"
    assert resp["account_url"] == "[redacted]"
    assert resp["ssn"] == "[redacted]"
    assert resp["tax_id"] == "[redacted]"
    # Provenance reference is intentionally NOT redacted.
    assert resp["account_ref"] == "rh_ref_opaque_keepme"
    # Benign response fields preserved.
    assert resp["order_id"] == "rh_1"
    assert resp["state"] == "accepted"


class _RecordingTrace:
    """Minimal TraceWriter-shaped sink that records the entries it receives."""

    def __init__(self) -> None:
        self.entries: list[dict] = []

    def write(self, entry: dict) -> None:
        self.entries.append(entry)


def test_trace_writer_sink_receives_live_action_type(live_runtime: Path) -> None:
    """H5 sink 2: when a trace_writer is passed it gets the redacted record
    tagged ``type="live_action"``, alongside tool_call/tool_result."""
    trace = _RecordingTrace()
    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        broker_request={"symbol": "AAPL", "token": "leak-me", "account_number": "999"},
    )
    rec = write_live_action(event, trace_writer=trace)

    assert len(trace.entries) == 1
    entry = trace.entries[0]
    assert entry["type"] == "live_action"
    # Redacted BEFORE the trace sink — no secret/account number leaks.
    assert entry["broker_request"]["token"] == "[redacted]"
    assert entry["broker_request"]["account_number"] == "[redacted]"
    assert entry["broker_request"]["symbol"] == "AAPL"
    # The trace entry carries the same record fields as the returned dict.
    assert entry["audit_id"] == rec["audit_id"]
    assert entry["kind"] == "order_placed"


def test_event_callback_sink_called_with_redacted_record(live_runtime: Path) -> None:
    """H5 sink 3: event_callback fires with ("live.action", redacted_record)."""
    captured: list[tuple] = []

    def cb(name: str, payload: dict) -> None:
        captured.append((name, payload))

    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        broker_request={"symbol": "MSFT", "ssn": "111-22-3333"},
    )
    rec = write_live_action(event, event_callback=cb)

    assert len(captured) == 1
    name, payload = captured[0]
    assert name == "live.action"
    assert payload == rec
    # Redacted before the surface sees it.
    assert payload["broker_request"]["ssn"] == "[redacted]"
    assert payload["broker_request"]["symbol"] == "MSFT"


def test_redaction_happens_before_all_sinks(live_runtime: Path) -> None:
    """All three sinks (ledger, trace, callback) receive the SAME redacted dict;
    nothing sees the raw secret/account number."""
    trace = _RecordingTrace()
    captured: list[dict] = []
    event = LiveActionEvent(
        kind="order_placed",
        session_id="s1",
        outcome="accepted",
        server="robinhood",
        broker_request={"authorization": "Bearer x", "account_number": "777", "qty": 1},
    )
    rec = write_live_action(
        event,
        trace_writer=trace,
        event_callback=lambda _n, p: captured.append(p),
    )

    ledger_rec = _read_ledger()[0]
    trace_req = trace.entries[0]["broker_request"]
    cb_req = captured[0]["broker_request"]
    for req in (rec["broker_request"], ledger_rec["broker_request"], trace_req, cb_req):
        assert req["authorization"] == "[redacted]"
        assert req["account_number"] == "[redacted]"
        assert req["qty"] == 1


def test_optional_sinks_skipped_when_absent_backward_compat(live_runtime: Path) -> None:
    """Backward compat: write_live_action(event) with no kwargs still works and
    writes ONLY the ledger (no trace, no callback)."""
    rec = write_live_action(
        LiveActionEvent(
            kind="order_placed",
            session_id="s1",
            outcome="accepted",
            server="robinhood",
            intent_normalized="ledger only",
        )
    )
    written = _read_ledger()
    assert len(written) == 1
    assert written[0]["intent_normalized"] == "ledger only"
    assert written[0] == rec


def test_ledger_still_append_only_with_sinks(live_runtime: Path) -> None:
    """Trace/callback sinks do not disturb the append-only ledger semantics."""
    trace = _RecordingTrace()
    for i in range(3):
        write_live_action(
            LiveActionEvent(
                kind="order_placed",
                session_id="s1",
                outcome="accepted",
                server="robinhood",
                intent_normalized=f"order {i}",
            ),
            trace_writer=trace,
            event_callback=lambda _n, _p: None,
        )
    written = _read_ledger()
    assert [r["intent_normalized"] for r in written] == ["order 0", "order 1", "order 2"]
    assert len(trace.entries) == 3
