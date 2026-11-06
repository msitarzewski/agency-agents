# Jaystudio Brand OS

Web app chạy **trên máy bạn** để xây dựng thương hiệu cá nhân và doanh nghiệp với chi phí marketing thấp nhất mà vẫn
ra kết quả tốt. App nối với các công cụ AI qua **MCP** (mcp-video, VibeFrame, Video Toolkit, Pixelle/ComfyUI) và
**Claude API**. Bản thân app cũng là một **MCP server**, nên nó cắm được vào hệ sinh thái AIOS của bạn.

## Chạy

```bash
bash .claude/skills/jaystudio/setup.sh     # lần đầu: cài mcp-video, video toolkit, Pixelle, npm install
cd apps/jaystudio
cp .env.example .env                       # điền ANTHROPIC_API_KEY (+ khóa khác nếu dùng)
npm start                                  # http://127.0.0.1:4321
npm run check                              # smoke test (SMOKE_MCP=1 để thử cả MCP server thật)
```

Cần Node.js 20.12 trở lên. Các MCP server cần `uv`/`uvx`, `npx` và `ffmpeg`.

## Tính năng

| Màn hình | Làm gì |
|---|---|
| Thương hiệu | Hồ sơ cá nhân/doanh nghiệp: sản phẩm, khách hàng, nỗi đau, khác biệt, giọng điệu, kênh, ngân sách, màu/font |
| Studio nội dung | Chiến lược thương hiệu · Ngân sách marketing · Lịch nội dung 30 ngày · Bài viết/kịch bản · Tái chế 1→nhiều · Biến thể A/B. Gán thêm "chuyên gia" (69 persona của repo này: marketing, design, paid-media, sales, product) |
| Thư viện | Mọi kết quả được lưu, xem lại, tải `.md` |
| Video studio | Chủ đề → AI viết spec → **báo giá** → chạy job Video Toolkit (giọng, hình, phụ đề, nhạc, QC) → MP4 |
| Trợ lý AI | Claude điều khiển các tool MCP (cắt, ghép, phụ đề, Shorts, sinh video...). Tool tốn phí **phải được bạn duyệt** |
| Kết nối MCP / API | Trạng thái server, danh sách tool (đánh dấu miễn phí/tốn phí), chạy thử tool, khóa API nào đã có |
| Chi phí & cài đặt | Chi tiêu tháng, tiền đã tiết kiệm, ngân sách trần, mức model cho từng tác vụ |

## Tối ưu chi phí: cách app tiết kiệm

