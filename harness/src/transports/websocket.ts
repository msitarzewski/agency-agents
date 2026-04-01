// ---------------------------------------------------------------------------
// Transport: WebSocket
// Bidirectional real-time channel for dashboards and other agents.
// ---------------------------------------------------------------------------

import type { Transport, TransportMessage } from "../types/index.js";

/**
 * WebSocket transport scaffold. In production this wraps a ws/WebSocket
 * server. For the scaffold we define the interface and message protocol
 * so the wiring is ready when a WS library is added.
 */

interface WebSocketLike {
  send(data: string): void;
  addEventListener(event: "message", handler: (ev: { data: string }) => void): void;
  removeEventListener(event: "message", handler: (ev: { data: string }) => void): void;
  readyState: number;
}

export class WebSocketTransport implements Transport {
  name = "websocket";
  private ws: WebSocketLike | null = null;

  /** Attach an existing WebSocket connection. */
  attach(ws: WebSocketLike): void {
    this.ws = ws;
  }

  async send(message: TransportMessage): Promise<void> {
    if (!this.ws || this.ws.readyState !== 1 /* OPEN */) {
      console.warn("[websocket] Not connected — message dropped");
      return;
    }

    const frame = JSON.stringify({
      type: "agent_message",
      sessionId: message.sessionId,
      content: message.content,
      structured: message.structured,
      channel: message.channel,
      timestamp: Date.now(),
    });

    this.ws.send(frame);
  }

  listen(handler: (message: TransportMessage) => Promise<void>): () => void {
    if (!this.ws) {
      console.warn("[websocket] No connection attached — listen is a no-op");
      return () => {};
    }

    const onMessage = async (ev: { data: string }) => {
      try {
        const frame = JSON.parse(ev.data) as {
          type: string;
          content: string;
          structured?: Record<string, unknown>;
          sessionId?: string;
        };

        if (frame.type === "user_message") {
          await handler({
            sessionId: frame.sessionId ?? "",
            content: frame.content,
            structured: frame.structured,
            channel: "websocket",
          });
        }
      } catch (err) {
        console.warn(`[websocket] Failed to parse inbound frame: ${String(err)}`);
      }
    };

    this.ws.addEventListener("message", onMessage);

    return () => {
      this.ws?.removeEventListener("message", onMessage);
    };
  }
}
