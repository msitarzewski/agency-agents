// Jaystudio Brand OS - local web app + REST API + MCP endpoint.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { HOST, PORT, API_TOKEN, PUBLIC_DIR, APP_DIR, KNOWN_KEYS, getSettings, saveSettings } from "./config.js";
import { readCollection, findById, insert, update, remove, newId } from "./store.js";
import { sanitizeBrand } from "./brands.js";
import { listPersonas } from "./personas.js";
import { runWorkflow, WORKFLOWS } from "./workflows.js";
import { TIERS, report, BudgetError } from "./costs.js";
import { TASK_TIER, anthropicConfigured, ollamaStatus } from "./llm.js";
import * as hub from "./mcp-hub.js";
import * as assistant from "./assistant.js";
import * as video from "./video.js";
import { buildMcpServer } from "./aios-mcp.js";
import { emit, listEvents, listWebhooks, createWebhook, deleteWebhook, testWebhook, EVENT_TYPES } from "./events.js";
import { openapi } from "./openapi.js";

const VERSION = "1.0.0";

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".json": "application/json", ".png": "image/png" };

// Static files the browser may load: the app itself and the markdown renderer from node_modules.
const VENDOR = { "/vendor/marked.esm.js": path.join(APP_DIR, "node_modules", "marked", "lib", "marked.esm.js") };

function send(res, code, data) {
  res.writeHead(code, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data));
}

async function body(req) {
  const chunks = [];
  let size = 0;
  for await (const c of req) {
    size += c.length;
    if (size > 5 * 1024 * 1024) throw Object.assign(new Error("Payload quá lớn"), { status: 413 });
    chunks.push(c);
  }
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function serveStatic(req, res, pathname) {
  let file = VENDOR[pathname];
  if (!file) {
    const rel = pathname === "/" ? "index.html" : pathname.slice(1);
    file = path.join(PUBLIC_DIR, path.normalize(rel));
    if (!file.startsWith(PUBLIC_DIR)) return send(res, 403, { error: "forbidden" });
  }
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(PUBLIC_DIR, "index.html");
  res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
}

function manifest() {
  return {
    name: "jaystudio-brand-os",
    version: VERSION,
    description: "Xây dựng thương hiệu cá nhân & doanh nghiệp tối ưu chi phí: chiến lược, nội dung, lịch đăng, ngân sách, video AI qua MCP.",
    auth: API_TOKEN ? "bearer" : "none (chỉ localhost)",
    endpoints: {
      rest: `/api`,
      openapi: `/api/openapi.json`,
      mcp_http: `/mcp`,
      mcp_stdio: "node apps/jaystudio/server/mcp-stdio.js",
      events: `/api/events`,
      webhooks: `/api/webhooks`,
    },
    standards: {
      tools: "Model Context Protocol (Streamable HTTP + stdio)",
      rest: "OpenAPI 3.1",
      events: "Standard Webhooks (HMAC-SHA256, headers webhook-id/timestamp/signature) + polling feed",
      auth: "HTTP Bearer token (JAYSTUDIO_API_TOKEN)",
    },
    eventTypes: EVENT_TYPES,
    workflows: WORKFLOWS,
    tiers: Object.fromEntries(Object.entries(TIERS).map(([k, t]) => [k, { label: t.label, model: t.model || null, usdPer1MIn: t.in, usdPer1MOut: t.out }])),
    mcpServers: hub.status().map(({ name, label, role }) => ({ name, label, role })),
    routes: [
      "GET  /api/brands | POST /api/brands | GET/PUT/DELETE /api/brands/:id",
      "POST /api/generate/:workflow  {brandId, personaId, tier, params}",
      "GET  /api/documents?brandId= | GET/DELETE /api/documents/:id",
      "GET  /api/mcp/servers | POST /api/mcp/servers/:name/connect | GET /api/mcp/servers/:name/tools | POST /api/mcp/call {server, tool, args}",
      "POST /api/video/estimate {spec} | POST /api/video/submit {spec, maxUsd} | GET /api/video/:jobId/status | GET /api/video/:jobId/result",
      "POST /api/assistant {sessionId?, message, brandId, servers, tier} | POST /api/assistant/approve {sessionId, decisions}",
      "GET  /api/events?since=&type= | GET/POST /api/webhooks | DELETE /api/webhooks/:id | POST /api/webhooks/:id/test",
      "GET  /api/openapi.json | GET /api/costs | GET/PUT /api/settings | GET /api/status",
    ],
  };
}

async function handleMcp(req, res) {
  // Stateless Streamable HTTP: a fresh server + transport per request.
  const server = buildMcpServer();
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => {
    transport.close();
    server.close();
  });
  await server.connect(transport);
  const parsed = req.method === "POST" ? await body(req) : undefined;
  await transport.handleRequest(req, res, parsed);
}

