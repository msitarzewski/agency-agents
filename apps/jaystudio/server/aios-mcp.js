// Jaystudio as an MCP server, so other AIOS agents (Claude Code, Claude Desktop, any MCP client)
// can use the brand tools. Exposed over stdio (npm run mcp) and Streamable HTTP (POST /mcp).
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { readCollection, findById, insert, update, newId } from "./store.js";
import { runWorkflow, WORKFLOWS } from "./workflows.js";
import { listPersonas } from "./personas.js";
import { report } from "./costs.js";
import * as video from "./video.js";
import { sanitizeBrand } from "./brands.js";
import { emit, listEvents } from "./events.js";

const json = (data) => ({ content: [{ type: "text", text: JSON.stringify(data, null, 2) }] });

export function buildMcpServer() {
  const server = new McpServer({ name: "jaystudio-brand-os", version: "1.0.0" });

  server.registerTool("brand_list", { description: "Liệt kê các hồ sơ thương hiệu (cá nhân/doanh nghiệp) đã lưu." }, async () =>
    json(readCollection("brands").map((b) => ({ id: b.id, name: b.name, kind: b.kind, industry: b.industry })))
  );

  server.registerTool(
    "brand_get",
    { description: "Lấy đầy đủ hồ sơ một thương hiệu.", inputSchema: { brandId: z.string() } },
    async ({ brandId }) => json(findById("brands", brandId) || { error: "not found" })
  );

  server.registerTool(
    "brand_upsert",
    {
      description: "Tạo mới (không có brandId) hoặc cập nhật hồ sơ thương hiệu. Trường: name, kind (personal|business), tagline, industry, offer, audience, problems, differentiators, values, voice, competitors, channels, goals, budget, currency, colors, fonts, assets, language, notes.",
      inputSchema: { brandId: z.string().optional(), fields: z.record(z.string(), z.any()) },
    },
    async ({ brandId, fields }) => {
      const clean = sanitizeBrand(fields);
      if (brandId) {
        const updated = update("brands", brandId, clean);
        if (updated) emit("brand.updated", updated);
        return json(updated || { error: "not found" });
      }
      const created = insert("brands", { id: newId("brand"), kind: "business", ...clean, createdAt: new Date().toISOString() });
      emit("brand.created", created);
      return json(created);
    }
  );

  server.registerTool(
    "brand_generate",
    {
      description: `Chạy quy trình thương hiệu và lưu kết quả. workflow: ${WORKFLOWS.join(", ")}. tier: auto|local|eco|balanced|premium (auto = rẻ nhất đủ chất lượng). params tùy quy trình, ví dụ content: {platform, topic, format, count}; calendar: {days, channels}; budget: {amount, currency, goal}; repurpose: {source, targets}; videoSpec: {topic, format, seconds}.`,
      inputSchema: {
        workflow: z.enum(WORKFLOWS),
        brandId: z.string().optional(),
        personaId: z.string().optional(),
        tier: z.enum(["auto", "local", "eco", "balanced", "premium"]).optional(),
        params: z.record(z.string(), z.any()).optional(),
      },
    },
    async (args) => {
      const doc = await runWorkflow(args.workflow, args);
      return json({ id: doc.id, title: doc.title, model: doc.model, costUsd: doc.costUsd, content: doc.content, data: doc.data });
    }
  );

  server.registerTool("brand_personas", { description: "Danh sách chuyên gia (persona) có thể gán cho quy trình qua personaId." }, async () =>
    json(listPersonas().map(({ id, name, description }) => ({ id, name, description })))
  );

  server.registerTool(
    "brand_documents",
    { description: "Liệt kê tài liệu đã tạo (chiến lược, lịch, bài viết...).", inputSchema: { brandId: z.string().optional() } },
    async ({ brandId }) =>
      json(
        readCollection("documents")
          .filter((d) => !brandId || d.brandId === brandId)
          .map(({ id, type, title, brandId: b, costUsd, createdAt }) => ({ id, type, title, brandId: b, costUsd, createdAt }))
      )
  );

  server.registerTool(
    "brand_document_get",
    { description: "Lấy nội dung một tài liệu.", inputSchema: { id: z.string() } },
    async ({ id }) => json(findById("documents", id) || { error: "not found" })
  );

  server.registerTool("brand_cost_report", { description: "Báo cáo chi phí AI tháng này, ngân sách và tiền đã tiết kiệm." }, async () => {
    const r = report();
    delete r.recent;
    return json(r);
  });

  server.registerTool(
    "brand_video_submit",
    {
      description: "Gửi spec video (từ workflow videoSpec) tới video-toolkit. Trả về jobId; kiểm tra bằng brand_video_status.",
      inputSchema: { spec: z.record(z.string(), z.any()), maxUsd: z.number().optional(), brandId: z.string().optional() },
    },
    async (args) => json(await video.submit(args))
  );

  server.registerTool(
    "brand_video_status",
    { description: "Trạng thái job video; khi xong trả về kết quả MP4.", inputSchema: { jobId: z.string() } },
    async ({ jobId }) => {
      const s = await video.status(jobId);
      if ((s?.phase || s?.status) === "done") return json({ status: s, result: await video.result(jobId) });
      return json(s);
    }
  );

  server.registerTool(
    "brand_events",
    {
      description: "Đọc nhật ký sự kiện (brand.*, document.created, video.job.*, budget.*). Truyền since = id sự kiện cuối đã xử lý để chỉ lấy cái mới.",
      inputSchema: { since: z.string().optional(), type: z.string().optional(), limit: z.number().optional() },
    },
    async (args) => json(listEvents(args))
  );

  return server;
}
