import { marked } from "/vendor/marked.esm.js";

// ---------- helpers ----------
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// Never render raw HTML coming from model output.
marked.use({ renderer: { html: (t) => esc(t.text ?? t) } });
const md = (s) => marked.parse(s || "");
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const usd = (n) => `$${(n || 0).toFixed(n < 0.01 && n > 0 ? 4 : 3)}`;
const main = $("#main");

async function api(path, opts = {}) {
  const r = await fetch(`/api${path}`, {
    method: opts.method || (opts.body ? "POST" : "GET"),
    headers: { "content-type": "application/json" },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `Lỗi ${r.status}`);
  return data;
}

function toast(msg, isErr = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast" + (isErr ? " err" : "");
  t.hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => (t.hidden = true), isErr ? 7000 : 3000);
}

async function busy(btn, fn) {
  const label = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Đang chạy...";
  try {
    return await fn();
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = label;
  }
}

const state = { brands: [], personas: [], activeBrand: localStorage.getItem("activeBrand") || "" };
const tierOptions = (sel = "auto") =>
  [["auto", "Tự động (rẻ nhất đủ tốt)"], ["local", "Local Ollama ($0)"], ["eco", "Tiết kiệm - Haiku"], ["balanced", "Cân bằng - Sonnet"], ["premium", "Cao cấp - Opus"]]
    .map(([v, l]) => `<option value="${v}" ${v === sel ? "selected" : ""}>${l}</option>`)
    .join("");

async function loadBrands() {
  state.brands = await api("/brands");
  const sel = $("#activeBrand");
  sel.innerHTML = `<option value="">(chưa chọn)</option>` + state.brands.map((b) => `<option value="${b.id}">${esc(b.name)}</option>`).join("");
  if (!state.brands.find((b) => b.id === state.activeBrand)) state.activeBrand = state.brands[0]?.id || "";
  sel.value = state.activeBrand;
}
$("#activeBrand").addEventListener("change", (e) => {
  state.activeBrand = e.target.value;
  localStorage.setItem("activeBrand", state.activeBrand);
  route();
});

// ---------- views ----------
const views = {};

views.dashboard = async () => {
  const s = await api("/status");
  const c = s.costs;
  const pct = c.budgetUsd ? Math.min(100, (c.spentUsd / c.budgetUsd) * 100) : 0;
  main.innerHTML = `
    <h1>Tổng quan</h1>
    <p class="sub">Xưởng thương hiệu chạy trên máy của bạn. Mục tiêu: kết quả tốt nhất trên mỗi đồng chi phí.</p>
    <div class="grid">
      <div class="card"><h3>Chi phí AI tháng ${esc(c.month)}</h3><div class="stat">${usd(c.spentUsd)}</div>
        <div class="muted">/ ngân sách $${c.budgetUsd} (${pct.toFixed(0)}%) · ${c.calls} lượt gọi</div></div>
      <div class="card"><h3>Đã tiết kiệm</h3><div class="stat">${usd(c.savedUsd)}</div><div class="muted">nhờ cache câu trả lời và chạy local</div></div>
      <div class="card"><h3>Claude API</h3><div>${s.anthropic ? '<span class="pill ok">Đã cấu hình</span>' : '<span class="pill err">Chưa có ANTHROPIC_API_KEY</span>'}</div>
        <div class="muted">Ollama: ${s.ollama.ok ? `<span class="pill ok">chạy</span> ${esc(s.ollama.models.join(", "))}` : '<span class="pill">tắt</span> (tùy chọn, $0)'}</div></div>
      <div class="card"><h3>Dữ liệu</h3><div>${s.counts.brands} thương hiệu · ${s.counts.documents} tài liệu · ${s.counts.videos} video</div></div>
    </div>
    <h2>Công cụ AI (MCP)</h2>
    <div class="grid">${s.mcp
      .map((m) => `<div class="card"><h3>${esc(m.label)} ${pill(m.status)}</h3><div class="muted">${esc(m.role)}</div></div>`)
      .join("")}</div>
    <h2>Bắt đầu nhanh</h2>
    <ol>
      <li>Tạo hồ sơ <a href="#brands">Thương hiệu</a> (cá nhân hoặc doanh nghiệp).</li>
      <li>Vào <a href="#studio">Studio nội dung</a> → <b>Chiến lược</b> → rồi <b>Ngân sách</b> và <b>Lịch nội dung</b>.</li>
      <li>Viết bài hằng ngày bằng mức <b>Cân bằng</b>, tái chế bằng mức <b>Tiết kiệm</b>.</li>
      <li>Làm video ngắn ở <a href="#video">Video studio</a> (báo giá trước khi chạy).</li>
    </ol>`;
};

