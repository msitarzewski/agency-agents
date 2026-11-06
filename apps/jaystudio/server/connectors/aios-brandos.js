// Connector: Jaystudio -> AIOS Brand OS V1 (vitusngochai68-code/AIOS-CRM, folder brand-os/).
// Contract taken from that repo: REST under /api/v1, cookie session `brandos_session` from POST auth/login,
// workspace in header `x-organization-id`, Origin must equal the Brand OS WEB_ORIGIN on writes.
// AIOS stays the system of record for approval and publishing: everything pushed lands there as a DRAFT.
import fs from "node:fs";
import path from "node:path";
import { getSettings } from "../config.js";
import { readCollection, insert, findById, update, newId, hash } from "../store.js";
import { emit } from "../events.js";

const MAX_TEXT = 50_000; // ContentVersion.text limit in AIOS
const MAX_UPLOAD = 50 * 1024 * 1024; // media/upload limit in AIOS

export function config() {
  return {
    baseUrl: (process.env.AIOS_BRANDOS_URL || "http://localhost:4000/api/v1").replace(/\/+$/, ""),
    origin: process.env.AIOS_BRANDOS_ORIGIN || "http://localhost:3001",
    email: process.env.AIOS_BRANDOS_EMAIL || "",
    password: process.env.AIOS_BRANDOS_PASSWORD || "",
    organizationId: process.env.AIOS_BRANDOS_ORG_ID || "",
  };
}

export const configured = () => Boolean(config().email && config().password);

export class AiosError extends Error {
  constructor(message, status = 502) {
    super(message);
    this.status = status;
  }
}

// ---------- HTTP client with session handling ----------
let session = { cookie: "", at: 0, orgId: "", me: null };

