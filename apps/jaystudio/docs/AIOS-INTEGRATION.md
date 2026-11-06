# Tích hợp Jaystudio Brand OS vào AIOS

Tài liệu này dành cho người kỹ thuật nối Jaystudio với các thành phần khác của AIOS (CRM, tự động hóa, agent AI).

## AIOS hiện tại (khảo sát repo `vitusngochai68-code/AIOS-CRM`, commit `3ff28c1`)

| Thành phần | Công nghệ | Cách tích hợp hiện có |
|---|---|---|
| **AIOS CRM V2.1** (gốc repo) | Next.js + Prisma + PostgreSQL | REST nội bộ `/api/...` cho giao diện web; phiên cookie + kiểm tra Origin; chưa có API cho hệ thống ngoài |
| **AIOS Brand OS V1.0** (`brand-os/`) | NestJS + Prisma + PostgreSQL + BullMQ + S3 | REST `/api/v1`, có Swagger/OpenAPI ở `/api/docs`; đăng nhập `POST auth/login` → cookie `brandos_session`; workspace qua header `x-organization-id`; mọi request ghi phải có `Origin` = `WEB_ORIGIN` |

Master Prompt của Brand OS (mục IX) yêu cầu: "connector có thể cấu hình", "đồng bộ có idempotency", "ghi log các lần đồng bộ",
"không giả định dùng chung database", "webhook có chữ ký". AIOS chưa dùng MCP và chưa có API token cho máy.

**Kết luận thiết kế:**
1. Jaystudio nói đúng "ngôn ngữ" của AIOS: REST JSON, OpenAPI, webhook có chữ ký.
2. Có thêm **connector AIOS Brand OS** (`server/connectors/aios-brandos.js`), gọi đúng API thật của AIOS.
3. AIOS vẫn là **hệ thống gốc** về duyệt và đăng bài. Jaystudio chỉ là "xưởng AI": mọi thứ gửi sang đều là **bản nháp**, có ghi rõ nguồn AI, nên giữ đúng nguyên tắc maker–checker (người lập khác người duyệt) của AIOS.

## Connector AIOS Brand OS

| Jaystudio → AIOS | API AIOS dùng | Chống trùng |
|---|---|---|
| Đồng bộ thương hiệu | `POST /brands`, `PATCH /brands/:id` | Liên kết lưu ở `brand.aios.brandId`; lần sau là cập nhật (AIOS tăng version) |
| Gửi tài liệu (bài viết, lịch, chiến lược, spec video...) | `POST /content-projects`, `POST /content-projects/:id/versions` | Nội dung giống hệt thì bỏ qua; nội dung đổi thì thành version mới của cùng project |
| Gửi lead | `POST /leads` | Không gửi lại cùng email (hoặc tên) + nguồn |
| Gửi video MP4 (≤ 50 MB) | `POST /media/upload` | Ghi log mỗi lần |
| AIOS → Jaystudio: nhập thương hiệu | `GET /brands`, `GET /brands/:id` | Nhập lại là cập nhật, không tạo bản sao |

Mỗi lần đồng bộ được ghi vào `data/aios-sync.json` (xem ở trang Kết nối → Nhật ký đồng bộ) và phát sự kiện
`aios.sync.succeeded` / `aios.sync.failed`. Tùy chọn **tự gửi**: mọi tài liệu mới của thương hiệu đã liên kết tự sang AIOS.

Cấu hình trong `apps/jaystudio/.env`:

```
AIOS_BRANDOS_URL=http://localhost:4000/api/v1
AIOS_BRANDOS_ORIGIN=http://localhost:3001     # đúng giá trị WEB_ORIGIN của Brand OS
AIOS_BRANDOS_EMAIL=jaystudio@cong-ty.vn       # tài khoản dịch vụ riêng
AIOS_BRANDOS_PASSWORD=...
AIOS_BRANDOS_ORG_ID=                          # chỉ cần khi tài khoản thuộc nhiều workspace
```