const pill = (st) =>
  st === "connected" ? '<span class="pill ok">đã kết nối</span>' : st === "error" ? '<span class="pill err">lỗi</span>' : st === "connecting" ? '<span class="pill warn">đang nối</span>' : '<span class="pill">chưa nối</span>';

const BRAND_FORM = [
  ["name", "Tên thương hiệu *"],
  ["tagline", "Câu định vị / slogan"],
  ["industry", "Lĩnh vực"],
  ["offer", "Sản phẩm / dịch vụ", true],
  ["audience", "Khách hàng mục tiêu", true],
  ["problems", "Nỗi đau / nhu cầu của khách", true],
  ["differentiators", "Điểm khác biệt", true],
  ["values", "Giá trị cốt lõi"],
  ["voice", "Giọng điệu / tính cách"],
  ["competitors", "Đối thủ / hình mẫu"],
  ["channels", "Kênh (phân cách bằng dấu phẩy)"],
  ["goals", "Mục tiêu 3-6 tháng", true],
  ["budget", "Ngân sách marketing / tháng (số)"],
  ["currency", "Tiền tệ (VND, USD...)"],
  ["colors", "Màu thương hiệu (mã HEX)"],
  ["fonts", "Font"],
  ["assets", "Tài sản sẵn có (logo, ảnh, video, website...)", true],
  ["language", "Ngôn ngữ nội dung"],
  ["notes", "Ghi chú", true],
];

views.brands = async () => {
  await loadBrands();
  const editing = state.brands.find((b) => b.id === state.editBrand) || null;
  const b = editing || { kind: "business", currency: "VND", language: "Tiếng Việt" };
  main.innerHTML = `
    <h1>Thương hiệu</h1><p class="sub">Hồ sơ càng cụ thể, kết quả AI càng sát. Hồ sơ được cache nên không tốn thêm tiền mỗi lần dùng.</p>
    <div class="split">
      <div class="card">
        <h3>Danh sách</h3>
        <table class="list">${state.brands
          .map((x) => `<tr><td><b>${esc(x.name)}</b><br><span class="muted">${x.kind === "personal" ? "Cá nhân" : "Doanh nghiệp"} · ${esc(x.industry || "")}</span></td>
            <td><button data-edit="${x.id}">Sửa</button></td></tr>`)
          .join("") || '<tr><td class="muted">Chưa có thương hiệu nào.</td></tr>'}</table>
        <p><button id="newBrand">+ Thương hiệu mới</button></p>
      </div>
      <form class="card" id="brandForm">
        <h3>${editing ? "Sửa: " + esc(editing.name) : "Thương hiệu mới"}</h3>
        <label>Loại</label>
        <select name="kind"><option value="business" ${b.kind !== "personal" ? "selected" : ""}>Doanh nghiệp</option><option value="personal" ${b.kind === "personal" ? "selected" : ""}>Cá nhân</option></select>
        ${BRAND_FORM.map(([k, l, area]) => {
          const v = Array.isArray(b[k]) ? b[k].join(", ") : b[k] ?? "";
          return `<label>${l}</label>${area ? `<textarea name="${k}">${esc(v)}</textarea>` : `<input name="${k}" value="${esc(v)}">`}`;
        }).join("")}
        <p class="row"><button class="primary" type="submit">Lưu</button>${editing ? '<button type="button" class="danger" id="delBrand">Xóa</button>' : ""}</p>
      </form>
    </div>`;
  $$("[data-edit]").forEach((el) => (el.onclick = () => ((state.editBrand = el.dataset.edit), views.brands())));
  $("#newBrand").onclick = () => ((state.editBrand = null), views.brands());
  $("#brandForm").onsubmit = async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    try {
      const saved = editing ? await api(`/brands/${editing.id}`, { method: "PUT", body: data }) : await api("/brands", { body: data });
      state.editBrand = saved.id;
      state.activeBrand = saved.id;
      localStorage.setItem("activeBrand", saved.id);
      toast("Đã lưu thương hiệu");
      views.brands();
    } catch (err) {
      toast(err.message, true);
    }
  };
  if (editing)
    $("#delBrand").onclick = async () => {
      if (!confirm(`Xóa thương hiệu "${editing.name}"?`)) return;
      await api(`/brands/${editing.id}`, { method: "DELETE" });
      state.editBrand = null;
      views.brands();
    };
};

