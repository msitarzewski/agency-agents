// ---------------------------------------------------------------------------
// Pattern 4: Session Persistence
// Records every decision — not just outcomes. The full reasoning chain
// is preserved for auditability, learning, and agent-to-agent handoff.
// ---------------------------------------------------------------------------

import type { Id, Session, SessionEvent } from "../types/index.js";
import { PermissionTier, SessionEventType } from "../types/index.js";

let eventCounter = 0;
function makeEventId(): Id {
  return `evt_${Date.now()}_${++eventCounter}`;
}

export class SessionManager {
  private sessions = new Map<Id, Session>();

  /** Create a new session. */
  create(agentId: Id, permissionTier?: PermissionTier): Session {
    const session: Session = {
      id: `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      agentId,
      createdAt: Date.now(),
      events: [],
      permissionTier: permissionTier ?? PermissionTier.Standard,
      state: {},
    };
    this.sessions.set(session.id, session);
    return session;
  }

  /** Get a session by ID. */
  get(sessionId: Id): Session | undefined {
    return this.sessions.get(sessionId);
  }

  /** Record an event in the session log. */
  record(session: Session, type: SessionEventType, payload: unknown): SessionEvent {
    const event: SessionEvent = {
      id: makeEventId(),
      sessionId: session.id,
      timestamp: Date.now(),
      type,
      payload,
    };
    session.events.push(event);
    return event;
  }

  /** Get all events of a specific type from a session. */
  eventsOfType(sessionId: Id, type: SessionEventType): SessionEvent[] {
    const session = this.sessions.get(sessionId);
    if (!session) return [];
    return session.events.filter((e) => e.type === type);
  }

  /** Get events in a time range. */
  eventsBetween(sessionId: Id, start: number, end: number): SessionEvent[] {
    const session = this.sessions.get(sessionId);
    if (!session) return [];
    return session.events.filter((e) => e.timestamp >= start && e.timestamp <= end);
  }

  /**
   * Export a session for handoff to another agent. Includes the full
   * event log and current state — the receiving agent gets complete
   * decision context.
   */
  export(sessionId: Id): Session | undefined {
    const session = this.sessions.get(sessionId);
    if (!session) return undefined;
    // Deep clone to prevent mutation of the original
    return JSON.parse(JSON.stringify(session));
  }

  /**
   * Import a session from another agent. Used for agent-to-agent handoff
   * where the full decision history transfers.
   */
  import(session: Session): void {
    this.sessions.set(session.id, session);
  }

  /** Update arbitrary session state. */
  setState(sessionId: Id, key: string, value: unknown): void {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.state[key] = value;
    }
  }

  /** Get a session state value. */
  getState(sessionId: Id, key: string): unknown {
    return this.sessions.get(sessionId)?.state[key];
  }

  /**
   * Replay a session up to a specific event, returning the state
   * as it was at that point. Useful for "what if" analysis.
   */
  replayTo(sessionId: Id, eventId: Id): SessionEvent[] {
    const session = this.sessions.get(sessionId);
    if (!session) return [];
    const idx = session.events.findIndex((e) => e.id === eventId);
    if (idx === -1) return [];
    return session.events.slice(0, idx + 1);
  }

  /** List all active sessions. */
  listActive(): Array<{ id: Id; agentId: Id; createdAt: number; eventCount: number }> {
    return Array.from(this.sessions.values()).map((s) => ({
      id: s.id,
      agentId: s.agentId,
      createdAt: s.createdAt,
      eventCount: s.events.length,
    }));
  }

  /** Remove a session (cleanup after completion). */
  destroy(sessionId: Id): void {
    this.sessions.delete(sessionId);
  }
}