**Tạo tài khoản dịch vụ:**
1. Đăng ký một tài khoản riêng trên AIOS Brand OS.
2. OWNER thêm email đó vào workspace ở mục Thành viên, với vai trò **CONTENT_MANAGER** (hoặc BRAND_MANAGER).
3. Không dùng tài khoản OWNER hay APPROVER. Nhờ vậy Jaystudio không thể tự duyệt hay tự đăng.

**Kiểm thử:** `npm run test:aios` (đặt `AIOS_BRANDOS_URL` trỏ tới một AIOS Brand OS **dùng để thử**; script tự tạo 2 tài khoản test).
Bản hiện tại đã chạy trên API thật của AIOS Brand OS (PostgreSQL nhúng PGlite): 17/17 kiểm tra đạt.

## Đề xuất cho phía AIOS (để tích hợp bền hơn)

Không bắt buộc, nhưng nên làm khi AIOS mở rộng:

1. **Token cho máy** (service token / API key theo workspace), thay cho việc đăng nhập bằng mật khẩu và giả Origin của trình duyệt.
2. **Webhook đi từ AIOS**, ví dụ khi bản nháp được duyệt hay bài đã đăng. Khi đó Jaystudio có thể học từ nội dung được duyệt và theo dõi hiệu quả.
3. **Idempotency-Key** cho `POST /leads` và `POST /content-projects` (đã có trong bảng `idempotency_keys` của Master Prompt). Phía AIOS tự chống trùng, không chỉ dựa vào log của Jaystudio.
4. **Gắn nhãn nguồn AI** cho content version (cột `provider`/`model` đã có trong schema nhưng API thủ công chưa nhận). Hiện Jaystudio ghi nguồn ở cuối nội dung.
5. **CRM V2.1** cần một API cho hệ thống ngoài nếu muốn lead từ Brand OS/Jaystudio chảy vào CRM (Master Prompt mục 10 có ghi "CRM sync adapter").

---

Ngoài connector trên, Jaystudio còn mở **ba chuẩn mở, phổ biến** để mọi thành phần AIOS khác nối vào.