// Workflow forms in the content studio.
const WF = {
  strategy: { label: "Chiến lược", hint: "Định vị, persona, giọng điệu, trụ cột nội dung, kênh, lộ trình 90 ngày. Mặc định mức Cao cấp (chạy 1 lần, giá trị lâu dài).", fields: [["focus", "Trọng tâm (tùy chọn)"]], persona: "design/design-brand-guardian" },
  budget: { label: "Ngân sách", hint: "Phân bổ ngân sách marketing để ra kết quả nhiều nhất trên mỗi đồng.", fields: [["amount", "Số tiền"], ["currency", "Tiền tệ"], ["period", "Chu kỳ (tháng/quý)"], ["goal", "Mục tiêu chính"]], persona: "marketing/marketing-growth-hacker" },
  calendar: { label: "Lịch nội dung", hint: "Lịch đăng theo ngày, áp dụng 1 nội dung gốc → nhiều định dạng.", fields: [["days", "Số ngày", "30"], ["channels", "Kênh"], ["frequency", "Tần suất"]], persona: "marketing/marketing-social-media-strategist" },
  content: { label: "Bài viết / kịch bản", hint: "Bài đăng, kịch bản video ngắn, email theo đúng giọng thương hiệu.", fields: [["platform", "Kênh", "Facebook"], ["format", "Định dạng", "bài đăng"], ["topic", "Chủ đề", "", true], ["count", "Số lượng", "1"], ["extra", "Yêu cầu thêm", "", true]], persona: "marketing/marketing-content-creator" },
  repurpose: { label: "Tái chế", hint: "Biến 1 nội dung thành nhiều định dạng. Mặc định mức Tiết kiệm.", fields: [["source", "Nội dung gốc", "", true], ["targets", "Định dạng đích"]] },
  variants: { label: "Biến thể A/B", hint: "Nhiều tiêu đề/hook để test, mặc định mức Tiết kiệm.", fields: [["topic", "Cho nội dung / sản phẩm"], ["kind", "Loại", "tiêu đề / hook"], ["count", "Số lượng", "10"]] },
};

views.studio = async () => {
  state.personas.length || (state.personas = await api("/personas"));
  const wf = state.wf || "strategy";
  const def = WF[wf];
  const brand = state.brands.find((b) => b.id === state.activeBrand);
  main.innerHTML = `
    <h1>Studio nội dung</h1><p class="sub">Thương hiệu: <b>${esc(brand?.name || "chưa chọn - chọn ở thanh bên")}</b></p>
    <div class="tabs">${Object.entries(WF).map(([k, v]) => `<button data-wf="${k}" class="${k === wf ? "active" : ""}">${v.label}</button>`).join("")}</div>
    <div class="split">
      <form class="card" id="wfForm">
        <p class="muted">${def.hint}</p>
        ${def.fields.map(([k, l, d, area]) => `<label>${l}</label>${area ? `<textarea name="${k}">${esc(d || "")}</textarea>` : `<input name="${k}" value="${esc(d || "")}">`}`).join("")}
        <label>Chuyên gia (persona từ The Agency)</label>
        <select name="personaId"><option value="">(không dùng)</option>${state.personas
          .map((p) => `<option value="${p.id}" ${p.id === def.persona ? "selected" : ""}>${esc(p.emoji)} ${esc(p.name)} · ${p.division}</option>`)
          .join("")}</select>
        <label>Mức model</label><select name="tier">${tierOptions()}</select>
        <p><button class="primary" type="submit">Tạo</button></p>
      </form>
      <div><div class="row" id="outMeta"></div><div class="output" id="out"><p class="muted">Kết quả hiển thị ở đây và được lưu vào Thư viện.</p></div></div>
    </div>`;
  $$("[data-wf]").forEach((b) => (b.onclick = () => ((state.wf = b.dataset.wf), views.studio())));
  $("#wfForm").onsubmit = (e) => {
    e.preventDefault();
    const fd = Object.fromEntries(new FormData(e.target));
    const { personaId, tier, ...params } = fd;
    busy(e.submitter, async () => {
      const doc = await api(`/generate/${wf}`, { body: { brandId: state.activeBrand || undefined, personaId: personaId || undefined, tier, params } });
      showDoc(doc, $("#out"), $("#outMeta"));
    });
  };
};