async function login() {
  const c = config();
  if (!configured()) throw new AiosError("Chưa cấu hình AIOS_BRANDOS_EMAIL / AIOS_BRANDOS_PASSWORD trong .env.", 400);
  let r;
  try {
    r = await fetch(`${c.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json", origin: c.origin },
      body: JSON.stringify({ email: c.email, password: c.password }),
      signal: AbortSignal.timeout(15_000),
    });
  } catch (e) {
    throw new AiosError(`Không kết nối được AIOS Brand OS tại ${c.baseUrl} (${e.cause?.code || e.message}). API đã chạy chưa?`, 502);
  }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new AiosError(`Đăng nhập AIOS thất bại (${r.status}): ${data.error || data.message || ""}`.trim(), r.status === 401 ? 401 : 502);
  const cookie = (r.headers.getSetCookie?.() || [r.headers.get("set-cookie") || ""]).map((x) => x.split(";")[0]).find((x) => x.startsWith("brandos_session="));
  if (!cookie) throw new AiosError("AIOS không trả cookie phiên.", 502);
  session = { cookie, at: Date.now(), orgId: "", me: null };
  return session;
}

async function ensureSession() {
  // AIOS sessions last 8h; refresh a little earlier.
  if (!session.cookie || Date.now() - session.at > 7.5 * 3600_000) await login();
  if (!session.me) {
    session.me = await raw("GET", "/auth/me", undefined, { noOrg: true });
    const c = config();
    const ms = session.me.memberships || [];
    const chosen = c.organizationId ? ms.find((m) => m.organizationId === c.organizationId) : ms.length === 1 ? ms[0] : null;
    if (!chosen) {
      throw new AiosError(
        c.organizationId
          ? "Tài khoản AIOS không thuộc workspace AIOS_BRANDOS_ORG_ID."
          : `Tài khoản thuộc ${ms.length} workspace; đặt AIOS_BRANDOS_ORG_ID trong .env để chọn.`,
        400
      );
    }
    session.orgId = chosen.organizationId;
    session.role = chosen.role;
    session.orgName = chosen.organization?.name;
  }
  return session;
}

async function raw(method, pathname, body, { noOrg = false, form = null, retried = false } = {}) {
  const c = config();
  const headers = { cookie: session.cookie };
  if (!noOrg) headers["x-organization-id"] = session.orgId;
  if (method !== "GET") headers.origin = c.origin;
  if (body !== undefined) headers["content-type"] = "application/json";
  let r;
  try {
    r = await fetch(c.baseUrl + pathname, {
      method,
      headers,
      body: form || (body !== undefined ? JSON.stringify(body) : undefined),
      signal: AbortSignal.timeout(120_000),
    });
  } catch (e) {
    throw new AiosError(`Không kết nối được AIOS Brand OS (${e.cause?.code || e.message}).`, 502);
  }
  if (r.status === 401 && !retried) {
    await login();
    if (!noOrg) await ensureSession();
    return raw(method, pathname, body, { noOrg, form, retried: true });
  }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msg = Array.isArray(data.message) ? data.message.join("; ") : data.error || data.message || r.statusText;
    throw new AiosError(`AIOS ${method} ${pathname} → ${r.status}: ${msg}`, r.status >= 500 ? 502 : r.status);
  }
  return data;
}

async function call(method, pathname, body, opts) {
  await ensureSession();
  return raw(method, pathname, body, opts);
}

// ---------- sync log (idempotency + audit) ----------
function logSync(entry) {
  const row = insert("aios-sync", { id: newId("sync"), at: new Date().toISOString(), ...entry });
  emit(entry.status === "ok" ? "aios.sync.succeeded" : "aios.sync.failed", { op: entry.op, localId: entry.localId, remoteId: entry.remoteId || null, error: entry.error || null });
  return row;
}

async function tracked(op, localId, fn, key) {
  try {
    const remoteId = await fn();
    logSync({ op, localId, remoteId, key, status: "ok" });
    return remoteId;
  } catch (e) {
    logSync({ op, localId, key, status: "error", error: e.message });
    throw e;
  }
}

export const syncLog = (limit = 100) => readCollection("aios-sync").slice(-limit).reverse();

// ---------- field mapping ----------
const clip = (s, n) => (s ? String(s).trim().slice(0, n) : "");

export function toAiosBrand(b) {
  const color = String(b.colors || "").match(/#[0-9a-fA-F]{6}\b/)?.[0];
  return {
    name: clip(b.name, 120),
    industry: clip(b.industry, 200) || "Chưa xác định",
    targetAudience: clip([b.audience, b.problems && `Nỗi đau: ${b.problems}`].filter(Boolean).join("\n"), 2000),
    tone: clip(b.voice, 200) || "Thân thiện, rõ ràng",
    positioning: clip([b.tagline, b.differentiators && `Khác biệt: ${b.differentiators}`, b.offer && `Sản phẩm: ${b.offer}`].filter(Boolean).join("\n"), 2000),
    cta: clip(b.goals, 2000),
    ...(color ? { brandColor: color } : {}),
  };
}

export function fromAiosBrand(r) {
  return {
    name: r.name,
    kind: "business",
    industry: r.industry,
    audience: r.targetAudience,
    voice: r.tone,
    tagline: r.positioning,
    goals: r.cta,
    colors: r.brandColor,
  };
}

// ---------- operations ----------
export async function status() {
  const c = config();
  const base = { configured: configured(), baseUrl: c.baseUrl, origin: c.origin, autoPush: getSettings().aiosAutoPush };
  let health = null;
  try {
    const r = await fetch(`${c.baseUrl}/health`, { signal: AbortSignal.timeout(4000) });
    health = await r.json().catch(() => null);
  } catch {
    return { ...base, reachable: false, connected: false, error: `Không kết nối được ${c.baseUrl}/health` };
  }
  if (!configured()) return { ...base, reachable: true, health, connected: false };
  try {
    const s = await ensureSession();
    return { ...base, reachable: true, health, connected: true, user: s.me.user?.email, organizationId: s.orgId, organization: s.orgName, role: s.role };
  } catch (e) {
    return { ...base, reachable: true, health, connected: false, error: e.message };
  }
}

export const remoteBrands = () => call("GET", "/brands");

/** Import (or refresh) an AIOS brand into Jaystudio and link the two. */
export async function importBrand(remoteId) {
  const r = await call("GET", `/brands/${encodeURIComponent(remoteId)}`);
  const local = readCollection("brands").find((b) => b.aios?.brandId === r.id);
  const link = { brandId: r.id, organizationId: session.orgId, version: r.version, syncedAt: new Date().toISOString() };
  const fields = fromAiosBrand(r);
  const saved = local ? update("brands", local.id, { ...fields, aios: link }) : insert("brands", { id: newId("brand"), ...fields, aios: link, createdAt: new Date().toISOString() });
  logSync({ op: "brand.import", localId: saved.id, remoteId: r.id, status: "ok" });
  emit(local ? "brand.updated" : "brand.created", saved);
  return saved;
}

/** Create the brand in AIOS, or update the linked one. Returns the AIOS brand id. */
export async function pushBrand(localId) {
  const b = findById("brands", localId);
  if (!b) throw new AiosError("Không tìm thấy thương hiệu", 404);
  return tracked("brand.push", localId, async () => {
    const payload = toAiosBrand(b);
    const r = b.aios?.brandId
      ? await call("PATCH", `/brands/${b.aios.brandId}`, payload)
      : await call("POST", "/brands", payload);
    update("brands", localId, { aios: { brandId: r.id, organizationId: session.orgId, version: r.version, syncedAt: new Date().toISOString() } });
    return r.id;
  });
}

/** Push a generated document to AIOS Content Studio as a draft; later pushes add a new version. */
export async function pushDocument(docId) {
  const doc = findById("documents", docId);
  if (!doc) throw new AiosError("Không tìm thấy tài liệu", 404);
  if (!doc.brandId) throw new AiosError("Tài liệu chưa gắn thương hiệu nên không gửi được sang AIOS.", 400);
  let brand = findById("brands", doc.brandId);
  const aiosBrandId = brand?.aios?.brandId || (await pushBrand(doc.brandId));
  brand = findById("brands", doc.brandId);

  const body = doc.type === "videoSpec" && doc.data ? "```json\n" + JSON.stringify(doc.data, null, 2) + "\n```" : doc.content;
  const text = `${body}\n\n---\nBản nháp AI từ Jaystudio Brand OS · ${doc.model} · ${doc.type} · cần duyệt trước khi đăng.`;
  if (text.length > MAX_TEXT) throw new AiosError(`Tài liệu dài ${text.length} ký tự, vượt giới hạn ${MAX_TEXT} của AIOS. Hãy tách nhỏ.`, 400);

  // Same content already pushed -> nothing to do (idempotent).
  const key = hash(aiosBrandId, text);
  if (doc.aios?.contentKey === key) return { projectId: doc.aios.projectId, version: doc.aios.version, unchanged: true };

  const result = await tracked(
    "document.push",
    docId,
    async () => {
      if (doc.aios?.projectId) {
        const v = await call("POST", `/content-projects/${doc.aios.projectId}/versions`, { text });
        update("documents", docId, { aios: { ...doc.aios, version: v.version, contentKey: key, syncedAt: new Date().toISOString() } });
        return doc.aios.projectId;
      }
      const p = await call("POST", "/content-projects", { brandId: aiosBrandId, title: clip(doc.title, 200) || "Nội dung Jaystudio", text });
      update("documents", docId, { aios: { projectId: p.id, brandId: aiosBrandId, version: 1, contentKey: key, syncedAt: new Date().toISOString() } });
      return p.id;
    },
    key
  );
  const after = findById("documents", docId);
  return { projectId: result, version: after.aios.version };
}

/** Send a lead to AIOS. Idempotent on (email or name, source) via the local sync log. */
export async function pushLead({ name, email, source = "Jaystudio" }) {
  if (!name) throw new AiosError("Cần tên lead", 400);
  const key = hash("lead", (email || name).toLowerCase().trim(), source);
  const prior = readCollection("aios-sync").find((s) => s.op === "lead.push" && s.key === key && s.status === "ok");
  if (prior) return { leadId: prior.remoteId, duplicate: true };
  const leadId = await tracked("lead.push", email || name, async () => (await call("POST", "/leads", { name: clip(name, 200), ...(email ? { email } : {}), source: clip(source, 200) })).id, key);
  return { leadId };
}

/** Upload a finished video file (e.g. a video-toolkit MP4) into the AIOS media library. */
export async function pushVideo({ filePath, brandId }) {
  const b = findById("brands", brandId);
  if (!b) throw new AiosError("Không tìm thấy thương hiệu", 404);
  const abs = path.resolve(filePath);
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) throw new AiosError(`Không thấy file ${abs}`, 400);
  const size = fs.statSync(abs).size;
  if (size > MAX_UPLOAD) throw new AiosError(`File ${(size / 1048576).toFixed(1)} MB vượt giới hạn 50 MB của AIOS.`, 400);
  const aiosBrandId = b.aios?.brandId || (await pushBrand(brandId));
  return tracked("video.push", abs, async () => {
    const form = new FormData();
    form.append("brandId", aiosBrandId);
    form.append("file", await fs.openAsBlob(abs, { type: "video/mp4" }), path.basename(abs));
    const m = await call("POST", "/media/upload", undefined, { form });
    return m.id;
  });
}

export function resetSession() {
  session = { cookie: "", at: 0, orgId: "", me: null };
}
