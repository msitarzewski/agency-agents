// ---------------------------------------------------------------------------
// Pattern 1c: Streaming Layer
// Pushes incremental results back to callers in real-time rather than
// waiting for the full execution pipeline to complete.
// ---------------------------------------------------------------------------

import type { Id } from "../types/index.js";

export interface StreamEvent {
  sessionId: Id;
  timestamp: number;
  type: string;
  data: unknown;
}

export type StreamListener = (event: StreamEvent) => void;

export class StreamManager {
  /** Per-session listener sets. */
  private listeners = new Map<Id, Set<StreamListener>>();
  /** Global listeners that receive all events. */
  private globalListeners = new Set<StreamListener>();

  /** Subscribe to events for a specific session. Returns unsubscribe fn. */
  subscribe(sessionId: Id, listener: StreamListener): () => void {
    let set = this.listeners.get(sessionId);
    if (!set) {
      set = new Set();
      this.listeners.set(sessionId, set);
    }
    set.add(listener);

    return () => {
      set!.delete(listener);
      if (set!.size === 0) this.listeners.delete(sessionId);
    };
  }

  /** Subscribe to all events across all sessions. Returns unsubscribe fn. */
  subscribeAll(listener: StreamListener): () => void {
    this.globalListeners.add(listener);
    return () => {
      this.globalListeners.delete(listener);
    };
  }

  /** Emit an event to session-specific and global listeners. */
  emit(sessionId: Id, data: { type: string } & Record<string, unknown>): void {
    const event: StreamEvent = {
      sessionId,
      timestamp: Date.now(),
      type: data.type,
      data,
    };

    // Session-specific listeners
    const sessionListeners = this.listeners.get(sessionId);
    if (sessionListeners) {
      for (const listener of sessionListeners) {
        try {
          listener(event);
        } catch {
          // Listener errors must not break the pipeline
        }
      }
    }

    // Global listeners
    for (const listener of this.globalListeners) {
      try {
        listener(event);
      } catch {
        // Listener errors must not break the pipeline
      }
    }
  }

  /** Clean up listeners for a completed session. */
  cleanup(sessionId: Id): void {
    this.listeners.delete(sessionId);
  }
}