function showDoc(doc, out, meta) {
  out.innerHTML = md(doc.content);
  meta.innerHTML = `<span class="pill">${esc(doc.model)}</span><span class="pill">${doc.cached ? "từ cache · $0" : usd(doc.costUsd)}</span>
    ${doc.truncated ? '<span class="pill warn">bị cắt do giới hạn độ dài</span>' : ""}
    <button id="copyDoc">Sao chép</button><button id="dlDoc">Tải .md</button>`;
  $("#copyDoc").onclick = () => navigator.clipboard.writeText(doc.content).then(() => toast("Đã sao chép"));
  $("#dlDoc").onclick = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([doc.content], { type: "text/markdown" }));
    a.download = `${doc.title.replace(/[^\p{L}\p{N}]+/gu, "-")}.md`;
    a.click();
  };
}

views.library = async () => {
  const q = state.activeBrand ? `?brandId=${state.activeBrand}` : "";
  const docs = await api(`/documents${q}`);
  main.innerHTML = `<h1>Thư viện</h1><p class="sub">Mọi kết quả đã tạo cho thương hiệu đang chọn.</p>
    <div class="split"><div class="card"><table class="list">${docs
      .map((d) => `<tr><td><a href="#" data-doc="${d.id}">${esc(d.title)}</a><br><span class="muted">${esc(WF[d.type]?.label || d.type)} · ${new Date(d.createdAt).toLocaleString("vi-VN")} · ${usd(d.costUsd)}</span></td></tr>`)
      .join("") || '<tr><td class="muted">Chưa có tài liệu.</td></tr>'}</table></div>
    <div><div class="row" id="outMeta"></div><div class="output" id="out"><p class="muted">Chọn một tài liệu.</p></div></div></div>`;
  $$("[data-doc]").forEach(
    (a) =>
      (a.onclick = async (e) => {
        e.preventDefault();
        const doc = await api(`/documents/${a.dataset.doc}`);
        showDoc(doc, $("#out"), $("#outMeta"));
        $("#outMeta").insertAdjacentHTML("beforeend", '<button class="danger" id="rmDoc">Xóa</button>');
        $("#rmDoc").onclick = async () => (await api(`/documents/${doc.id}`, { method: "DELETE" }), views.library());
      })
  );
};

views.video = async () => {
  main.innerHTML = `<h1>Video studio</h1>
    <p class="sub">Chủ đề → AI viết spec theo thương hiệu → <b>báo giá</b> → chạy job (giọng, hình, phụ đề, nhạc, QC) qua Video Toolkit.</p>
    <div class="split">
      <form class="card" id="specForm">
        <label>Chủ đề video</label><textarea name="topic" placeholder="Ví dụ: 3 sai lầm khi chọn mỹ phẩm cho da dầu"></textarea>
        <div class="row"><div style="flex:1"><label>Khung hình</label><select name="format"><option>9:16</option><option>16:9</option></select></div>
        <div style="flex:1"><label>Giây</label><input name="seconds" value="45"></div></div>
        <label>Mức model viết spec</label><select name="tier">${tierOptions()}</select>
        <p><button class="primary" type="submit">1. Viết spec</button></p>
        <label>Trần chi phí / video (USD)</label><input id="maxUsd" value="2">
      </form>
      <div class="card">
        <label>Spec JSON (sửa được)</label><textarea class="code" id="spec">{}</textarea>
        <p class="row"><button id="estBtn">2. Báo giá</button><button class="primary" id="subBtn">3. Chạy job</button></p>
        <div id="est" class="muted"></div>
      </div>
    </div>
    <h2>Job video</h2><div class="card" id="jobs">Đang tải...</div>`;
  const specBox = $("#spec");
  const getSpec = () => JSON.parse(specBox.value);
  $("#specForm").onsubmit = (e) => {
    e.preventDefault();
    const { tier, ...params } = Object.fromEntries(new FormData(e.target));
    busy(e.submitter, async () => {
      const doc = await api("/generate/videoSpec", { body: { brandId: state.activeBrand || undefined, tier, params } });
      specBox.value = JSON.stringify(doc.data, null, 2);
      toast(`Đã viết spec (${doc.cached ? "cache" : usd(doc.costUsd)})`);
    });
  };
  $("#estBtn").onclick = (e) =>
    busy(e.target, async () => {
      const r = await api("/video/estimate", { body: { spec: getSpec() } });
      $("#est").innerHTML = `<pre>${esc(JSON.stringify(r, null, 2))}</pre>`;
    });
  $("#subBtn").onclick = (e) =>
    busy(e.target, async () => {
      if (!confirm("Chạy job này sẽ tốn phí theo báo giá. Tiếp tục?")) return;
      const r = await api("/video/submit", { body: { spec: getSpec(), maxUsd: Number($("#maxUsd").value) || 2, brandId: state.activeBrand || undefined } });
      toast(`Đã gửi job ${r.jobId}`);
      loadJobs();
    });
  loadJobs();
};

