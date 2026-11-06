// Integration test: Jaystudio <-> a running AIOS Brand OS API (AIOS-CRM repo, brand-os/).
// Usage: AIOS_BRANDOS_URL=http://127.0.0.1:4000/api/v1 node scripts/aios-integration.js
// It registers two throwaway accounts on that AIOS instance, so point it ONLY at a disposable dev/test database.
import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const AIOS = (process.env.AIOS_BRANDOS_URL || "http://127.0.0.1:4000/api/v1").replace(/\/+$/, "");
const ORIGIN = process.env.AIOS_BRANDOS_ORIGIN || "http://localhost:3001";
const suffix = crypto.randomBytes(4).toString("hex");
const password = crypto.randomBytes(16).toString("hex");
let failures = 0;
const ok = (c, label) => (console.log(`${c ? "PASS" : "FAIL"}  ${label}`), c || failures++);

async function aios(method, p, body, cookie, org) {
  const r = await fetch(AIOS + p, {
    method,
    headers: { "content-type": "application/json", origin: ORIGIN, ...(cookie ? { cookie } : {}), ...(org ? { "x-organization-id": org } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`${method} ${p} ${r.status} ${JSON.stringify(data)}`);
  return { data, cookie: (r.headers.getSetCookie?.() || []).map((c) => c.split(";")[0]).find((c) => c.startsWith("brandos_session=")) };
}

// 1. AIOS side: an owner workspace plus a CONTENT_MANAGER service account for Jaystudio.
const owner = await aios("POST", "/auth/register", { email: `owner-${suffix}@example.test`, password, name: "Owner", organizationName: `Jay Test ${suffix}` });
const ownerCookie = owner.cookie;
const org = (await aios("GET", "/auth/me", null, ownerCookie)).data.memberships[0].organizationId;
await aios("POST", "/auth/register", { email: `svc-${suffix}@example.test`, password, name: "Jaystudio", organizationName: `svc ${suffix}` });
await aios("POST", "/members", { email: `svc-${suffix}@example.test`, role: "CONTENT_MANAGER" }, ownerCookie, org);
const remoteBrand = (await aios("POST", "/brands", { name: "Spa Hoa Sen", industry: "Làm đẹp", tone: "Dịu dàng", targetAudience: "Nữ 25-40", brandColor: "#C2185B" }, ownerCookie, org)).data;

// 2. Jaystudio with the connector configured (service account belongs to 2 workspaces -> ORG_ID needed).
const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), "jaystudio-aios-"));
const port = 4600 + Math.floor(Math.random() * 300);
const base = `http://127.0.0.1:${port}/api`;
const env = { ...process.env, JAYSTUDIO_PORT: String(port), JAYSTUDIO_DATA_DIR: dataDir, JAYSTUDIO_API_TOKEN: "", AIOS_BRANDOS_URL: AIOS, AIOS_BRANDOS_ORIGIN: ORIGIN, AIOS_BRANDOS_EMAIL: `svc-${suffix}@example.test`, AIOS_BRANDOS_PASSWORD: password };
const startJay = (extra = {}) => spawn(process.execPath, [path.join(here, "..", "server", "index.js")], { env: { ...env, ...extra }, stdio: ["ignore", "ignore", "inherit"] });
const j = async (p, body, method) => {
  const r = await fetch(base + p, { method: method || (body ? "POST" : "GET"), headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  return { status: r.status, data: await r.json().catch(() => null) };
};
const up = async () => { for (let i = 0; i < 50; i++) { try { await fetch(base + "/manifest"); return; } catch { await new Promise((r) => setTimeout(r, 100)); } } };

let jay = startJay();
try {
  await up();
  let st = await j("/aios/status");
  ok(st.data.reachable && !st.data.connected && /AIOS_BRANDOS_ORG_ID/.test(st.data.error), "asks for ORG_ID when the account has 2 workspaces");
  jay.kill();
  jay = startJay({ AIOS_BRANDOS_ORG_ID: org });
  await up();
  st = await j("/aios/status");
  ok(st.data.connected && st.data.organizationId === org && st.data.role === "CONTENT_MANAGER", `connects as ${st.data.role} to ${st.data.organization}`);

  // Import an AIOS brand
  const remote = await j("/aios/brands");
  ok(remote.data.some((b) => b.id === remoteBrand.id), "lists AIOS brands");
  const imported = await j("/aios/brands/import", { remoteId: remoteBrand.id });
  ok(imported.data.name === "Spa Hoa Sen" && imported.data.aios.brandId === remoteBrand.id && imported.data.colors === "#C2185B", "imports an AIOS brand with link");
  const again = await j("/aios/brands/import", { remoteId: remoteBrand.id });
  ok(again.data.id === imported.data.id && (await j("/brands")).data.length === 1, "re-import updates instead of duplicating");

  // Push a Jaystudio brand
  const local = (await j("/brands", { name: "Jay Coffee", industry: "Cà phê", voice: "Gần gũi", colors: "nâu #6D4C41", audience: "Dân văn phòng" })).data;
  const pushed = await j(`/aios/brands/${local.id}/push`, {});
  const rb = (await aios("GET", `/brands/${pushed.data.aiosBrandId}`, null, ownerCookie, org)).data;
  ok(rb.name === "Jay Coffee" && rb.brandColor === "#6D4C41" && rb.tone === "Gần gũi", "pushes a brand to AIOS");
  await j(`/brands/${local.id}`, { tagline: "Cà phê sạch mỗi sáng" }, "PUT");
  await j(`/aios/brands/${local.id}/push`, {});
  const rb2 = (await aios("GET", `/brands/${pushed.data.aiosBrandId}`, null, ownerCookie, org)).data;
  ok(rb2.version === 2 && rb2.positioning.includes("Cà phê sạch"), "second push updates the same AIOS brand (version 2)");

  // Push a document (seeded directly: no LLM key in tests)
  const docs = [{ id: "doc_test1", type: "content", brandId: local.id, title: "TikTok: 3 cách pha cold brew", content: "# Hook\nBạn pha cold brew sai cách?", model: "claude-sonnet-5-5", tier: "balanced", costUsd: 0.01, createdAt: new Date().toISOString() }];
  fs.writeFileSync(path.join(dataDir, "documents.json"), JSON.stringify(docs));
  const d1 = await j("/aios/documents/doc_test1/push", {});
  ok(d1.status === 200 && d1.data.version === 1, "pushes a document as an AIOS content draft");
  const d2 = await j("/aios/documents/doc_test1/push", {});
  ok(d2.data.unchanged === true, "unchanged document is not pushed twice");
  const cur = JSON.parse(fs.readFileSync(path.join(dataDir, "documents.json"), "utf8"));
  cur[0].content += "\nThêm CTA.";
  fs.writeFileSync(path.join(dataDir, "documents.json"), JSON.stringify(cur));
  const d3 = await j("/aios/documents/doc_test1/push", {});
  ok(d3.data.version === 2 && d3.data.projectId === d1.data.projectId, "edited document becomes version 2 of the same project");
  const projects = (await aios("GET", "/content-projects", null, ownerCookie, org)).data;
  const proj = projects.find((p) => p.id === d1.data.projectId);
  ok(proj && proj.versions.length === 2 && proj.status === "DRAFT" && proj.versions[1].text.includes("Bản nháp AI từ Jaystudio"), "AIOS shows the draft with 2 versions and an AI label");

  // Leads
  const l1 = await j("/aios/leads", { name: "Chị Lan", email: "lan@example.test", source: "TikTok Jaystudio" });
  const l2 = await j("/aios/leads", { name: "Chị Lan", email: "LAN@example.test", source: "TikTok Jaystudio" });
  ok(l1.data.leadId && l2.data.duplicate === true && l2.data.leadId === l1.data.leadId, "lead push is idempotent");

  // Video upload
  const mp4 = path.join(dataDir, "clip.mp4");
  execFileSync("ffmpeg", ["-v", "error", "-f", "lavfi", "-i", "testsrc=size=720x1280:rate=30:duration=2", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-shortest", "-pix_fmt", "yuv420p", mp4]);
  const v = await j("/aios/media", { filePath: mp4, brandId: local.id });
  const media = (await aios("GET", "/media", null, ownerCookie, org)).data;
  ok(v.status === 200 && media.some((m) => m.id === v.data.mediaId), "uploads an MP4 to the AIOS media library");

  // Errors are reported, logged and evented
  const bad = await j("/aios/documents/nope/push", {});
  ok(bad.status === 404, "missing document -> 404");
  const log = (await j("/aios/sync-log")).data;
  ok(log.length >= 6 && log.every((x) => x.status === "ok"), `sync log has ${log.length} entries`);
  const ev = (await j("/events?type=aios.*")).data;
  ok(ev.length >= 6 && ev.every((e) => e.type === "aios.sync.succeeded"), "emits aios.sync.succeeded events");

  // Auto-push on document.created (via workflow event)
  await j("/settings", { aiosAutoPush: true }, "PUT");
  ok((await j("/settings")).data.settings.aiosAutoPush === true, "auto-push setting saved");
} catch (e) {
  console.error(e);
  failures++;
} finally {
  jay.kill();
  fs.rmSync(dataDir, { recursive: true, force: true });
}
console.log(failures ? `\n${failures} check(s) failed` : "\nAll AIOS integration checks passed");
process.exit(failures ? 1 : 0);
