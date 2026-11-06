// OpenAPI 3.1 description of the REST API, served at GET /api/openapi.json.
// Lets any AIOS component (CRM, n8n, Make, Zapier, custom agents) generate a client automatically.
import { WORKFLOWS } from "./workflows.js";
import { EVENT_TYPES } from "./events.js";
import { BRAND_FIELDS } from "./brands.js";

const ref = (name) => ({ $ref: `#/components/schemas/${name}` });
const json = (schema, description = "OK") => ({ description, content: { "application/json": { schema } } });
const body = (schema) => ({ required: true, content: { "application/json": { schema } } });
const idParam = (name) => ({ name, in: "path", required: true, schema: { type: "string" } });
const errors = { 400: json(ref("Error"), "Yêu cầu sai"), 401: json(ref("Error"), "Thiếu token"), 402: json(ref("Error"), "Vượt ngân sách"), 500: json(ref("Error"), "Lỗi") };

const TAG_INFO = {
  brands: "Hồ sơ thương hiệu cá nhân / doanh nghiệp",
  generate: "Quy trình AI: chiến lược, ngân sách, lịch, nội dung, tái chế, A/B, spec video",
  documents: "Kết quả đã tạo",
  video: "Video studio qua video-toolkit",
  events: "Nhật ký sự kiện và webhook",
  system: "Trạng thái, chi phí, khám phá",
  aios: "Connector tới AIOS Brand OS (đẩy bản nháp, lead, video; nhập thương hiệu)",
};

// Fill summary/operationId where missing so generated clients get readable names.
function finish(spec) {
  const human = (id) => id.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase());
  for (const item of Object.values(spec.paths)) {
    for (const op of Object.values(item)) if (op && op.operationId && !op.summary) op.summary = human(op.operationId);
  }
  for (const [name, item] of Object.entries(spec.webhooks)) {
    item.post.operationId = "on_" + name.replace(/\W/g, "_");
  }
  return spec;
}

