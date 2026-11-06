// Brand-building workflows. Each one = stable system blocks (persona + brand, prompt-cached)
// + a task prompt, routed to the cheapest tier that holds quality for that task.
import { complete } from "./llm.js";
import { personaPrompt } from "./personas.js";
import { findById, insert, newId } from "./store.js";
import { getSettings } from "./config.js";

const BASE = `Bạn là bộ não chiến lược của Jaystudio Brand OS: một studio xây dựng thương hiệu cá nhân và doanh nghiệp
với mục tiêu ra kết quả tốt nhất trên mỗi đồng chi phí marketing.
Nguyên tắc:
- Ưu tiên kênh và cách làm có chi phí thấp, hiệu quả đo được (organic, nội dung tái sử dụng, cộng đồng, đối tác, UGC) trước quảng cáo trả phí.
- Một nội dung gốc phải được tái chế thành nhiều định dạng (video dài -> Shorts -> bài viết -> carousel -> email).
- Mọi đề xuất phải cụ thể, làm được ngay, có chỉ số đo (KPI) và ước tính chi phí.
- Không bịa số liệu thị trường; nếu là giả định thì ghi rõ "giả định".
- Không dùng nhạc, hình ảnh, nhân vật có bản quyền hay hình người nổi tiếng.
- Trả lời bằng ngôn ngữ của thương hiệu (mặc định tiếng Việt), định dạng Markdown gọn, có tiêu đề và bảng khi phù hợp.`;

export function brandContext(b) {
  if (!b) return "Chưa có hồ sơ thương hiệu. Hãy giả định hợp lý và ghi rõ giả định.";
  const line = (label, v) => (v && String(v).trim() ? `- ${label}: ${Array.isArray(v) ? v.join(", ") : v}` : null);
  return [
    `# HỒ SƠ THƯƠNG HIỆU: ${b.name}`,
    line("Loại", b.kind === "personal" ? "Thương hiệu cá nhân" : "Thương hiệu doanh nghiệp"),
    line("Câu định vị / slogan", b.tagline),
    line("Lĩnh vực", b.industry),
    line("Sản phẩm / dịch vụ", b.offer),
    line("Khách hàng mục tiêu", b.audience),
    line("Nỗi đau / nhu cầu của khách", b.problems),
    line("Điểm khác biệt", b.differentiators),
    line("Giá trị cốt lõi", b.values),
    line("Giọng điệu / tính cách", b.voice),
    line("Đối thủ / hình mẫu", b.competitors),
    line("Kênh đang có", b.channels),
    line("Mục tiêu", b.goals),
    line("Ngân sách marketing / tháng", b.budget ? `${b.budget} ${b.currency || getSettings().currency}` : null),
    line("Màu thương hiệu", b.colors),
    line("Font", b.fonts),
    line("Tài sản sẵn có", b.assets),
    line("Ngôn ngữ nội dung", b.language || "Tiếng Việt"),
    line("Ghi chú", b.notes),
  ]
    .filter(Boolean)
    .join("\n");
}

function systemBlocks(brand, personaId) {
  const blocks = [{ text: BASE }];
  const p = personaPrompt(personaId);
  if (p) blocks.push({ text: `# VAI CHUYÊN GIA: ${p.name}\n${p.prompt}` });
  blocks.push({ text: brandContext(brand), cache: true });
  return blocks;
}