async function api(req, res, url) {
  const p = url.pathname.replace(/\/+$/, "");
  const parts = p.split("/").filter(Boolean); // ["api", ...]
  const m = req.method;
  const seg = (i) => decodeURIComponent(parts[i] || "");

  if (p === "/api/manifest") return send(res, 200, manifest());
  if (p === "/api/openapi.json") return send(res, 200, openapi(VERSION, `http://${req.headers.host}`));

  // Events & webhooks
  if (p === "/api/events") return send(res, 200, listEvents(Object.fromEntries(url.searchParams)));
  if (parts[1] === "webhooks") {
    if (parts.length === 2 && m === "GET") return send(res, 200, listWebhooks());
    if (parts.length === 2 && m === "POST") return send(res, 201, createWebhook(await body(req)));
    if (parts.length === 3 && m === "DELETE") return send(res, 200, { ok: deleteWebhook(seg(2)) });
    if (parts[3] === "test" && m === "POST") return send(res, 200, await testWebhook(seg(2)));
  }

  if (p === "/api/status") {
    const o = await ollamaStatus();
    return send(res, 200, {
      version: VERSION,
      anthropic: anthropicConfigured(),
      ollama: { ok: o.ok, models: o.models },
      keys: KNOWN_KEYS.map((k) => ({ ...k, set: Boolean(process.env[k.env]) })),
      mcp: hub.status(),
      costs: (({ recent, ...r }) => r)(report()),
      counts: { brands: readCollection("brands").length, documents: readCollection("documents").length, videos: readCollection("videos").length },
    });
  }

  if (p === "/api/settings") {
    if (m === "GET") return send(res, 200, { settings: getSettings(), taskTier: TASK_TIER, tiers: TIERS });
    if (m === "PUT") return send(res, 200, { settings: saveSettings(await body(req)) });
  }

  if (p === "/api/personas") return send(res, 200, listPersonas());
  if (p === "/api/costs") return send(res, 200, report());

  // Brands
  if (parts[1] === "brands") {
    if (parts.length === 2 && m === "GET") return send(res, 200, readCollection("brands"));
    if (parts.length === 2 && m === "POST") {
      const b = sanitizeBrand(await body(req));
      if (!b.name) return send(res, 400, { error: "Cần tên thương hiệu" });
      const created = insert("brands", { id: newId("brand"), kind: "business", ...b, createdAt: new Date().toISOString() });
      emit("brand.created", created);
      return send(res, 201, created);
    }
    const id = seg(2);
    if (m === "GET") return findById("brands", id) ? send(res, 200, findById("brands", id)) : send(res, 404, { error: "not found" });
    if (m === "PUT") {
      const updated = update("brands", id, sanitizeBrand(await body(req)));
      if (!updated) return send(res, 404, { error: "not found" });
      emit("brand.updated", updated);
      return send(res, 200, updated);
    }
    if (m === "DELETE") {
      const ok = remove("brands", id);
      if (ok) emit("brand.deleted", { id });
      return send(res, 200, { ok });
    }
  }

  // Workflows
  if (parts[1] === "generate" && m === "POST") {
    const doc = await runWorkflow(seg(2), await body(req));
    return send(res, 200, doc);
  }

  // Documents
  if (parts[1] === "documents") {
    if (parts.length === 2) {
      const brandId = url.searchParams.get("brandId");
      const type = url.searchParams.get("type");
      const docs = readCollection("documents")
        .filter((d) => (!brandId || d.brandId === brandId) && (!type || d.type === type))
        .reverse();
      return send(res, 200, docs);
    }
    const id = seg(2);
    if (m === "GET") return send(res, 200, findById("documents", id) || { error: "not found" });
    if (m === "DELETE") return send(res, 200, { ok: remove("documents", id) });
  }

  // MCP hub
  if (parts[1] === "mcp") {
    if (p === "/api/mcp/servers") return send(res, 200, hub.status());
    if (parts[2] === "servers" && parts[4] === "connect" && m === "POST") {
      await hub.connect(seg(3));
      return send(res, 200, hub.status().find((s) => s.name === seg(3)));
    }
    if (parts[2] === "servers" && parts[4] === "disconnect" && m === "POST") {
      await hub.disconnect(seg(3));
      return send(res, 200, { ok: true });
    }
    if (parts[2] === "servers" && parts[4] === "tools") return send(res, 200, await hub.listTools(seg(3)));
    if (p === "/api/mcp/call" && m === "POST") {
      const { server, tool, args } = await body(req);
      return send(res, 200, await hub.callTool(server, tool, args || {}));
    }
  }

  // Video studio
  if (parts[1] === "video") {
    if (p === "/api/video/presets") return send(res, 200, await video.presets());
    if (p === "/api/video/jobs") return send(res, 200, video.list());
    if (p === "/api/video/estimate" && m === "POST") return send(res, 200, await video.estimate((await body(req)).spec));
    if (p === "/api/video/submit" && m === "POST") return send(res, 200, await video.submit(await body(req)));
    const jobId = seg(2);
    if (parts[3] === "status") return send(res, 200, await video.status(jobId));
    if (parts[3] === "result") return send(res, 200, await video.result(jobId));
    if (parts[3] === "cancel" && m === "POST") return send(res, 200, await video.cancel(jobId));
    if (parts[3] === "resume" && m === "POST") return send(res, 200, await video.resume(jobId, (await body(req)).maxUsd));
  }

  // Assistant
  if (parts[1] === "assistant") {
    if (p === "/api/assistant" && m === "POST") return send(res, 200, await assistant.send(await body(req)));
    if (p === "/api/assistant/approve" && m === "POST") return send(res, 200, await assistant.approve(await body(req)));
    const s = assistant.getSession(seg(2));
    return s ? send(res, 200, assistant.view(s)) : send(res, 404, { error: "not found" });
  }

  return send(res, 404, { error: "Không có API này" });
}