export function openapi(version, serverUrl) {
  return finish({
    openapi: "3.1.0",
    info: {
      title: "Jaystudio Brand OS API",
      version,
      description:
        "Xây dựng thương hiệu cá nhân/doanh nghiệp tối ưu chi phí. Cùng dữ liệu được mở qua MCP tại /mcp và sự kiện qua webhook (Standard Webhooks).",
    },
    servers: [{ url: serverUrl }],
    security: [{ bearer: [] }, {}],
    tags: Object.entries(TAG_INFO).map(([name, description]) => ({ name, description })),
    paths: {
      "/api/brands": {
        get: { tags: ["brands"], operationId: "listBrands", responses: { 200: json({ type: "array", items: ref("Brand") }) } },
        post: { tags: ["brands"], operationId: "createBrand", requestBody: body(ref("BrandInput")), responses: { 201: json(ref("Brand")), ...errors } },
      },
      "/api/brands/{id}": {
        parameters: [idParam("id")],
        get: { tags: ["brands"], operationId: "getBrand", responses: { 200: json(ref("Brand")), 404: json(ref("Error")) } },
        put: { tags: ["brands"], operationId: "updateBrand", requestBody: body(ref("BrandInput")), responses: { 200: json(ref("Brand")) } },
        delete: { tags: ["brands"], operationId: "deleteBrand", responses: { 200: json({ type: "object", properties: { ok: { type: "boolean" } } }) } },
      },
      "/api/generate/{workflow}": {
        parameters: [{ name: "workflow", in: "path", required: true, schema: { type: "string", enum: WORKFLOWS } }],
        post: {
          tags: ["generate"],
          operationId: "runWorkflow",
          description:
            "Chạy một quy trình và lưu kết quả. params theo quy trình: strategy {focus}; budget {amount, currency, period, goal}; calendar {days, channels, frequency}; content {platform, format, topic, count, extra}; repurpose {source, targets}; variants {topic, kind, count}; videoSpec {topic, format, seconds, language}.",
          requestBody: body({
            type: "object",
            properties: {
              brandId: { type: "string" },
              personaId: { type: "string", description: "Ví dụ marketing/marketing-tiktok-strategist (GET /api/personas)" },
              tier: { type: "string", enum: ["auto", "local", "eco", "balanced", "premium"], default: "auto" },
              params: { type: "object", additionalProperties: true },
            },
          }),
          responses: { 200: json(ref("Document")), ...errors },
        },
      },
      "/api/documents": {
        get: {
          tags: ["documents"],
          operationId: "listDocuments",
          parameters: [
            { name: "brandId", in: "query", schema: { type: "string" } },
            { name: "type", in: "query", schema: { type: "string", enum: WORKFLOWS } },
          ],
          responses: { 200: json({ type: "array", items: ref("Document") }) },
        },
      },
      "/api/documents/{id}": {
        parameters: [idParam("id")],
        get: { tags: ["documents"], operationId: "getDocument", responses: { 200: json(ref("Document")) } },
        delete: { tags: ["documents"], operationId: "deleteDocument", responses: { 200: json({ type: "object" }) } },
      },
      "/api/personas": { get: { tags: ["generate"], operationId: "listPersonas", responses: { 200: json({ type: "array", items: { type: "object" } }) } } },
      "/api/video/estimate": { post: { tags: ["video"], operationId: "estimateVideo", requestBody: body({ type: "object", properties: { spec: { type: "object" } }, required: ["spec"] }), responses: { 200: json({ type: "object" }) } } },
      "/api/video/submit": {
        post: {
          tags: ["video"],
          operationId: "submitVideo",
          requestBody: body({ type: "object", properties: { spec: { type: "object" }, maxUsd: { type: "number", default: 2 }, brandId: { type: "string" } }, required: ["spec"] }),
          responses: { 200: json({ type: "object", properties: { jobId: { type: "string" } } }), ...errors },
        },
      },
      "/api/video/jobs": { get: { tags: ["video"], operationId: "listVideoJobs", responses: { 200: json({ type: "array", items: { type: "object" } }) } } },
      "/api/video/{jobId}/status": { parameters: [idParam("jobId")], get: { tags: ["video"], operationId: "videoStatus", responses: { 200: json({ type: "object" }) } } },
      "/api/video/{jobId}/result": { parameters: [idParam("jobId")], get: { tags: ["video"], operationId: "videoResult", responses: { 200: json({ type: "object" }) } } },
      "/api/events": {
        get: {
          tags: ["events"],
          operationId: "listEvents",
          description: "Nhật ký sự kiện để đồng bộ bằng polling. Truyền `since` = id sự kiện cuối cùng đã xử lý.",
          parameters: [
            { name: "since", in: "query", schema: { type: "string" } },
            { name: "type", in: "query", schema: { type: "string" }, description: "Ví dụ video.* hoặc document.created" },
            { name: "limit", in: "query", schema: { type: "integer", default: 100, maximum: 500 } },
          ],
          responses: { 200: json({ type: "array", items: ref("Event") }) },
        },
      },
      "/api/webhooks": {
        get: { tags: ["events"], operationId: "listWebhooks", responses: { 200: json({ type: "array", items: ref("Webhook") }) } },
        post: {
          tags: ["events"],
          operationId: "createWebhook",
          description: "Đăng ký URL nhận sự kiện. Phản hồi chứa `secret` (chỉ hiện một lần) để kiểm chữ ký webhook-signature.",
          requestBody: body({ type: "object", properties: { url: { type: "string", format: "uri" }, events: { type: "array", items: { type: "string" }, default: ["*"] }, description: { type: "string" } }, required: ["url"] }),
          responses: { 201: json(ref("Webhook")), ...errors },
        },
      },
      "/api/webhooks/{id}": { parameters: [idParam("id")], delete: { tags: ["events"], operationId: "deleteWebhook", responses: { 200: json({ type: "object" }) } } },
      "/api/webhooks/{id}/test": { parameters: [idParam("id")], post: { tags: ["events"], operationId: "testWebhook", responses: { 200: json({ type: "object" }) } } },
      "/api/aios/status": { get: { tags: ["aios"], operationId: "aiosStatus", responses: { 200: json({ type: "object" }) } } },
      "/api/aios/brands": { get: { tags: ["aios"], operationId: "aiosListBrands", description: "Thương hiệu bên AIOS Brand OS", responses: { 200: json({ type: "array", items: { type: "object" } }) } } },
      "/api/aios/brands/import": { post: { tags: ["aios"], operationId: "aiosImportBrand", requestBody: body({ type: "object", properties: { remoteId: { type: "string" } }, required: ["remoteId"] }), responses: { 200: json(ref("Brand")) } } },
      "/api/aios/brands/{id}/push": { parameters: [idParam("id")], post: { tags: ["aios"], operationId: "aiosPushBrand", responses: { 200: json({ type: "object", properties: { aiosBrandId: { type: "string" } } }) } } },
      "/api/aios/documents/{id}/push": { parameters: [idParam("id")], post: { tags: ["aios"], operationId: "aiosPushDocument", responses: { 200: json({ type: "object", properties: { projectId: { type: "string" }, version: { type: "integer" }, unchanged: { type: "boolean" } } }) } } },
      "/api/aios/leads": { post: { tags: ["aios"], operationId: "aiosPushLead", requestBody: body({ type: "object", properties: { name: { type: "string" }, email: { type: "string" }, source: { type: "string" } }, required: ["name"] }), responses: { 200: json({ type: "object", properties: { leadId: { type: "string" }, duplicate: { type: "boolean" } } }) } } },
      "/api/aios/media": { post: { tags: ["aios"], operationId: "aiosPushVideo", requestBody: body({ type: "object", properties: { filePath: { type: "string" }, brandId: { type: "string" } }, required: ["filePath", "brandId"] }), responses: { 200: json({ type: "object", properties: { mediaId: { type: "string" } } }) } } },
      "/api/aios/sync-log": { get: { tags: ["aios"], operationId: "aiosSyncLog", responses: { 200: json({ type: "array", items: { type: "object" } }) } } },
      "/api/costs": { get: { tags: ["system"], operationId: "costReport", responses: { 200: json({ type: "object" }) } } },
      "/api/status": { get: { tags: ["system"], operationId: "status", responses: { 200: json({ type: "object" }) } } },
      "/api/manifest": { get: { tags: ["system"], operationId: "manifest", security: [{}], responses: { 200: json({ type: "object" }) } } },
    },
    webhooks: Object.fromEntries(
      EVENT_TYPES.map((t) => [t, { post: { summary: `Sự kiện ${t}`, requestBody: body(ref("Event")), responses: { 200: { description: "Nhận thành công (2xx)" } } } }])
    ),
    components: {
      securitySchemes: { bearer: { type: "http", scheme: "bearer", description: "JAYSTUDIO_API_TOKEN (khi đã đặt)" } },
      schemas: {
        Error: { type: "object", properties: { error: { type: "string" } } },
        BrandInput: {
          type: "object",
          properties: Object.fromEntries(
            BRAND_FIELDS.map((f) => [
              f,
              f === "budget" ? { type: "number" } : f === "channels" ? { type: "array", items: { type: "string" } } : f === "kind" ? { type: "string", enum: ["personal", "business"] } : { type: "string" },
            ])
          ),
        },
        Brand: { allOf: [ref("BrandInput"), { type: "object", properties: { id: { type: "string" }, createdAt: { type: "string" }, updatedAt: { type: "string" } } }] },
        Document: {
          type: "object",
          properties: {
            id: { type: "string" },
            type: { type: "string", enum: WORKFLOWS },
            brandId: { type: ["string", "null"] },
            title: { type: "string" },
            content: { type: "string", description: "Markdown" },
            data: { description: "JSON có cấu trúc (videoSpec)" },
            model: { type: "string" },
            tier: { type: "string" },
            costUsd: { type: "number" },
            cached: { type: "boolean" },
            createdAt: { type: "string" },
          },
        },
        Event: {
          type: "object",
          properties: { id: { type: "string" }, type: { type: "string", enum: EVENT_TYPES }, timestamp: { type: "string" }, source: { type: "string" }, data: { type: "object" } },
        },
        Webhook: {
          type: "object",
          properties: { id: { type: "string" }, url: { type: "string" }, events: { type: "array", items: { type: "string" } }, secret: { type: "string" }, active: { type: "boolean" }, lastStatus: { type: ["integer", "null"] } },
        },
      },
    },
  });
}
