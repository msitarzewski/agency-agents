// MCP client hub: connects to the video/AI MCP servers listed in mcp.config.json.
import fs from "node:fs";
import path from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { APP_DIR, REPO_ROOT } from "./config.js";

const CONFIG_FILE = path.join(APP_DIR, "mcp.config.json");

// What each server is for, shown in the UI and given to the assistant.
export const SERVER_INFO = {
  "mcp-video": { label: "mcp-video", role: "Cắt, ghép, chèn chữ, nhạc, đổi khung, Shorts, QC - chạy local, miễn phí" },
  vibeframe: { label: "VibeFrame", role: "Storyboard, dựng cảnh, phụ đề động, lồng tiếng, sinh ảnh/video/nhạc AI, remix Shorts" },
  "video-toolkit": { label: "Video Toolkit", role: "Brief -> video giải thích hoàn chỉnh (giọng, hình, phụ đề, nhạc, QC), có báo giá" },
  pixelle: { label: "Pixelle (ComfyUI)", role: "Workflow ComfyUI: ảnh, sửa ảnh, video, giọng nói - local GPU hoặc RunningHub" },
};

// Tools that can spend money or take long; the assistant asks before running them.
const PAID = /^(generate_|remix_|audio_(dub|clone_voice|isolate|transcribe)$|edit_(grade|speed_ramp|motion_overlay|translate_srt|fill_gaps|image|jump_cut|caption|animated_caption)$|inspect_(media|suggest)$|video_(submit|resume)$|build$|render$|scene_add$)/;

export function isPaidTool(server, tool) {
  return server === "pixelle" || PAID.test(tool);
}

export function loadConfig() {
  const file = fs.existsSync(CONFIG_FILE) ? CONFIG_FILE : path.join(REPO_ROOT, ".mcp.json");
  const raw = JSON.parse(fs.readFileSync(file, "utf8"));
  return raw.mcpServers || {};
}

const conns = new Map(); // name -> { client, status, error, tools, toolsAt }

export function status() {
  const cfg = loadConfig();
  return Object.entries(cfg).map(([name, c]) => {
    const conn = conns.get(name);
    return {
      name,
      ...(SERVER_INFO[name] || { label: name, role: "" }),
      type: c.type || (c.url ? "http" : "stdio"),
      target: c.url || [c.command, ...(c.args || [])].join(" "),
      status: conn?.status || "disconnected",
      error: conn?.error || null,
      toolCount: conn?.tools?.length || 0,
    };
  });
}

export async function connect(name) {
  const existing = conns.get(name);
  if (existing?.status === "connected") return existing;
  if (existing?.pending) return existing.pending;

  const cfg = loadConfig()[name];
  if (!cfg) throw new Error(`Không có MCP server "${name}" trong mcp.config.json`);

  const pending = (async () => {
    const client = new Client({ name: "jaystudio-brand-os", version: "1.0.0" });
    let transport;
    if ((cfg.type || "") === "http" || cfg.url) {
      transport = new StreamableHTTPClientTransport(new URL(cfg.url), { requestInit: { headers: cfg.headers || {} } });
    } else {
      transport = new StdioClientTransport({
        command: cfg.command,
        args: cfg.args || [],
        env: { ...process.env, ...(cfg.env || {}) },
        cwd: REPO_ROOT,
        stderr: "ignore",
      });
    }
    try {
      await client.connect(transport, { timeout: 120_000 });
      const { tools } = await client.listTools();
      const conn = { client, status: "connected", error: null, tools, toolsAt: Date.now() };
      client.onclose = () => conns.set(name, { status: "disconnected", error: "Kết nối đã đóng" });
      conns.set(name, conn);
      return conn;
    } catch (err) {
      const msg = err.code === "ECONNREFUSED" || /fetch failed|ECONNREFUSED/.test(String(err))
        ? "Không kết nối được. Server chưa chạy? (Pixelle: chạy `pixelle start`)"
        : err.message;
      conns.set(name, { status: "error", error: msg });
      throw new Error(`${name}: ${msg}`);
    }
  })();
  conns.set(name, { status: "connecting", pending });
  return pending;
}

export async function disconnect(name) {
  const conn = conns.get(name);
  conns.delete(name);
  if (conn?.client) await conn.client.close().catch(() => {});
}

export async function listTools(name) {
  const conn = await connect(name);
  return conn.tools.map((t) => ({ ...t, paid: isPaidTool(name, t.name) }));
}

export async function callTool(name, tool, args = {}, timeoutMs = 15 * 60_000) {
  const conn = await connect(name);
  const res = await conn.client.callTool({ name: tool, arguments: args }, undefined, {
    timeout: timeoutMs,
    resetTimeoutOnProgress: true,
  });
  return res;
}

// Parse the first JSON text block of a tool result (most video tools reply with JSON).
export function resultJson(res) {
  if (res?.structuredContent) return res.structuredContent;
  const t = (res?.content || []).find((c) => c.type === "text")?.text;
  if (!t) return null;
  try {
    return JSON.parse(t);
  } catch {
    return { text: t };
  }
}

export async function closeAll() {
  await Promise.all([...conns.keys()].map(disconnect));
}