1. **Cache câu trả lời**: yêu cầu giống hệt thì trả lại kết quả cũ, $0.
2. **Chạy local miễn phí**: nếu bật [Ollama](https://ollama.com), các tác vụ mức "Tiết kiệm" chạy trên máy, $0.
3. **Prompt caching**: persona và hồ sơ thương hiệu được Claude cache, các lần sau đọc với giá khoảng 1/10.
4. **Định tuyến theo tác vụ**:

   | Mức | Dùng cho |
   |---|---|
   | Opus 5.5 | Chiến lược và ngân sách: làm ít lần, cần chất lượng cao |
   | Sonnet 5.5 | Bài viết, lịch nội dung, spec video, trợ lý |
   | Haiku 5.5 | Tái chế nội dung, biến thể A/B |

   Đổi mức cho từng tác vụ trong Cài đặt hoặc ngay trên từng yêu cầu.
5. **Ngân sách trần / tháng**: yêu cầu nào làm vượt ngân sách sẽ bị chặn (HTTP 402) trước khi gọi API.
6. **Duyệt trước khi tiêu tiền**: video job luôn báo giá trước. Trợ lý dừng lại hỏi trước khi gọi tool sinh AI trả phí.
7. **Ưu tiên công cụ local**: mcp-video và các tool FFmpeg của VibeFrame chạy miễn phí, trợ lý được dặn dùng chúng trước.

Giá tham khảo (USD / 1 triệu token, vào/ra):

| Model | Giá vào | Giá ra |
|---|---|---|
| Haiku 5.5 | 0,10 | 0,50 |
| Sonnet 5.5 | 2 | 10 |
| Opus 5.5 | 4 | 20 |

Opus và Sonnet bật sẵn `fallbacks: "default"`: khi một yêu cầu bị chặn vì an toàn, nó được tự động chạy lại trên model dự phòng.

## Tích hợp AIOS

Jaystudio vừa là **client** (gọi tool video/AI), vừa là **server** cho các thành phần khác. Hướng dẫn đầy đủ cho đội
kỹ thuật xem ở [docs/AIOS-INTEGRATION.md](docs/AIOS-INTEGRATION.md).

| Kênh | Chuẩn | Địa chỉ |
|---|---|---|
| Agent AI | MCP | `http://127.0.0.1:4321/mcp` (Streamable HTTP) hoặc `node apps/jaystudio/server/mcp-stdio.js` (có sẵn trong `.mcp.json` của repo) |
| Phần mềm / CRM / n8n | REST + OpenAPI 3.1 | `/api/...`, đặc tả ở `GET /api/openapi.json` |
| Thông báo đẩy | Standard Webhooks | đăng ký ở trang Kết nối hoặc `POST /api/webhooks` |
| Đồng bộ kéo | Event feed | `GET /api/events?since=<id>` |

Sự kiện: `brand.*`, `document.created`, `video.job.submitted|completed|failed`, `budget.warning`, `budget.exceeded`, `aios.sync.*`.

**Connector AIOS Brand OS** (repo AIOS-CRM, thư mục `brand-os/`): nhập/đồng bộ thương hiệu, gửi tài liệu thành bản nháp
có version, gửi lead (không trùng) và video MP4 sang AIOS; tùy chọn tự gửi. Cấu hình `AIOS_BRANDOS_*` trong `.env`,
kiểm thử bằng `npm run test:aios`.

Tool MCP mà app cung cấp: `brand_list`, `brand_get`, `brand_upsert`, `brand_generate`, `brand_personas`,
`brand_documents`, `brand_document_get`, `brand_cost_report`, `brand_video_submit`, `brand_video_status`, `brand_events`.

Ví dụ gọi REST:

```bash
curl -X POST http://127.0.0.1:4321/api/generate/content \
  -H 'content-type: application/json' \
  -d '{"brandId":"brand_xxx","tier":"auto","params":{"platform":"TikTok","topic":"3 sai lầm khi pha cà phê"}}'
```

**Bảo mật:**
- App chỉ nghe ở `127.0.0.1`, chặn request khác origin và chặn host lạ (chống DNS rebinding).
- Muốn cho service AIOS khác gọi vào: đặt `JAYSTUDIO_API_TOKEN` rồi gửi kèm header `Authorization: Bearer <token>`. Nếu mở ra mạng LAN (`JAYSTUDIO_HOST=0.0.0.0`) thì bắt buộc đặt token.

## Thêm hoặc đổi MCP server

Sửa `apps/jaystudio/mcp.config.json` (cùng định dạng `.mcp.json`):

```json
{ "mcpServers": { "ten-server": { "type": "stdio", "command": "npx", "args": ["-y", "goi-mcp"] },
                  "server-http": { "type": "http", "url": "http://localhost:9000/mcp" } } }
```

Tool có tên khớp quy tắc tốn phí trong `server/mcp-hub.js` (`generate_*`, `remix_*`, `video_submit`...) sẽ cần duyệt
trong Trợ lý. Mọi tool của server `pixelle` cũng cần duyệt.

## Cấu trúc

```
server/
  index.js        HTTP server: web, REST, /mcp
  llm.js          bộ định tuyến model theo chi phí (Claude SDK + Ollama), cache, budget guard
  costs.js        bảng giá, sổ chi phí, ngân sách
  mcp-hub.js      MCP client tới các server video/AI
  workflows.js    quy trình thương hiệu (prompt, persona, hồ sơ)
  assistant.js    trợ lý có tool MCP, duyệt tool tốn phí
  video.js        Video studio qua video-toolkit
  aios-mcp.js     Jaystudio như một MCP server
  events.js       nhật ký sự kiện + webhook ký theo Standard Webhooks
  openapi.js      đặc tả OpenAPI 3.1 (GET /api/openapi.json)
  personas.js     nạp persona từ các thư mục agent của repo
public/           giao diện (HTML/CSS/JS thuần, không cần build)
data/             dữ liệu local (gitignored): thương hiệu, tài liệu, sổ chi phí, cache
```