async function loadJobs() {
  const box = $("#jobs");
  if (!box) return;
  const jobs = await api("/video/jobs").catch(() => []);
  box.innerHTML = jobs.length
    ? `<table class="list">${jobs
        .map((j) => `<tr><td><b>${esc(j.title)}</b><br><span class="muted">${esc(j.id)}</span></td><td>${esc(j.status)}</td>
          <td>${j.result ? `<code>${esc(j.result.path || j.result.mp4 || j.result.url || "")}</code>` : ""}</td>
          <td><button data-st="${esc(j.id)}">Cập nhật</button></td></tr>`)
        .join("")}</table>`
    : '<span class="muted">Chưa có job.</span>';
  $$("[data-st]").forEach(
    (b) =>
      (b.onclick = () =>
        busy(b, async () => {
          const s = await api(`/video/${encodeURIComponent(b.dataset.st)}/status`);
          if ((s.phase || s.status) === "done") await api(`/video/${encodeURIComponent(b.dataset.st)}/result`);
          toast(`Trạng thái: ${s.phase || s.status}`);
          loadJobs();
        }))
  );
}

views.assistant = async () => {
  const servers = await api("/mcp/servers");
  const settings = (await api("/settings")).settings;
  const chosen = state.chatServers || settings.assistantServers;
  main.innerHTML = `<h1>Trợ lý AI</h1>
    <p class="sub">Claude điều khiển các công cụ MCP (cắt, ghép, phụ đề, sinh video...). Tool tốn phí sẽ chờ bạn duyệt.</p>
    <div class="card checks">Công cụ: ${servers
      .map((s) => `<label><input type="checkbox" value="${s.name}" ${chosen.includes(s.name) ? "checked" : ""}> ${esc(s.label)}</label>`)
      .join("")}
      <span class="muted">(bật ít server = rẻ hơn: mô tả tool cũng tính token)</span>
      <div class="row" style="margin-top:8px"><select id="chatTier" style="width:auto">${tierOptions(state.chatTier || "auto")}</select>
      <button id="newChat">Phiên mới</button><span id="chatCost" class="muted"></span></div></div>
    <div class="chat" id="chat" style="margin:16px 0"></div>
    <form id="chatForm" class="row"><textarea name="m" style="flex:1;min-height:60px" placeholder="Ví dụ: Lấy thông tin video /home/me/clip.mp4 rồi cắt 30 giây đầu thành bản dọc 9:16 có phụ đề"></textarea><button class="primary">Gửi</button></form>`;
  $$(".checks input[type=checkbox]").forEach((c) => (c.onchange = () => (state.chatServers = $$(".checks input[type=checkbox]:checked").map((x) => x.value))));
  $("#chatTier").onchange = (e) => (state.chatTier = e.target.value);
  $("#newChat").onclick = () => ((state.chat = null), renderChat());
  $("#chatForm").onsubmit = (e) => {
    e.preventDefault();
    const m = e.target.m.value.trim();
    if (!m) return;
    busy(e.submitter, async () => {
      state.chat = await api("/assistant", {
        body: { sessionId: state.chat?.id, message: m, brandId: state.activeBrand || null, servers: state.chatServers || chosen, tier: state.chatTier || "auto" },
      });
      e.target.m.value = "";
      renderChat();
    });
  };
  renderChat();
};

