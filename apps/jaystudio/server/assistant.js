// Studio assistant: Claude with the connected MCP tools, run in a manual tool loop.
// Tools that can spend money pause the loop until the user approves them in the UI.
import { chatTurn } from "./llm.js";
import * as hub from "./mcp-hub.js";
import { brandContext } from "./workflows.js";
import { findById, readMap, writeMap, newId } from "./store.js";
import { getSettings } from "./config.js";

const MAX_STEPS = 12;
const MAX_RESULT_CHARS = 60_000;
const SEP = "__"; // Claude tool name = <server>__<tool>

const SYSTEM = `Bạn là trợ lý sản xuất của Jaystudio Brand OS (đạo diễn + biên tập + kỹ sư).
Bạn có các công cụ MCP về video/AI. Quy tắc:
- Kiểm tra trước (info/doctor/estimate/plan), rồi mới làm. Với tác vụ tốn phí, nêu chi phí ước tính trước khi gọi.
- Ưu tiên công cụ miễn phí chạy local (mcp-video, các tool FFmpeg của VibeFrame) trước công cụ AI trả phí.
- Đường dẫn file dùng đường dẫn tuyệt đối. Không bao giờ ghi đè file gốc.
- Không dùng nhạc/hình/nhân vật có bản quyền hay ảnh người nổi tiếng.
- Sau khi xong: tóm tắt 2-3 dòng (đã làm gì, file đầu ra, bước tiếp theo nên làm). Trả lời bằng tiếng Việt.`;

function sessions() {
  return readMap("assistant-sessions");
}
function saveSession(s) {
  const all = sessions();
  all[s.id] = s;
  writeMap("assistant-sessions", all);
}

export function getSession(id) {
  return sessions()[id] || null;
}

async function toolsFor(servers) {
  const tools = [];
  const errors = [];
  for (const server of servers) {
    try {
      for (const t of await hub.listTools(server)) {
        const name = `${server}${SEP}${t.name}`.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 64);
        tools.push({
          name,
          description: `[${server}${t.paid ? ", TỐN PHÍ - cần người dùng duyệt" : ""}] ${t.description || ""}`.slice(0, 1024),
          input_schema: t.inputSchema || { type: "object", properties: {} },
          _server: server,
          _tool: t.name,
          _paid: t.paid,
        });
      }
    } catch (e) {
      errors.push(e.message);
    }
  }
  return { tools, errors };
}

function toolResultContent(res) {
  const out = [];
  let chars = 0;
  for (const c of res?.content || []) {
    if (c.type === "text") {
      let text = c.text;
      if (chars + text.length > MAX_RESULT_CHARS) {
        text = text.slice(0, Math.max(0, MAX_RESULT_CHARS - chars)) + "\n[Kết quả quá dài, đã cắt bớt]";
      }
      chars += text.length;
      out.push({ type: "text", text });
    } else if (c.type === "image" && c.data) {
      out.push({ type: "image", source: { type: "base64", media_type: c.mimeType || "image/png", data: c.data } });
    } else if (c.type === "resource" && c.resource?.text) {
      out.push({ type: "text", text: c.resource.text.slice(0, 20_000) });
    }
  }
  if (!out.length) out.push({ type: "text", text: res?.structuredContent ? JSON.stringify(res.structuredContent) : "(không có nội dung)" });
  return out;
}

async function runTool(map, block) {
  const def = map.get(block.name);
  if (!def) return { type: "tool_result", tool_use_id: block.id, is_error: true, content: `Không có công cụ ${block.name}` };
  try {
    const res = await hub.callTool(def._server, def._tool, block.input || {});
    return { type: "tool_result", tool_use_id: block.id, is_error: Boolean(res.isError), content: toolResultContent(res) };
  } catch (e) {
    return { type: "tool_result", tool_use_id: block.id, is_error: true, content: `Lỗi: ${e.message}` };
  }
}