| Bạn cần | Dùng chuẩn | Ở đâu |
|---|---|---|
| Một **agent AI** (Claude, trợ lý khác) dùng tính năng của Jaystudio | **MCP** (Model Context Protocol) | `http://127.0.0.1:4321/mcp` (HTTP) hoặc `node apps/jaystudio/server/mcp-stdio.js` (stdio) |
| Một **phần mềm** (CRM, n8n, Make, Zapier, backend riêng) gọi Jaystudio | **REST + OpenAPI 3.1** | `GET /api/openapi.json`: nhập file này vào công cụ là có client tự động |
| Hệ thống khác **được báo ngay** khi có việc xảy ra | **Webhook** chuẩn [Standard Webhooks](https://www.standardwebhooks.com) | Đăng ký URL trong app (Kết nối → Webhook) hoặc `POST /api/webhooks` |
| Không mở được cổng nhận webhook | **Event feed** (polling) | `GET /api/events?since=<id sự kiện cuối>` |

Cả bốn đường dùng **chung dữ liệu**. Một thương hiệu tạo qua MCP sẽ hiện ngay trên web, qua REST và sinh sự kiện `brand.created`.

## Vì sao chọn bộ chuẩn này

- **MCP** là chuẩn chung để agent AI dùng công cụ. Claude, ChatGPT, Cursor và nhiều agent framework đều hỗ trợ.
- **OpenAPI** là cách mô tả REST API phổ biến nhất. CRM, nền tảng low-code và trình sinh SDK đều đọc được.
- **Standard Webhooks** là quy ước ký webhook công khai (cùng kiểu Svix, nhiều SaaS dùng). Bên nhận có thư viện sẵn để kiểm chữ ký.
- **Event feed** là đường dự phòng cho hệ thống chỉ chạy nội bộ, không nhận được kết nối từ ngoài.

Thêm thành phần AIOS mới không cần sửa Jaystudio: thành phần đó chỉ cần nói một trong bốn "ngôn ngữ" trên.

## Xác thực

- Mặc định app chỉ nghe ở `127.0.0.1`, nên chỉ chương trình trên cùng máy gọi được.
- Muốn máy khác trong AIOS gọi vào, đặt trong `.env`:

  ```
  JAYSTUDIO_HOST=0.0.0.0
  JAYSTUDIO_API_TOKEN=<chuỗi ngẫu nhiên dài>
  ```

  Mọi request `/api/*` và `/mcp` khi đó phải có header `Authorization: Bearer <token>`. Ngoại lệ là `/api/manifest` và `/api/openapi.json`, vốn chỉ chứa mô tả.
- Khi mở ra mạng, nên đặt sau reverse proxy có HTTPS (Caddy, Nginx).

## Sự kiện

Mỗi sự kiện có dạng:

```json
{
  "id": "evt_3f9a...",
  "type": "document.created",
  "timestamp": "2026-11-06T10:00:00.000Z",
  "source": "jaystudio-brand-os",
  "data": { "id": "doc_...", "type": "content", "title": "TikTok: ...", "brandId": "brand_...", "costUsd": 0.004, "url": "/api/documents/doc_..." }
}
```

| Loại | Khi nào | Gợi ý dùng trong AIOS |
|---|---|---|
| `brand.created` / `brand.updated` / `brand.deleted` | Hồ sơ thương hiệu thay đổi | Đồng bộ thông tin khách hàng hoặc dự án trong CRM |
| `document.created` | Tạo xong chiến lược, ngân sách, lịch, bài viết, tái chế, A/B, spec video | Tạo task duyệt nội dung, đưa vào lịch đăng, lưu vào hồ sơ khách |
| `video.job.submitted` / `video.job.completed` / `video.job.failed` | Video bắt đầu, xong hoặc lỗi | Báo cho người phụ trách; đăng video tự động khi xong |
| `budget.warning` | Chi phí AI tháng vượt 80% ngân sách | Cảnh báo quản lý |
| `budget.exceeded` | Một yêu cầu bị chặn vì hết ngân sách | Cảnh báo và tăng ngân sách hoặc chờ sang tháng |
| `webhook.test` | Bấm "Gửi thử" | Kiểm tra kết nối |

Khi đăng ký, có thể lọc theo mẫu: `*` (tất cả), `video.*`, hoặc liệt kê từng loại như `document.created,budget.warning`.

### Gửi webhook

Jaystudio gửi `POST` JSON tới URL đã đăng ký, kèm 3 header:

| Header | Nội dung |
|---|---|
| `webhook-id` | id sự kiện, dùng để chống xử lý trùng |
| `webhook-timestamp` | thời điểm gửi (giây, Unix) |
| `webhook-signature` | `v1,` + base64(HMAC-SHA256(`<id>.<timestamp>.<body>`, khóa)) |

Khóa là phần sau `whsec_` của `secret`, giải mã base64. `secret` chỉ hiện **một lần** khi đăng ký.

Trả về 2xx là coi như đã nhận. Lỗi mạng, 408, 429 hay 5xx thì được gửi lại tối đa 3 lần (sau 2 giây, 15 giây và 60 giây). Các lỗi 4xx khác không gửi lại.

### Mã mẫu nhận webhook

Node.js (không cần thư viện):

```js
import http from "node:http";
import crypto from "node:crypto";

const SECRET = process.env.JAYSTUDIO_WEBHOOK_SECRET; // whsec_...
const key = Buffer.from(SECRET.replace(/^whsec_/, ""), "base64");

http.createServer(async (req, res) => {
  let raw = "";
  for await (const c of req) raw += c;
  const { "webhook-id": id, "webhook-timestamp": ts, "webhook-signature": sig } = req.headers;
  const expected = "v1," + crypto.createHmac("sha256", key).update(`${id}.${ts}.${raw}`).digest("base64");
  const fresh = Math.abs(Date.now() / 1000 - Number(ts)) < 300; // chống phát lại
  if (!fresh || !crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sig || ""))) {
    res.writeHead(401).end();
    return;
  }
  const event = JSON.parse(raw);
  console.log("Nhận sự kiện", event.type, event.data);
  res.writeHead(204).end();
}).listen(8080);
```

Python dùng thư viện chính thức `standardwebhooks` (`pip install standardwebhooks`):

```python
from standardwebhooks.webhooks import Webhook
wh = Webhook(os.environ["JAYSTUDIO_WEBHOOK_SECRET"])           # whsec_...
event = wh.verify(request_body_bytes, dict(request.headers))     # lỗi nếu chữ ký sai hoặc quá hạn
```

### Đồng bộ bằng polling (không cần webhook)

```bash
curl "http://127.0.0.1:4321/api/events?limit=100"                       # lần đầu
curl "http://127.0.0.1:4321/api/events?since=evt_3f9a...&type=video.*"  # các lần sau
```

Lưu `id` của sự kiện cuối cùng đã xử lý và truyền vào `since` lần sau. App giữ 2.000 sự kiện gần nhất.

## MCP: cho agent AI

Danh sách tool: `brand_list`, `brand_get`, `brand_upsert`, `brand_generate`, `brand_personas`, `brand_documents`,
`brand_document_get`, `brand_cost_report`, `brand_video_submit`, `brand_video_status`, `brand_events`.

```bash
# Claude Code
claude mcp add --transport http jaystudio http://127.0.0.1:4321/mcp
# hoặc không cần chạy web app:
claude mcp add jaystudio -- node /duong-dan/agency-agents/apps/jaystudio/server/mcp-stdio.js
```

Nếu đã đặt token, client MCP gửi header `Authorization: Bearer <token>`. Ví dụ với Claude Code: `--header "Authorization: Bearer ..."`.

## REST: ví dụ cho CRM

```bash
# 1. Tạo/đồng bộ thương hiệu của một khách hàng
curl -X POST http://127.0.0.1:4321/api/brands -H 'content-type: application/json' \
  -d '{"name":"Spa Hoa Sen","kind":"business","industry":"Làm đẹp","audience":"Nữ 25-40, TP.HCM","budget":10000000,"currency":"VND"}'

# 2. Sinh lịch nội dung 30 ngày (mức model tự chọn rẻ nhất đủ tốt)
curl -X POST http://127.0.0.1:4321/api/generate/calendar -H 'content-type: application/json' \
  -d '{"brandId":"brand_xxx","params":{"days":30,"channels":"TikTok, Facebook, Zalo OA"}}'

# 3. Nhận sự kiện document.created qua webhook để tạo task duyệt trong CRM
```

Mọi lỗi trả JSON `{"error": "..."}`:

| Mã | Ý nghĩa |
|---|---|
| 400 | Dữ liệu sai |
| 401 | Thiếu token |
| 402 | Vượt ngân sách AI tháng |
| 404 | Không tìm thấy |
| 500 | Lỗi khác, kể cả chưa có `ANTHROPIC_API_KEY` |

## Mở rộng về sau

- **Thêm loại sự kiện:** gọi `emit("ten.su.kien", data)` trong `server/` và thêm tên vào `EVENT_TYPES` ở `server/events.js`. OpenAPI tự cập nhật theo.
- **Thêm công cụ AI mới:** khai báo MCP server trong `mcp.config.json`. Trợ lý và trang Kết nối nhận ngay.
- **Agent-to-Agent (A2A):** nếu AIOS sau này dùng chuẩn A2A, có thể thêm một agent card trỏ về các endpoint trên mà không phải đổi dữ liệu.