function renderChat() {
  const box = $("#chat");
  const c = state.chat;
  if (!c) return (box.innerHTML = '<p class="muted">Bắt đầu bằng một yêu cầu.</p>');
  $("#chatCost").textContent = `Phiên: ${usd(c.costUsd)} · ${c.lastModel || ""}`;
  box.innerHTML =
    c.items
      .map((it) =>
        it.kind === "text"
          ? `<div class="msg ${it.role}">${it.role === "user" ? esc(it.text) : md(it.text)}</div>`
          : it.kind === "tool_use"
          ? `<div class="msg tool">→ ${esc(it.name)} ${esc(JSON.stringify(it.input))}</div>`
          : `<div class="msg tool">${it.error ? "✗" : "✓"} ${esc(it.text)}</div>`
      )
      .join("") +
    (c.notice ? `<div class="msg assistant">${esc(c.notice)}</div>` : "") +
    (c.toolErrors?.length ? `<div class="msg tool">Không nối được: ${esc(c.toolErrors.join(" | "))}</div>` : "") +
    (c.pending.length
      ? `<div class="card pending"><h3>Cần bạn duyệt</h3>${c.pending
          .map((p) => `<div class="checks"><label><input type="checkbox" data-ap="${p.id}" ${p.paid ? "" : "checked disabled"}> <b>${esc(p.name)}</b> ${p.paid ? '<span class="pill warn">tốn phí</span>' : '<span class="pill">miễn phí</span>'}</label>
              <pre class="msg tool">${esc(JSON.stringify(p.input, null, 2))}</pre></div>`)
          .join("")}<button class="primary" id="apBtn">Xác nhận</button></div>`
      : "");
  if (c.pending.length)
    $("#apBtn").onclick = (e) =>
      busy(e.target, async () => {
        const decisions = Object.fromEntries($$("[data-ap]").map((x) => [x.dataset.ap, x.checked]));
        state.chat = await api("/assistant/approve", { body: { sessionId: c.id, decisions } });
        renderChat();
      });
}

views.integrations = async () => {
  const s = await api("/status");
  const man = await api("/manifest");
  main.innerHTML = `<h1>Kết nối MCP / API</h1>
    <p class="sub">Server MCP lấy từ <code>apps/jaystudio/mcp.config.json</code> (hoặc <code>.mcp.json</code> của repo). Khóa API đặt trong <code>apps/jaystudio/.env</code>.</p>
    <h2>MCP server</h2>
    <table class="list card">${s.mcp
      .map((m) => `<tr><td><b>${esc(m.label)}</b> ${pill(m.status)}<br><span class="muted">${esc(m.role)}</span>${m.error ? `<br><span class="pill err">${esc(m.error)}</span>` : ""}</td>
        <td><code>${esc(m.target)}</code></td><td>${m.toolCount || ""} tool</td>
        <td class="row"><button data-conn="${m.name}">Kết nối</button><button data-tools="${m.name}">Xem tool</button></td></tr>`)
      .join("")}</table>
    <div id="toolBox"></div>
    <h2>Khóa API</h2>
    <table class="list card">${s.keys.map((k) => `<tr><td><code>${k.env}</code></td><td>${k.set ? '<span class="pill ok">có</span>' : '<span class="pill">chưa</span>'}</td><td class="muted">${esc(k.use)}</td></tr>`).join("")}</table>
    <h2>Tích hợp AIOS</h2>
    <div class="card"><p>Jaystudio vừa là <b>client</b> (gọi các tool video/AI) vừa là <b>server</b> để các agent khác trong AIOS dùng:</p>
      <ul><li><b>Agent AI</b> (Claude, trợ lý khác) → MCP HTTP: <code>${location.origin}/mcp</code> hoặc stdio: <code>node apps/jaystudio/server/mcp-stdio.js</code></li>
      <li><b>Phần mềm / CRM / n8n / Zapier</b> → REST, mô tả chuẩn OpenAPI: <code>${location.origin}/api/openapi.json</code></li>
      <li><b>Nhận thông báo tự động</b> → Webhook (bên dưới) hoặc đọc <code>${location.origin}/api/events?since=&lt;id&gt;</code></li></ul>
      <details><summary>Danh sách route</summary><pre>${esc(JSON.stringify(man.routes, null, 2))}</pre></details></div>
    <h2>Webhook (gửi sự kiện sang hệ thống khác)</h2>
    <div class="card">
      <p class="muted">Mỗi khi có sự kiện, Jaystudio gửi POST JSON có chữ ký theo chuẩn Standard Webhooks tới URL bạn đăng ký. Bên nhận dùng <code>secret</code> để kiểm chữ ký.</p>
      <form id="whForm" class="row"><input name="url" style="flex:2" placeholder="https://crm.cua-ban/webhooks/jaystudio">
        <input name="events" style="flex:1" value="*" title="Ví dụ: document.created, video.*"><button class="primary">Đăng ký</button></form>
      <p class="muted">Loại sự kiện: ${man.eventTypes.map((t) => `<code>${t}</code>`).join(" ")}</p>
      <div id="whSecret"></div><div id="whList"></div>
    </div>
    <h2>Sự kiện gần đây</h2><div class="card" id="evList"></div>`;
  loadHooks();
  $$("[data-conn]").forEach((b) => (b.onclick = () => busy(b, async () => (await api(`/mcp/servers/${b.dataset.conn}/connect`, { method: "POST" }), views.integrations()))));
  $$("[data-tools]").forEach(
    (b) =>
      (b.onclick = () =>
        busy(b, async () => {
          const tools = await api(`/mcp/servers/${b.dataset.tools}/tools`);
          $("#toolBox").innerHTML = `<h2>Tool của ${esc(b.dataset.tools)} (${tools.length})</h2>
            <div class="card"><table class="list">${tools.map((t) => `<tr><td><code>${esc(t.name)}</code> ${t.paid ? '<span class="pill warn">tốn phí</span>' : '<span class="pill ok">miễn phí/local</span>'}</td><td class="muted">${esc((t.description || "").slice(0, 160))}</td></tr>`).join("")}</table>
            <h3>Thử gọi tool</h3><div class="row"><select id="tName" style="width:auto">${tools.map((t) => `<option>${esc(t.name)}</option>`).join("")}</select>
            <input id="tArgs" style="flex:1" value="{}"><button id="tRun">Chạy</button></div><pre id="tOut" class="msg tool"></pre></div>`;
          $("#tRun").onclick = (e) =>
            busy(e.target, async () => {
              const r = await api("/mcp/call", { body: { server: b.dataset.tools, tool: $("#tName").value, args: JSON.parse($("#tArgs").value || "{}") } });
              $("#tOut").textContent = (r.content || []).map((c) => c.text || `[${c.type}]`).join("\n");
            });
        }))
  );
};