const TASKS = {
  strategy: {
    title: () => "Chiến lược thương hiệu",
    prompt: (p) => `Xây dựng CHIẾN LƯỢC THƯƠNG HIỆU hoàn chỉnh cho hồ sơ trên.${p.focus ? ` Trọng tâm: ${p.focus}.` : ""}
Gồm các phần:
1. Tóm tắt định vị (1 câu định vị + lời hứa thương hiệu)
2. Chân dung khách hàng (2-3 persona: nhu cầu, nỗi đau, nơi họ xem nội dung, rào cản mua)
3. Archetype và giọng điệu (nên / không nên, ví dụ câu mẫu)
4. Thông điệp chính và 4-5 trụ cột nội dung (content pillars) kèm tỉ lệ
5. Định hướng nhận diện hình ảnh (màu, font, phong cách hình/video) - nhất quán với tài sản sẵn có
6. Kênh ưu tiên theo chi phí/hiệu quả: bảng (kênh, vai trò, tần suất, chi phí ước tính, KPI)
7. Phễu: thu hút -> nuôi dưỡng -> chuyển đổi -> giữ chân, với tài sản cụ thể cho từng tầng
8. Lộ trình 90 ngày theo tuần (việc làm, sản phẩm đầu ra, chỉ số)
9. 5 rủi ro và cách giảm thiểu`,
  },
  budget: {
    title: (p) => `Tối ưu ngân sách ${p.amount || ""}`.trim(),
    prompt: (p) => `Lập KẾ HOẠCH NGÂN SÁCH MARKETING tối ưu chi phí.
Ngân sách: ${p.amount || "theo hồ sơ"} ${p.currency || ""} / ${p.period || "tháng"}. Mục tiêu chính: ${p.goal || "theo hồ sơ"}.
Yêu cầu:
- Bảng phân bổ (hạng mục, %, số tiền, lý do, KPI, mức tối thiểu để có tín hiệu)
- Chia rõ: nội dung organic tự làm bằng AI (chi phí công cụ AI), quảng cáo trả phí, KOC/đối tác, công cụ
- Chi phí sản xuất nội dung với Jaystudio (ước tính theo lượt AI: video giải thích ~ dưới 1 USD/video, ảnh 0,01-0,1 USD)
- Quy tắc tăng/giảm ngân sách theo dữ liệu (ví dụ CPA, CTR ngưỡng nào thì dừng/nhân)
- Thử nghiệm A/B ưu tiên trong 30 ngày đầu
- Những thứ KHÔNG nên chi tiền giai đoạn này`,
  },
  calendar: {
    title: (p) => `Lịch nội dung ${p.days || 30} ngày`,
    prompt: (p) => `Lập LỊCH NỘI DUNG ${p.days || 30} ngày cho các kênh: ${p.channels || "các kênh ưu tiên trong hồ sơ"}.
Tần suất: ${p.frequency || "phù hợp nguồn lực 1 người + AI"}.
Xuất một bảng Markdown: Ngày | Kênh | Trụ cột | Định dạng | Tiêu đề / Hook | Ý chính | CTA | Tái chế từ (nếu có).
Áp dụng nguyên tắc "1 nội dung gốc -> nhiều định dạng". Sau bảng: danh sách 5 nội dung gốc cần sản xuất trước và cách tái chế từng cái.`,
  },
  content: {
    title: (p) => `${p.platform || "Nội dung"}: ${(p.topic || "").slice(0, 60)}`,
    prompt: (p) => `Viết ${p.count || 1} nội dung cho kênh ${p.platform || "Facebook"}, định dạng ${p.format || "bài đăng"}.
Chủ đề: ${p.topic || "chọn chủ đề hiệu quả nhất theo trụ cột nội dung"}.
${p.extra ? `Yêu cầu thêm: ${p.extra}\n` : ""}Mỗi nội dung gồm: Hook (3 giây / dòng đầu), thân bài, CTA, hashtag (nếu kênh dùng), gợi ý hình ảnh/video.
Nếu là video ngắn: viết kịch bản theo cảnh (thời lượng, hình ảnh, chữ trên màn hình, lời thoại).
Giữ đúng giọng điệu thương hiệu, độ dài chuẩn của nền tảng.`,
  },
  repurpose: {
    title: () => "Tái chế nội dung",
    prompt: (p) => `Tái chế nội dung gốc dưới đây thành: ${p.targets || "1 kịch bản TikTok/Reels 30-45s, 1 bài Facebook, 1 bài LinkedIn, 1 carousel 7 slide, 1 email ngắn"}.
Giữ thông điệp, đổi cách kể cho từng nền tảng.

NỘI DUNG GỐC:
"""
${p.source || ""}
"""`,
  },
  variants: {
    title: () => "Biến thể A/B",
    prompt: (p) => `Tạo ${p.count || 10} biến thể ${p.kind || "tiêu đề / hook"} để test A/B cho: ${p.topic || ""}.
Phân nhóm theo góc tiếp cận (nỗi đau, lợi ích, tò mò, bằng chứng, khan hiếm). Đánh dấu 3 biến thể nên test trước và lý do.`,
  },
  videoSpec: {
    title: (p) => `Video: ${(p.topic || "").slice(0, 60)}`,
    json: true,
    prompt: (p) => `Viết SPEC JSON cho claude-code-video-toolkit để làm video về: ${p.topic}.
Khung hình: ${p.format || "9:16"}. Thời lượng mục tiêu: ${p.seconds || 45} giây (khoảng 2,4 từ/giây lời dẫn).
Quy tắc: cảnh 1 là hook một câu; cảnh cuối là CTA; 3-6 cảnh; xen kẽ cảnh chuyển động ("ltx") và cảnh dựng ("text" hoặc "ideogram") khoảng 15 giây đổi một lần;
"ltx" chỉ mô tả chuyển động và không khí, không có chữ; "text" có "headline" (dưới 6 từ, VIẾT HOA) và "subline" tùy chọn;
lời dẫn viết đúng như phụ đề sẽ hiện. Ngôn ngữ lời dẫn: ${p.language || "tiếng Việt"}.
Chỉ trả về MỘT khối JSON hợp lệ, không giải thích, theo dạng:
{"title": "...", "format": "${p.format || "9:16"}", "voice": {"provider": "qwen3", "tone": "warm", "maxWpm": 165},
 "scenes": [{"slug": "hook", "text": "...", "visual": {"kind": "ltx", "prompt": "..."}},
            {"slug": "...", "text": "...", "visual": {"kind": "text", "headline": "...", "subline": "..."}}]}`,
  },
};

export const WORKFLOWS = Object.keys(TASKS);

function extractJson(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const raw = fenced ? fenced[1] : text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1);
  return JSON.parse(raw);
}

export async function runWorkflow(name, { brandId, personaId, tier, params = {} }) {
  const task = TASKS[name];
  if (!task) throw new Error(`Không có quy trình "${name}"`);
  const brand = brandId ? findById("brands", brandId) : null;
  if (brandId && !brand) throw new Error("Không tìm thấy thương hiệu");

  const res = await complete({
    task: name,
    tier,
    systemBlocks: systemBlocks(brand, personaId),
    prompt: task.prompt(params),
    maxTokens: name === "strategy" || name === "calendar" ? 32000 : 16000,
  });

  let data = null;
  if (task.json) {
    try {
      data = extractJson(res.text);
    } catch {
      throw new Error("Model không trả về JSON hợp lệ. Thử lại hoặc chọn mức model cao hơn.");
    }
  }

  const doc = insert("documents", {
    id: newId("doc"),
    type: name,
    brandId: brand?.id || null,
    personaId: personaId || null,
    title: task.title(params),
    params,
    content: res.text,
    data,
    model: res.model,
    tier: res.tier,
    costUsd: res.costUsd,
    cached: Boolean(res.cached),
    truncated: Boolean(res.truncated),
    createdAt: new Date().toISOString(),
  });
  return doc;
}
