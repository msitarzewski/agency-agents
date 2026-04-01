// ---------------------------------------------------------------------------
// Transport: Webhook
// Outbound HTTP POST for integrating with external systems (Discord bots,
// Telegram bots, dashboards, alerting pipelines).
// ---------------------------------------------------------------------------

import type { Transport, TransportMessage } from "../types/index.js";

interface WebhookConfig {
  /** Target URL to POST messages to. */
  url: string;
  /** Optional auth header value. */
  authHeader?: string;
  /** Retry count on failure. */
  maxRetries?: number;
}

export class WebhookTransport implements Transport {
  name = "webhook";
  private config: Required<WebhookConfig>;

  constructor(config: WebhookConfig) {
    this.config = {
      url: config.url,
      authHeader: config.authHeader ?? "",
      maxRetries: config.maxRetries ?? 3,
    };
  }

  async send(message: TransportMessage): Promise<void> {
    const payload = {
      sessionId: message.sessionId,
      content: message.content,
      structured: message.structured,
      channel: message.channel,
      timestamp: Date.now(),
    };

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.config.authHeader) {
      headers["Authorization"] = this.config.authHeader;
    }

    let lastError: Error | undefined;
    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        const res = await fetch(this.config.url, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        });
        if (res.ok) return;
        lastError = new Error(`Webhook returned ${res.status}: ${await res.text()}`);
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
      }

      if (attempt < this.config.maxRetries) {
        await new Promise((r) => setTimeout(r, 500 * Math.pow(2, attempt)));
      }
    }

    console.warn(`[webhook] Failed after ${this.config.maxRetries + 1} attempts: ${lastError?.message}`);
  }

  listen(_handler: (message: TransportMessage) => Promise<void>): () => void {
    // Webhook transport is outbound-only in this scaffold.
    // For inbound webhooks, use an HTTP server transport.
    return () => {};
  }
}