async function loadHooks() {
  const [hooks, events] = await Promise.all([api("/webhooks"), api("/events?limit=20")]);
  $("#whList").innerHTML = hooks.length
    ? `<table class="list">${hooks
        .map((h) => `<tr><td><code>${esc(h.url)}</code><br><span class="muted">${esc(h.events.join(", "))}</span></td>
          <td>${h.lastStatus ? (h.lastStatus < 300 ? `<span class="pill ok">${h.lastStatus}</span>` : `<span class="pill err">${h.lastStatus}</span>`) : h.lastError ? `<span class="pill err">${esc(h.lastError)}</span>` : '<span class="pill">chưa gửi</span>'}</td>
          <td class="row"><button data-wtest="${h.id}">Gửi thử</button><button class="danger" data-wdel="${h.id}">Xóa</button></td></tr>`)
        .join("")}</table>`
    : '<span class="muted">Chưa có webhook.</span>';
  $("#evList").innerHTML = events.length
    ? `<table class="list">${events
        .reverse()
        .map((e) => `<tr><td>${new Date(e.timestamp).toLocaleString("vi-VN")}</td><td><code>${esc(e.type)}</code></td><td class="muted">${esc(e.data?.title || e.data?.name || e.data?.jobId || e.data?.id || "")}</td></tr>`)
        .join("")}</table>`
    : '<span class="muted">Chưa có sự kiện.</span>';
  $$("[data-wtest]").forEach(
    (b) =>
      (b.onclick = () =>
        busy(b, async () => {
          const r = await api(`/webhooks/${b.dataset.wtest}/test`, { method: "POST" });
          toast(r.status ? `Phản hồi HTTP ${r.status}` : `Lỗi: ${r.error}`, !r.status || r.status >= 300);
          loadHooks();
        }))
  );
  $$("[data-wdel]").forEach((b) => (b.onclick = async () => (await api(`/webhooks/${b.dataset.wdel}`, { method: "DELETE" }), loadHooks())));
  $("#whForm").onsubmit = (e) => {
    e.preventDefault();
    busy(e.submitter, async () => {
      const h = await api("/webhooks", { body: { url: e.target.url.value, events: e.target.events.value } });
      $("#whSecret").innerHTML = `<p class="pill warn">Lưu secret này ngay, nó chỉ hiện một lần:</p><pre>${esc(h.secret)}</pre>`;
      e.target.url.value = "";
      loadHooks();
    });
  };
}

