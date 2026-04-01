// ---------------------------------------------------------------------------
// Pattern 6: Structured IO / Transport Layer
// Agent logic produces structured results. The transport layer routes them
// to the appropriate channel. Adding a new channel requires zero changes
// to agent logic.
// ---------------------------------------------------------------------------

import type { Transport, TransportMessage } from "../types/index.js";

export class TransportRouter {
  private transports = new Map<string, Transport>();
  private defaultChannel: string | undefined;

  /** Register a transport for a named channel. */
  register(channel: string, transport: Transport): void {
    this.transports.set(channel, transport);
    if (!this.defaultChannel) {
      this.defaultChannel = channel;
    }
  }

  /** Remove a transport. */
  unregister(channel: string): void {
    this.transports.delete(channel);
    if (this.defaultChannel === channel) {
      this.defaultChannel = this.transports.keys().next().value;
    }
  }

  /** Set the default channel for messages that don't specify one. */
  setDefault(channel: string): void {
    if (!this.transports.has(channel)) {
      throw new Error(`Cannot set default: channel "${channel}" is not registered`);
    }
    this.defaultChannel = channel;
  }

  /** Send a message through the appropriate transport. */
  async send(message: TransportMessage): Promise<void> {
    const channel = message.channel || this.defaultChannel;
    if (!channel) {
      throw new Error("No channel specified and no default channel configured");
    }

    const transport = this.transports.get(channel);
    if (!transport) {
      throw new Error(`No transport registered for channel "${channel}"`);
    }

    await transport.send(message);
  }

  /** Broadcast a message to all registered transports. */
  async broadcast(message: Omit<TransportMessage, "channel">): Promise<void> {
    const sends = Array.from(this.transports.entries()).map(([channel, transport]) =>
      transport.send({ ...message, channel }),
    );
    await Promise.allSettled(sends);
  }

  /**
   * Start listening on all registered transports. Inbound messages are
   * forwarded to the handler. Returns a cleanup function that stops
   * all listeners.
   */
  listenAll(handler: (message: TransportMessage) => Promise<void>): () => void {
    const cleanups: Array<() => void> = [];

    for (const [, transport] of this.transports) {
      const cleanup = transport.listen(handler);
      cleanups.push(cleanup);
    }

    return () => {
      for (const cleanup of cleanups) {
        cleanup();
      }
    };
  }

  /** List registered channels. */
  channels(): string[] {
    return Array.from(this.transports.keys());
  }
}
