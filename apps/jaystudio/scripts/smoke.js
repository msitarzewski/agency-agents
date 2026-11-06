// Smoke test: boots the server on a spare port with a temp data dir and exercises the API.
// Run: npm run check   (set SMOKE_MCP=1 to also connect the real MCP servers)
import { spawn } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), "jaystudio-smoke-"));
const port = 4400 + Math.floor(Math.random() * 500);
const base = `http://127.0.0.1:${port}`;

const proc = spawn(process.execPath, [path.join(here, "..", "server", "index.js")], {
  env: { ...process.env, JAYSTUDIO_PORT: String(port), JAYSTUDIO_DATA_DIR: dataDir, JAYSTUDIO_API_TOKEN: "", ANTHROPIC_API_KEY: "" },
  stdio: ["ignore", "pipe", "inherit"],
});

let failures = 0;
const ok = (cond, label) => {
  console.log(`${cond ? "PASS" : "FAIL"}  ${label}`);
  if (!cond) failures++;
};

async function j(p, opts = {}) {
  const r = await fetch(base + p, { method: opts.method || (opts.body ? "POST" : "GET"), headers: { "content-type": "application/json", ...(opts.headers || {}) }, body: opts.body ? JSON.stringify(opts.body) : undefined });
  return { status: r.status, data: await r.json().catch(() => null) };
}

async function waitUp() {
  for (let i = 0; i < 50; i++) {
    try {
      await fetch(base + "/api/manifest");
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 100));
    }
  }
  throw new Error("server did not start");
}

try {
  await waitUp();
  const html = await fetch(base + "/");
  ok(html.status === 200 && (await html.text()).includes("Jaystudio"), "serves the web app");
  ok((await fetch(base + "/vendor/marked.esm.js")).status === 200, "serves markdown renderer");

  const man = await j("/api/manifest");
  ok(man.data?.workflows?.includes("strategy"), "manifest lists workflows");

  const st = await j("/api/status");
  ok(st.status === 200 && Array.isArray(st.data.mcp) && st.data.mcp.length >= 3, "status lists MCP servers");

  const personas = await j("/api/personas");
  ok(personas.data.length > 20, `loads ${personas.data.length} personas from the repo`);

  // Webhook receiver that verifies Standard Webhooks signatures.
  const { sign } = await import("../server/events.js");
  const received = [];
  let hookSecret = "";
  const receiver = http.createServer(async (req, res) => {
    let raw = "";
    for await (const c of req) raw += c;
    const valid = sign(hookSecret, req.headers["webhook-id"], req.headers["webhook-timestamp"], raw) === req.headers["webhook-signature"];
    received.push({ valid, event: JSON.parse(raw) });
    res.writeHead(204).end();
  });
  await new Promise((r) => receiver.listen(0, "127.0.0.1", r));
  const hook = await j("/api/webhooks", { body: { url: `http://127.0.0.1:${receiver.address().port}/hook`, events: ["brand.*", "webhook.test"] } });
  hookSecret = hook.data.secret;
  ok(hook.status === 201 && hookSecret.startsWith("whsec_"), "registers a webhook");
  ok(!("secret" in (await j("/api/webhooks")).data[0]), "webhook list hides the secret");
  const bad = await j("/api/webhooks", { body: { url: "ftp://x" } });
  ok(bad.status === 400, "rejects non-http webhook URLs");

  const spec = await j("/api/openapi.json");
  ok(spec.data?.openapi === "3.1.0" && spec.data.paths["/api/generate/{workflow}"] && spec.data.webhooks["video.job.completed"], "serves OpenAPI 3.1 with webhooks");

  const created = await j("/api/brands", { body: { name: "Smoke Coffee", kind: "business", channels: "TikTok, Facebook", budget: "5000000" } });
  ok(created.status === 201 && created.data.channels.length === 2 && created.data.budget === 5000000, "creates a brand");
  const upd = await j(`/api/brands/${created.data.id}`, { method: "PUT", body: { tagline: "Cà phê sạch" } });
  ok(upd.data.tagline === "Cà phê sạch", "updates a brand");

  await j(`/api/webhooks/${hook.data.id}/test`, { method: "POST" });
  await new Promise((r) => setTimeout(r, 500));
  const types = received.map((x) => x.event.type);
  ok(types.includes("brand.created") && types.includes("brand.updated") && types.includes("webhook.test"), `webhook delivered ${types.join(", ")}`);
  ok(received.length > 0 && received.every((x) => x.valid), "webhook signatures verify");
  receiver.close();

  const feed = await j("/api/events?type=brand.*");
  ok(feed.data.length === 2 && feed.data[0].type === "brand.created", "event feed filters by type");
  const after = await j(`/api/events?since=${feed.data[0].id}&type=brand.*`);
  ok(after.data.length === 1 && after.data[0].type === "brand.updated", "event feed resumes from `since`");

  const gen = await j("/api/generate/strategy", { body: { brandId: created.data.id, tier: "premium" } });
  ok(gen.status === 500 && /ANTHROPIC_API_KEY/.test(gen.data.error), "generate without key gives a clear error");

  const set = await j("/api/settings", { method: "PUT", body: { monthlyBudgetUsd: 5, bogus: 1 } });
  ok(set.data.settings.monthlyBudgetUsd === 5 && !("bogus" in set.data.settings), "saves only known settings");

  const xo = await j("/api/status", { headers: { origin: "http://evil.example" } });
  ok(xo.status === 403, "blocks cross-origin API calls");

  // MCP endpoint (Jaystudio as a server for AIOS)
  const init = await fetch(base + "/mcp", {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json, text/event-stream" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "smoke", version: "1" } } }),
  });
  ok(init.status === 200 && (await init.text()).includes("jaystudio-brand-os"), "MCP HTTP initialize");
  const list = await fetch(base + "/mcp", {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json, text/event-stream", "mcp-protocol-version": "2025-06-18" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }),
  });
  const listText = await list.text();
  ok(listText.includes("brand_generate") && listText.includes("brand_events"), "MCP HTTP tools/list");

  if (process.env.SMOKE_MCP) {
    const c = await j("/api/mcp/servers/mcp-video/connect", { method: "POST" });
    ok(c.data?.status === "connected" && c.data.toolCount > 5, `connects mcp-video (${c.data?.toolCount} tools)`);
    const info = await j("/api/mcp/call", { body: { server: "mcp-video", tool: "video_doctor", args: {} } });
    ok(Array.isArray(info.data?.content), "calls an mcp-video tool");
    const pre = await j("/api/video/presets");
    ok(pre.status === 200 && pre.data?.prices, "video-toolkit presets via MCP");
  }
} catch (e) {
  console.error(e);
  failures++;
} finally {
  proc.kill();
  fs.rmSync(dataDir, { recursive: true, force: true });
}
console.log(failures ? `\n${failures} check(s) failed` : "\nAll checks passed");
process.exit(failures ? 1 : 0);