views.costs = async () => {
  const [c, st] = await Promise.all([api("/costs"), api("/settings")]);
  const s = st.settings;
  const tasks = Object.keys(st.taskTier);
  main.innerHTML = `<h1>Chi phí &amp; cài đặt</h1>
    <div class="grid">
      <div class="card"><h3>Đã chi tháng ${esc(c.month)}</h3><div class="stat">${usd(c.spentUsd)}</div><div class="muted">/ $${c.budgetUsd}</div></div>
      <div class="card"><h3>Tiết kiệm</h3><div class="stat">${usd(c.savedUsd)}</div></div>
      <div class="card"><h3>Theo mức</h3>${Object.entries(c.byTier).map(([k, v]) => `<div>${esc(k)}: ${usd(v)}</div>`).join("") || "-"}</div>
      <div class="card"><h3>Theo tác vụ</h3>${Object.entries(c.byTask).map(([k, v]) => `<div>${esc(k)}: ${usd(v)}</div>`).join("") || "-"}</div>
    </div>
    <h2>Cài đặt tối ưu chi phí</h2>
    <form class="card" id="setForm">
      <div class="grid">
        <div><label>Ngân sách AI / tháng (USD)</label><input name="monthlyBudgetUsd" value="${s.monthlyBudgetUsd}"></div>
        <div><label>Tiền tệ hiển thị</label><input name="currency" value="${esc(s.currency)}"></div>
        <div><label>Ollama URL</label><input name="ollamaUrl" value="${esc(s.ollamaUrl)}"></div>
        <div><label>Ollama model</label><input name="ollamaModel" value="${esc(s.ollamaModel)}"></div>
      </div>
      <div class="checks" style="margin-top:12px">
        <label><input type="checkbox" name="freeFirst" ${s.freeFirst ? "checked" : ""}> Ưu tiên chạy local miễn phí cho tác vụ "Tiết kiệm"</label>
        <label><input type="checkbox" name="responseCache" ${s.responseCache ? "checked" : ""}> Cache câu trả lời giống hệt ($0)</label>
        <label><input type="checkbox" name="approvePaidTools" ${s.approvePaidTools ? "checked" : ""}> Trợ lý phải hỏi trước khi gọi tool tốn phí</label>
      </div>
      <h3 style="margin-top:16px">Mức model cho từng tác vụ</h3>
      <div class="grid">${tasks
        .map((t) => `<div><label>${t} (mặc định: ${st.taskTier[t]})</label><select name="tier_${t}">${tierOptions(s.tierOverrides[t] || "auto").replace("Tự động (rẻ nhất đủ tốt)", "Mặc định")}</select></div>`)
        .join("")}</div>
      <p><button class="primary">Lưu cài đặt</button></p>
    </form>
    <h2>Bảng giá model (USD / 1 triệu token)</h2>
    <table class="list card">${Object.entries(st.tiers).map(([k, t]) => `<tr><td><b>${k}</b></td><td>${esc(t.label)}</td><td>vào $${t.in}</td><td>ra $${t.out}</td><td>cache đọc $${t.cacheRead}</td></tr>`).join("")}</table>
    <h2>Lượt gọi gần đây</h2>
    <table class="list card">${c.recent.map((e) => `<tr><td>${new Date(e.at).toLocaleString("vi-VN")}</td><td>${esc(e.task)}</td><td>${esc(e.model || e.tier)}</td><td>${usd(e.costUsd)}</td><td class="muted">${esc(e.note || "")}${e.savedUsd ? ` tiết kiệm ${usd(e.savedUsd)}` : ""}</td></tr>`).join("") || "<tr><td>-</td></tr>"}</table>`;
  $("#setForm").onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    const tierOverrides = {};
    for (const t of tasks) {
      const v = f[`tier_${t}`].value;
      if (v !== "auto") tierOverrides[t] = v;
    }
    try {
      await api("/settings", {
        method: "PUT",
        body: { monthlyBudgetUsd: Number(f.monthlyBudgetUsd.value) || 0, currency: f.currency.value, ollamaUrl: f.ollamaUrl.value, ollamaModel: f.ollamaModel.value, freeFirst: f.freeFirst.checked, responseCache: f.responseCache.checked, approvePaidTools: f.approvePaidTools.checked, tierOverrides },
      });
      toast("Đã lưu cài đặt");
    } catch (err) {
      toast(err.message, true);
    }
  };
};

// ---------- router ----------
async function route() {
  const view = (location.hash || "#dashboard").slice(1);
  $$("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === view));
  try {
    await (views[view] || views.dashboard)();
  } catch (e) {
    main.innerHTML = `<div class="card"><b>Lỗi:</b> ${esc(e.message)}</div>`;
  }
}
$$("#nav a").forEach((a) => (a.href = `#${a.dataset.view}`));
window.addEventListener("hashchange", route);
await loadBrands().catch(() => {});
route();
