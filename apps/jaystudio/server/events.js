// Event log + outbound webhooks, signed per the Standard Webhooks spec (https://www.standardwebhooks.com):
// headers webhook-id, webhook-timestamp, webhook-signature: "v1,<base64 HMAC-SHA256(id.timestamp.body)>".
// Any AIOS component (CRM, automation, other agents) can subscribe instead of polling.
import crypto from "node:crypto";
import { readCollection, writeCollection, newId, findById, update } from "./store.js";

export const EVENT_TYPES = [
  "brand.created",
  "brand.updated",
  "brand.deleted",
  "document.created", // strategy, budget, calendar, content, repurpose, variants, videoSpec
  "video.job.submitted",
  "video.job.completed",
  "video.job.failed",
  "budget.warning", // monthly AI spend crossed 80%
  "budget.exceeded", // a request was blocked by the budget guard
  "webhook.test",
];

const MAX_EVENTS = 2000;
const RETRY_DELAYS_MS = [0, 2_000, 15_000, 60_000];

function matches(patterns, type) {
  return (patterns || ["*"]).some((p) => p === "*" || p === type || (p.endsWith(".*") && type.startsWith(p.slice(0, -1))));
}

export function sign(secret, id, timestamp, body) {
  const key = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  return "v1," + crypto.createHmac("sha256", key).update(`${id}.${timestamp}.${body}`).digest("base64");
}

async function deliver(hook, event, attempt = 0) {
  const body = JSON.stringify(event);
  const ts = Math.floor(Date.now() / 1000).toString();
  let status = 0;
  let error = null;
  try {
    const r = await fetch(hook.url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "user-agent": "jaystudio-brand-os/1.0",
        "webhook-id": event.id,
        "webhook-timestamp": ts,
        "webhook-signature": sign(hook.secret, event.id, ts, body),
      },
      body,
      signal: AbortSignal.timeout(10_000),
    });
    status = r.status;
  } catch (e) {
    error = e.message;
  }
  const okDelivery = status >= 200 && status < 300;
  update("webhooks", hook.id, { lastStatus: status || null, lastError: okDelivery ? null : error || `HTTP ${status}`, lastDeliveryAt: new Date().toISOString() });
  if (!okDelivery && attempt + 1 < RETRY_DELAYS_MS.length && !(status >= 400 && status < 500 && status !== 408 && status !== 429)) {
    setTimeout(() => deliver(hook, event, attempt + 1), RETRY_DELAYS_MS[attempt + 1]).unref();
  }
  return { status, error };
}

/** Record an event and fan it out to matching webhooks (fire-and-forget). */
export function emit(type, data) {
  const event = { id: newId("evt"), type, timestamp: new Date().toISOString(), source: "jaystudio-brand-os", data };
  const events = readCollection("events");
  events.push(event);
  writeCollection("events", events.slice(-MAX_EVENTS));
  for (const hook of readCollection("webhooks")) {
    if (hook.active !== false && matches(hook.events, type)) deliver(hook, event).catch(() => {});
  }
  return event;
}

export function listEvents({ since, type, limit = 100 } = {}) {
  let ev = readCollection("events");
  if (since) {
    const i = ev.findIndex((e) => e.id === since);
    ev = i >= 0 ? ev.slice(i + 1) : ev.filter((e) => e.timestamp > since);
  }
  if (type) ev = ev.filter((e) => matches([type], e.type));
  return ev.slice(-Math.min(Number(limit) || 100, 500));
}

// ---- subscriptions ----
const publicHook = ({ secret, ...h }) => ({ ...h, secretHint: secret ? `${secret.slice(0, 10)}...` : null });

export function listWebhooks() {
  return readCollection("webhooks").map(publicHook);
}

export function createWebhook({ url, events, description }) {
  let u;
  try {
    u = new URL(url);
  } catch {
    throw Object.assign(new Error("URL không hợp lệ"), { status: 400 });
  }
  if (!["http:", "https:"].includes(u.protocol)) throw Object.assign(new Error("Chỉ hỗ trợ http/https"), { status: 400 });
  const list = (Array.isArray(events) ? events : String(events || "*").split(",")).map((s) => s.trim()).filter(Boolean);
  const hook = {
    id: newId("wh"),
    url: u.toString(),
    events: list.length ? list : ["*"],
    description: description || "",
    secret: "whsec_" + crypto.randomBytes(24).toString("base64"),
    active: true,
    createdAt: new Date().toISOString(),
  };
  const all = readCollection("webhooks");
  all.push(hook);
  writeCollection("webhooks", all);
  return hook; // the only time the full secret is returned
}

export function deleteWebhook(id) {
  const all = readCollection("webhooks");
  writeCollection("webhooks", all.filter((h) => h.id !== id));
  return all.length !== readCollection("webhooks").length;
}

export async function testWebhook(id) {
  const hook = findById("webhooks", id);
  if (!hook) throw Object.assign(new Error("Không tìm thấy webhook"), { status: 404 });
  const event = { id: newId("evt"), type: "webhook.test", timestamp: new Date().toISOString(), source: "jaystudio-brand-os", data: { message: "Xin chào từ Jaystudio" } };
  return deliver(hook, event, RETRY_DELAYS_MS.length); // single attempt, no retry
}
