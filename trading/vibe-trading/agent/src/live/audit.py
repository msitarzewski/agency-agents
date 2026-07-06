"""Live-action audit ledger (SPEC.md Consent §5).

Every live action — order placed, order rejected by the gate, mandate committed,
breach raised, kill switch tripped/cleared — appends one immutable record to a
dedicated, append-only ledger at ``<runtime_root>/live/audit.jsonl``. This ledger
is segregated from per-run research traces because it is the compliance-grade
record that must survive run-dir cleanup: the canonical answer to "show me
everything the agent did with real money."

``mandate_snapshot_ref`` + ``consent_record_ref`` together make every live order
traceable back to the exact user click that authorized the mandate it ran under —
the core accountability chain.

**Three sinks (SPEC §5).** Every redacted record fans out to up to three
append-only destinations: (1) the dedicated compliance ledger above; (2) the
per-run ``TraceWriter`` (``type="live_action"``, sitting alongside
``tool_call`` / ``tool_result`` in the run dir) when one is supplied; and (3)
the surfacing ``event_callback`` (``"live.action"``) so the CLI/frontend can
render the action inline. Sinks 2 and 3 are optional — when absent they are
silently skipped — and the dedicated ledger is always written.

**Redaction (SPEC §5 / #142 shared helper).** Broker requests/responses can carry
OAuth tokens, account numbers, and PII. Every record is scrubbed through
:func:`src.tools.redaction.redact_payload` BEFORE it is written to ANY sink,
so sensitive values are ``[redacted]`` before they reach the trace, the live
ledger, or the SSE bus. The opaque ``account_ref`` provenance carried by the
authorizing mandate is intentionally NOT a record field here and is preserved
elsewhere as the mandate→consent accountability chain.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from src.live.paths import live_root
from src.tools.redaction import redact_payload

logger = logging.getLogger(__name__)

#: SSE / surface event name for a live-action record (SPEC §5).
_LIVE_ACTION_EVENT = "live.action"

#: Trace record type, so live actions sit alongside ``tool_call`` /
#: ``tool_result`` in the per-run trace (SPEC §5).
_LIVE_ACTION_TRACE_TYPE = "live_action"


class _TraceWriterLike(Protocol):
    """Structural type for the per-run trace sink.

    Matches :class:`src.agent.trace.TraceWriter` without importing the
    protected agent core into the live module.
    """

    def write(self, entry: dict[str, Any]) -> None: ...


#: Surface callback shape: ``event_callback(event_name, payload)`` — the same
#: bus that already carries ``tool_call`` / ``tool_result`` (SPEC §5).
EventCallback = Callable[[str, dict[str, Any]], Any]

_LEDGER_FILENAME = "audit.jsonl"

#: Canonical live-action kinds (SPEC §5).
LiveActionKind = Literal[
    "order_placed",
    "order_cancelled",
    "order_rejected",
    "mandate_committed",
    "breach",
    "halt_tripped",
    "halt_cleared",
]

#: Canonical outcomes (SPEC §5).
LiveActionOutcome = Literal["accepted", "filled", "rejected", "error", "blocked"]


def _new_audit_id() -> str:
    """Return a fresh unique audit id with the ``la_`` prefix (SPEC §5)."""
    return f"la_{uuid.uuid4().hex}"


def _utc_now_iso_ms() -> str:
    """Return the current UTC time as an ISO-8601 string with ms precision."""
    now = datetime.now(timezone.utc)
    return now.isoformat(timespec="milliseconds")


def audit_ledger_path() -> Path:
    """Return the path to the dedicated live-action ledger.

    Returns:
        ``<runtime_root>/live/audit.jsonl``. The file/parent is NOT created here;
        :func:`write_live_action` creates the directory on first append.
    """
    return live_root() / _LEDGER_FILENAME


@dataclass(frozen=True)
class LiveActionEvent:
    """One immutable live-action audit record (SPEC.md Consent §5).

    Attributes:
        kind: The live-action kind (``order_placed`` | ``order_rejected`` |
            ``mandate_committed`` | ``breach`` | ``halt_tripped`` |
            ``halt_cleared``).
        session_id: Originating session id.
        outcome: Action outcome (``accepted`` | ``filled`` | ``rejected`` |
            ``error`` | ``blocked``).
        server: Origin server / broker key, e.g. ``"robinhood"`` (#142 origin
            metadata, reused).
        remote_tool: Broker remote tool name invoked, e.g. ``"place_order"``.
        intent_normalized: Human-readable normalized intent,
            e.g. ``"buy 3 NVDA @ market"``.
        mandate_snapshot_ref: Which mandate authorized the action — the first
            half of the accountability chain.
        consent_record_ref: Which user consent authorized that mandate — the
            second half of the accountability chain.
        broker_request: Raw request sent to the broker. **Redacted** before
            write/emit.
        broker_response: Raw broker response. **Redacted** before write/emit.
        gate_decision: The enforcement gate's verdict, e.g.
            ``{"allowed": True, "checked_limits": [...]}``.
        error: Error description when ``outcome == "error"``, else ``None``.
        audit_id: Unique id (``la_<hex>``); auto-generated when omitted.
        ts: ISO-8601 UTC timestamp (ms precision); auto-generated when omitted.
    """

    kind: LiveActionKind
    session_id: str
    outcome: LiveActionOutcome
    server: str
    remote_tool: str | None = None
    intent_normalized: str | None = None
    mandate_snapshot_ref: str | None = None
    consent_record_ref: str | None = None
    broker_request: dict[str, Any] | None = None
    broker_response: dict[str, Any] | None = None
    gate_decision: dict[str, Any] | None = None
    error: str | None = None
    audit_id: str = field(default_factory=_new_audit_id)
    ts: str = field(default_factory=_utc_now_iso_ms)

    def to_record(self) -> dict[str, Any]:
        """Return the redacted, JSON-serializable record for this event.

        Sensitive keys anywhere in the structure (notably inside
        ``broker_request`` / ``broker_response``) are replaced with
        ``[redacted]`` via :func:`src.tools.redaction.redact_payload`. The
        field order matches the SPEC §5 schema for readability.

        Returns:
            A new dict safe to append to the ledger and emit on the SSE bus. The
            event itself is never mutated.
        """
        record: dict[str, Any] = {
            "audit_id": self.audit_id,
            "ts": self.ts,
            "session_id": self.session_id,
            "kind": self.kind,
            "intent_normalized": self.intent_normalized,
            "mandate_snapshot_ref": self.mandate_snapshot_ref,
            "consent_record_ref": self.consent_record_ref,
            "broker_request": self.broker_request,
            "broker_response": self.broker_response,
            "outcome": self.outcome,
            "gate_decision": self.gate_decision,
            "server": self.server,
            "remote_tool": self.remote_tool,
            "error": self.error,
        }
        return redact_payload(record)


def write_live_action(
    event: LiveActionEvent,
    *,
    event_callback: EventCallback | None = None,
    trace_writer: _TraceWriterLike | None = None,
) -> dict[str, Any]:
    """Fan a redacted live-action record out to up to three sinks (SPEC §5).

    The record is redacted via :func:`src.tools.redaction.redact_payload` FIRST,
    before any write or emit, so OAuth tokens / account numbers / PII never reach
    the ledger, the trace, or a surface. The SAME redacted dict is then sent to
    every configured sink:

    1. **Dedicated ledger** (always) — appended as single-line JSONL with a
       trailing newline to ``<runtime_root>/live/audit.jsonl``, opened in append
       mode so concurrent writers cannot truncate it (append-only). The directory
       tree is created ``0700`` on first write.
    2. **Per-run trace** (when ``trace_writer`` is given) — written via
       ``trace_writer.write({...})`` with ``type="live_action"`` so it sits
       alongside ``tool_call`` / ``tool_result`` in the run dir.
    3. **Surface** (when ``event_callback`` is given) — called as
       ``event_callback("live.action", record)`` so the CLI / frontend renders
       the action inline. Notifications never gate autonomy (SPEC §5).

    Optional sinks are silently skipped when not supplied, preserving backward
    compatibility with ledger-only callers (``write_live_action(event)``).

    Args:
        event: The live-action event to record.
        event_callback: Optional surface bus ``(event_name, payload)`` callable;
            skipped when ``None``.
        trace_writer: Optional per-run trace sink exposing ``write(dict)``;
            skipped when ``None``.

    Returns:
        The redacted record dict — identical to what was written to every sink —
        for the caller to embed or re-emit.
    """
    record = event.to_record()

    # Sink 1: dedicated compliance ledger (always, append-only).
    path = audit_ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    line = json.dumps(record, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

    # Sink 2: per-run trace (optional). type="live_action" sits alongside
    # tool_call / tool_result for this run.
    if trace_writer is not None:
        trace_writer.write({"type": _LIVE_ACTION_TRACE_TYPE, **record})

    # Sink 3: surface / SSE bus (optional, non-blocking notification).
    if event_callback is not None:
        event_callback(_LIVE_ACTION_EVENT, record)

    return record