function authorized(req) {
  if (!API_TOKEN) return true;
  return req.headers.authorization === `Bearer ${API_TOKEN}`;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  try {
    // DNS-rebinding guard: when bound to loopback, only answer to loopback host names.
    const loopback = ["127.0.0.1", "localhost", "::1"].includes(HOST);
    const hostName = (req.headers.host || "").replace(/:\d+$/, "").replace(/^\[|\]$/g, "");
    if (loopback && !["127.0.0.1", "localhost", "::1"].includes(hostName)) return send(res, 403, { error: "host không hợp lệ" });
    if (url.pathname.startsWith("/api/") || url.pathname === "/mcp") {
      // Block cross-site requests from other web pages (the app is same-origin).
      const origin = req.headers.origin;
      if (origin && new URL(origin).host !== req.headers.host) return send(res, 403, { error: "cross-origin bị chặn" });
      if (!authorized(req) && !["/api/manifest", "/api/openapi.json"].includes(url.pathname)) return send(res, 401, { error: "Cần JAYSTUDIO_API_TOKEN" });
      if (url.pathname === "/mcp") return await handleMcp(req, res);
      return await api(req, res, url);
    }
    serveStatic(req, res, url.pathname);
  } catch (err) {
    const code = err instanceof BudgetError ? 402 : err.status || 500;
    if (!res.headersSent) send(res, code, { error: err.message || String(err) });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`Jaystudio Brand OS đang chạy: http://${HOST}:${PORT}`);
  console.log(`MCP (HTTP) cho AIOS: http://${HOST}:${PORT}/mcp`);
  if (!anthropicConfigured()) console.log("Lưu ý: chưa có ANTHROPIC_API_KEY - đặt trong apps/jaystudio/.env");
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, async () => {
    await hub.closeAll();
    process.exit(0);
  });
}