// Continue the loop until Claude finishes, hits the step cap, or a paid tool needs approval.
async function loop(session, decisions = null) {
  const settings = getSettings();
  const { tools, errors } = await toolsFor(session.servers);
  const map = new Map(tools.map((t) => [t.name, t]));
  const apiTools = tools.map(({ name, description, input_schema }) => ({ name, description, input_schema }));
  if (apiTools.length) apiTools[apiTools.length - 1].cache_control = { type: "ephemeral" };

  const brand = session.brandId ? findById("brands", session.brandId) : null;
  const system = [{ type: "text", text: SYSTEM }, { type: "text", text: brandContext(brand), cache_control: { type: "ephemeral" } }];

  // Resolve tool calls that were waiting for approval.
  if (session.pending?.length && decisions) {
    const results = [];
    for (const p of session.pending) {
      if (decisions[p.id]) results.push(await runTool(map, p));
      else results.push({ type: "tool_result", tool_use_id: p.id, is_error: true, content: "Người dùng không duyệt lệnh này. Đề xuất cách khác rẻ hơn hoặc hỏi lại." });
    }
    session.pending = [];
    session.messages.push({ role: "user", content: results });
  }

  for (let step = 0; step < MAX_STEPS; step++) {
    const { msg, costUsd, tier } = await chatTurn({ tier: session.tier, system, messages: session.messages, tools: apiTools });
    session.costUsd = (session.costUsd || 0) + costUsd;
    session.lastModel = msg.model;
    session.lastTier = tier;
    session.messages.push({ role: "assistant", content: msg.content }); // keep every block (thinking included)

    if (msg.stop_reason === "refusal") {
      session.notice = "Claude từ chối yêu cầu này. Hãy diễn đạt lại.";
      break;
    }
    if (msg.stop_reason !== "tool_use") break;

    const calls = msg.content.filter((b) => b.type === "tool_use");
    const needApproval = settings.approvePaidTools ? calls.filter((c) => map.get(c.name)?._paid) : [];
    if (needApproval.length) {
      // Run the free calls now? No: all results of one turn must go back together, so pause the whole turn.
      session.pending = calls.map((c) => ({ id: c.id, name: c.name, input: c.input, paid: Boolean(map.get(c.name)?._paid) }));
      break;
    }
    const results = await Promise.all(calls.map((c) => runTool(map, c)));
    session.messages.push({ role: "user", content: results });
  }
  session.toolErrors = errors;
  session.updatedAt = new Date().toISOString();
  saveSession(session);
  return view(session);
}

export function view(s) {
  // Compact transcript for the UI: text, tool calls and results.
  const items = [];
  for (const m of s.messages) {
    const blocks = typeof m.content === "string" ? [{ type: "text", text: m.content }] : m.content;
    for (const b of blocks) {
      if (b.type === "text" && b.text) items.push({ role: m.role, kind: "text", text: b.text });
      else if (b.type === "tool_use") items.push({ role: "assistant", kind: "tool_use", id: b.id, name: b.name, input: b.input });
      else if (b.type === "tool_result") {
        const text = Array.isArray(b.content) ? b.content.filter((c) => c.type === "text").map((c) => c.text).join("\n") : String(b.content);
        items.push({ role: "tool", kind: "tool_result", id: b.tool_use_id, error: Boolean(b.is_error), text: text.slice(0, 4000) });
      }
    }
  }
  return {
    id: s.id,
    brandId: s.brandId,
    servers: s.servers,
    tier: s.tier,
    costUsd: s.costUsd || 0,
    lastModel: s.lastModel,
    pending: s.pending || [],
    notice: s.notice || null,
    toolErrors: s.toolErrors || [],
    items,
  };
}

export async function send({ sessionId, message, brandId, servers, tier }) {
  let s = sessionId ? getSession(sessionId) : null;
  if (!s) {
    s = { id: newId("chat"), brandId: brandId || null, servers: servers || getSettings().assistantServers, tier: tier || "auto", messages: [], costUsd: 0, createdAt: new Date().toISOString() };
  }
  if (s.pending?.length) throw new Error("Đang chờ bạn duyệt lệnh công cụ trước.");
  if (servers) s.servers = servers;
  if (tier) s.tier = tier;
  if (brandId !== undefined) s.brandId = brandId || null;
  s.notice = null;
  s.messages.push({ role: "user", content: message });
  return loop(s);
}

export async function approve({ sessionId, decisions }) {
  const s = getSession(sessionId);
  if (!s) throw new Error("Không tìm thấy phiên trợ lý");
  if (!s.pending?.length) return view(s);
  // Free calls in the same turn run automatically; paid ones follow the user's decision.
  const full = {};
  for (const p of s.pending) full[p.id] = p.paid ? Boolean(decisions?.[p.id]) : true;
  return loop(s, full);
}
