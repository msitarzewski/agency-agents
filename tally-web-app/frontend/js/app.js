/**
 * ============================================================================
 * APP.JS — shared front-end core
 * ============================================================================
 * Everything page scripts need:
 *   App.api()        fetch wrapper with error toasts + 409 duplicate handling
 *   App.fmtINR()     Indian grouping (₹1,00,000.00)
 *   App.toWords()    amount → words (Indian system)
 *   App.autocomplete() searchable dropdown with keyboard navigation
 *   App.toast()      styled notifications
 *   App.theme()      dark-mode manager
 *   App.hotkeys()    Ctrl+S / Ctrl+K / Ctrl+Alt+N registry
 *   App.search()     global search across ledgers & vouchers
 * ============================================================================
 */
(function () {
  'use strict';

  const App = (window.App = {});

  /* ------------------------------------------------------------- helpers -- */
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  const round2 = (n) => Math.round((Number(n) + Number.EPSILON) * 100) / 100;

  App.$ = $; App.$$ = $$; App.esc = esc; App.debounce = debounce; App.round2 = round2;

  /* ----------------------------------------------------------- API client -- */
  /**
   * Fetch wrapper. Returns parsed `data` on success (res.success true).
   * On failure throws Error with .payload for field errors; shows a toast
   * unless opts.quiet.
   */
  App.api = async function api(path, opts = {}) {
    const { method = 'GET', body, quiet = false } = opts;
    let res;
    try {
      res = await fetch(path.startsWith('/api') ? path : '/api' + path, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (err) {
      App.sync?.setStatus('disconnected', 'Server unreachable');
      const e = new Error('Cannot reach the app server — is it running?');
      if (!quiet) App.toast('error', 'Network error', e.message);
      throw e;
    }
    let json = {};
    try { json = await res.json(); } catch { /* non-JSON */ }
    if (!res.ok || json.success === false) {
      const err = new Error(json.error?.message || `Request failed (${res.status})`);
      err.status = res.status;
      err.code = json.error?.code;
      err.errors = json.error?.errors || null;
      err.payload = json;
      if (!quiet && !opts.noToast) App.toast('error', err.code === 'DUPLICATE' ? 'Duplicate entry' : 'Error', err.message);
      throw err;
    }
    return json.data !== undefined ? json.data : json;
  };
  /** Full envelope (source/queued/message) when the caller needs it. */
  App.apiRaw = (path, opts) => fetch(path.startsWith('/api') ? path : '/api' + path, {
    method: opts?.method || 'GET',
    headers: opts?.body ? { 'Content-Type': 'application/json' } : undefined,
    body: opts?.body ? JSON.stringify(opts.body) : undefined,
  }).then((r) => r.json());

  /* ------------------------------------------------------------ GST states -- */
  App.GST_STATES = {
    '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab', '04': 'Chandigarh',
    '05': 'Uttarakhand', '06': 'Haryana', '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
    '10': 'Bihar', '11': 'Sikkim', '12': 'Arunachal Pradesh', '13': 'Nagaland', '14': 'Manipur',
    '15': 'Mizoram', '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam', '19': 'West Bengal',
    '20': 'Jharkhand', '21': 'Odisha', '22': 'Chattisgarh', '23': 'Madhya Pradesh', '24': 'Gujarat',
    '26': 'Dadra and Nagar Haveli and Daman and Diu', '27': 'Maharashtra', '29': 'Karnataka',
    '30': 'Goa', '31': 'Lakshadweep', '32': 'Kerala', '33': 'Tamil Nadu', '34': 'Puducherry',
    '35': 'Andaman and Nicobar Islands', '36': 'Telangana', '37': 'Andhra Pradesh', '38': 'Ladakh',
  };
  App.stateFromGSTIN = (g) => App.GST_STATES[String(g || '').slice(0, 2)] || null;
  App.validGSTIN = (g) => /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(String(g || '').toUpperCase());

  /* ------------------------------------------------------------ formatters -- */
  App.fmtINR = function (n, { sign = false } = {}) {
    const v = round2(Number(n) || 0);
    const neg = v < 0;
    const x = Math.abs(v).toFixed(2).split('.');
    let last3 = x[0].slice(-3);
    const rest = x[0].slice(0, -3);
    if (rest) last3 = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
    const prefix = neg ? '-' : sign ? '+' : '';
    return `${prefix}₹${last3}.${x[1]}`;
  };
  App.fmtNum = (n) => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(Number(n) || 0);

  /** ISO yyyy-mm-dd (input[type=date]) → DD-MM-YYYY */
  App.fmtDate = (iso) => {
    if (!iso) return '';
    if (/^\d{8}$/.test(iso)) return `${iso.slice(6, 8)}-${iso.slice(4, 6)}-${iso.slice(0, 4)}`;
    const [y, m, d] = iso.split('-');
    return d && m ? `${d}-${m}-${y}` : iso;
  };
  /** anything → ISO yyyy-mm-dd for <input type=date> */
  App.toISODate = (v) => {
    if (!v) return new Date().toISOString().slice(0, 10);
    if (/^\d{4}-\d{2}-\d{2}$/.test(v)) return v;
    if (/^\d{8}$/.test(v)) return `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6, 8)}`;
    const [d, m, y] = String(v).split('-');
    return y ? `${y}-${m}-${d}` : v;
  };
  App.timeAgo = (iso) => {
    if (!iso) return '—';
    const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
    if (s < 5) return 'just now';
    if (s < 60) return `${Math.floor(s)}s ago`;
    if (s < 3600) return `${Math.floor(s / 60)}m ago`;
    if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
    return `${Math.floor(s / 86400)}d ago`;
  };

  /* --------------------------------------------------- number → words (₹) -- */
  const ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
    'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
  const TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  const two = (n) => (n < 20 ? ONES[n] : TENS[Math.floor(n / 10)] + (n % 10 ? ' ' + ONES[n % 10] : ''));
  const three = (n) => (Math.floor(n / 100) ? ONES[Math.floor(n / 100)] + ' Hundred' + (n % 100 ? ' ' + two(n % 100) : '') : two(n));
  App.toWords = function (amount) {
    const v = round2(Number(amount) || 0);
    const rupees = Math.floor(Math.abs(v));
    const paise = Math.round((Math.abs(v) - rupees) * 100);
    if (!rupees && !paise) return 'Rupees Zero Only';
    const parts = [];
    const cr = Math.floor(rupees / 1e7), lk = Math.floor((rupees % 1e7) / 1e5), th = Math.floor((rupees % 1e5) / 1e3), hd = rupees % 1e3;
    if (cr) parts.push(`${three(cr)} Crore`);
    if (lk) parts.push(`${two(lk)} Lakh`);
    if (th) parts.push(`${two(th)} Thousand`);
    if (hd) parts.push(three(hd));
    let s = `Rupees ${parts.join(' ')}`;
    if (paise) s += ` and Paise ${two(paise)}`;
    return s + ' Only';
  };

  /* ---------------------------------------------------------------- toasts -- */
  App.toast = function (type, title, msg, ms = 4200) {
    const host = $('#toastHost');
    if (!host) return;
    const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', warning: 'fa-triangle-exclamation', info: 'fa-circle-info' };
    const el = document.createElement('div');
    el.className = `toast ${type || 'info'}`;
    el.innerHTML = `<i class="fa-solid ${icons[type] || icons.info} lead"></i>
      <div><div class="t-title">${esc(title)}</div>${msg ? `<div class="t-msg">${esc(msg)}</div>` : ''}</div>
      <button class="t-x"><i class="fa-solid fa-xmark"></i></button>`;
    el.querySelector('.t-x').onclick = () => el.remove();
    host.appendChild(el);
    setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 260); }, ms);
  };

  /* -------------------------------------------------------------- hotkeys -- */
  const hotkeys = [];
  App.hotkey = (combo, fn, opts = {}) => hotkeys.push({ combo, fn, opts });
  document.addEventListener('keydown', (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key.toLowerCase() === 's') { e.preventDefault(); App.emit('save'); return; }
    if (mod && e.key.toLowerCase() === 'k') { e.preventDefault(); openGlobalSearch(); return; }
    if (mod && e.altKey && e.key.toLowerCase() === 'n') { e.preventDefault(); App.emit('new'); return; }
    if (e.key === 'Escape') closeSearch();
    for (const h of hotkeys) {
      if (h.combo.toLowerCase() === e.key.toLowerCase() && !mod) { h.fn(e); }
    }
  });

  /* ------------------------------------------------------------ pub / sub -- */
  const listeners = {};
  App.on = (ev, fn) => { (listeners[ev] = listeners[ev] || []).push(fn); };
  App.emit = (ev, data) => (listeners[ev] || []).forEach((fn) => { try { fn(data); } catch (err) { console.error(err); } });

  /* ---------------------------------------------------------------- theme -- */
  App.theme = {
    get: () => localStorage.getItem('tw:theme') || 'light',
    set(t) {
      localStorage.setItem('tw:theme', t);
      document.documentElement.setAttribute('data-theme', t);
      $$('#themeToggle i').forEach((i) => (i.className = t === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon'));
      App.emit('theme', t);
    },
    toggle() { this.set(this.get() === 'dark' ? 'light' : 'dark'); },
  };
  document.addEventListener('DOMContentLoaded', () => {
    App.theme.set(App.theme.get());
    $('#themeToggle')?.addEventListener('click', () => App.theme.toggle());
    $('#hamburger')?.addEventListener('click', () => {
      $('#sidebar').classList.toggle('open');
      $('#sidebarBackdrop').classList.toggle('show');
    });
    $('#sidebarBackdrop')?.addEventListener('click', () => {
      $('#sidebar').classList.remove('open');
      $('#sidebarBackdrop').classList.remove('show');
    });
    // collapse panels
    $$('.collapse-head[data-toggle]').forEach((h) =>
      h.addEventListener('click', (e) => {
        if (e.target.closest('button')) return;
        document.getElementById(h.dataset.toggle)?.classList.toggle('open');
      }));
  });

  /* ------------------------------------------------- searchable dropdown --- */
  /**
   * App.autocomplete(inputEl, {
   *   source: async (query) => [{ label, sub, value }],   // or plain array
   *   select: (item) => {},                                // on pick
   *   placeholder: 'No matches'
   * })
   * Keyboard: ↑ ↓ navigate · Enter pick · Esc close. Typing filters remotely.
   */
  App.autocomplete = function (input, cfg) {
    if (!input || input._ac) return;
    const wrap = input.closest('.searchable') || input.parentElement;
    const dd = wrap.querySelector('.dd') || (() => { const d = document.createElement('div'); d.className = 'dd'; wrap.appendChild(d); return d; })();
    let items = [], active = -1, lastQuery = null;

    const hi = (q, s) => {
      if (!q) return esc(s);
      const i = s.toLowerCase().indexOf(q.toLowerCase());
      if (i < 0) return esc(s);
      return esc(s.slice(0, i)) + '<mark>' + esc(s.slice(i, i + q.length)) + '</mark>' + esc(s.slice(i + q.length));
    };
    const render = () => {
      if (!items.length) {
        dd.innerHTML = `<div class="dd-item none">${esc(cfg.emptyText || 'No matches found')}</div>`;
      } else {
        dd.innerHTML = items.map((it, i) => `
          <div class="dd-item ${i === active ? 'active' : ''}" data-i="${i}">
            <i class="fa-solid ${it.icon || 'fa-tag'}" style="color:var(--accent);opacity:.75;font-size:12px"></i>
            <span class="dd-main">${hi(lastQuery || '', it.label)}</span>
            ${it.sub ? `<span class="dd-sub">${esc(it.sub)}</span>` : ''}
          </div>`).join('');
      }
      wrap.classList.add('open');
    };
    const open = async () => {
      const q = input.value.trim();
      lastQuery = q;
      try {
        const src = cfg.source;
        items = typeof src === 'function' ? await src(q) : src.filter((x) => x.label.toLowerCase().includes(q.toLowerCase()));
        active = items.length ? 0 : -1;
      } catch { items = []; }
      render();
    };
    const close = () => wrap.classList.remove('open');
    const pick = (i) => {
      const it = items[i];
      if (it && cfg.select) { cfg.select(it, input); }
      if (it && cfg.fillInput !== false) input.value = it.label;
      close();
      input.dispatchEvent(new Event('change', { bubbles: true }));
    };

    input.addEventListener('focus', open);
    input.addEventListener('input', debounce(open, 160));
    input.addEventListener('keydown', (e) => {
      if (!wrap.classList.contains('open')) { if (e.key === 'ArrowDown') open(); return; }
      if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active + 1, items.length - 1); render(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, 0); render(); }
      else if (e.key === 'Enter') { if (active >= 0) { e.preventDefault(); pick(active); } }
      else if (e.key === 'Escape') close();
    });
    dd.addEventListener('mousedown', (e) => {
      const item = e.target.closest('.dd-item');
      if (item && item.dataset.i !== undefined) { e.preventDefault(); pick(+item.dataset.i); }
    });
    document.addEventListener('click', (e) => { if (!wrap.contains(e.target)) close(); });
    input._ac = { refresh: open, close };
  };

  /* ---------------------------------------------------------- ledgers cache -- */
  let ledgerCache = null;
  App.ledgers = async function (force = false) {
    if (!ledgerCache || force) ledgerCache = App.api('/ledgers?channel=xml').catch(() => []);
    return ledgerCache;
  };
  App.partySource = (filterFn) => async (q) => {
    const all = await App.ledgers();
    let list = all;
    if (filterFn) list = list.filter(filterFn);
    if (q) { const lq = q.toLowerCase(); list = list.filter((x) => x.name.toLowerCase().includes(lq) || (x.gstin || '').toLowerCase().includes(lq)); }
    return list.slice(0, 25).map((l) => ({
      label: l.name, sub: l.gstin ? `${l.gstin} · ${l.state || ''}` : l.parent, value: l.name, ledger: l,
    }));
  };
  App.cashBankSource = () => App.partySource((l) => /cash|bank/i.test(l.parent || '') || /cash|bank/i.test(l.name));

  /* --------------------------------------------------------- global search -- */
  function ensureSearchModal() {
    if ($('#gSearchModal')) return $('#gSearchModal');
    const ov = document.createElement('div');
    ov.className = 'modal-overlay';
    ov.id = 'gSearchModal';
    ov.innerHTML = `<div class="modal" style="width:min(620px,100%)">
      <div class="modal-head"><i class="fa-solid fa-magnifying-glass" style="color:var(--accent)"></i><h3>Search everything</h3>
        <button class="icon-btn x" data-close><i class="fa-solid fa-xmark"></i></button></div>
      <input class="input" id="gSearchInput" placeholder="Ledgers, voucher numbers, parties…" style="font-size:15px;padding:12px 14px" autocomplete="off">
      <div id="gSearchResults" style="margin-top:14px;max-height:52vh;overflow:auto"></div>
    </div>`;
    document.body.appendChild(ov);
    ov.addEventListener('click', (e) => { if (e.target === ov || e.target.closest('[data-close]')) ov.classList.remove('open'); });
    const inp = ov.querySelector('#gSearchInput');
    inp.addEventListener('input', debounce(runSearch, 220));
    return ov;
  }
  async function runSearch() {
    const q = $('#gSearchInput').value.trim();
    const box = $('#gSearchResults');
    if (q.length < 2) { box.innerHTML = `<div class="empty-state"><i class="fa-solid fa-keyboard"></i>Type at least 2 characters…</div>`; return; }
    box.innerHTML = `<div class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i>Searching…</div>`;
    const lq = q.toLowerCase();
    const [ledgers, vouchers] = await Promise.all([
      App.ledgers().catch(() => []),
      App.api(`/vouchers?limit=500`).catch(() => []),
    ]);
    const ledHits = ledgers.filter((l) => l.name.toLowerCase().includes(lq) || (l.gstin || '').toLowerCase().includes(lq)).slice(0, 8);
    const vchHits = vouchers.filter((v) => (v.voucherNumber || '').toLowerCase().includes(lq) || (v.party || '').toLowerCase().includes(lq)).slice(0, 8);
    if (!ledHits.length && !vchHits.length) { box.innerHTML = `<div class="empty-state"><i class="fa-solid fa-face-thinking"></i>Nothing found for “${esc(q)}”</div>`; return; }
    box.innerHTML =
      (ledHits.length ? `<div class="nav-label" style="padding-left:4px">Ledgers</div>` +
        ledHits.map((l) => `<a class="dd-item" href="reports.html?report=ledger&ledger=${encodeURIComponent(l.name)}">
          <i class="fa-solid fa-address-book" style="color:var(--accent)"></i>
          <span class="dd-main">${esc(l.name)}</span><span class="dd-sub">${esc(l.parent || '')}</span></a>`).join('') : '') +
      (vchHits.length ? `<div class="nav-label" style="padding-left:4px;margin-top:10px">Vouchers</div>` +
        vchHits.map((v) => `<div class="dd-item"><i class="fa-solid fa-receipt" style="color:var(--primary-500)"></i>
          <span class="dd-main">${esc(v.voucherNumber)} · ${esc(v.party || '—')}</span>
          <span class="dd-sub">${esc(v.voucherType)} · ${App.fmtDate(v.date)} · ${App.fmtINR(v.amount)}</span></div>`).join('') : '');
  }
  function openGlobalSearch() { const m = ensureSearchModal(); m.classList.add('open'); setTimeout(() => $('#gSearchInput').focus(), 30); }
  function closeSearch() { $('#gSearchModal')?.classList.remove('open'); }
  document.addEventListener('DOMContentLoaded', () => {
    $('#globalSearch')?.addEventListener('focus', openGlobalSearch);
  });

  /* --------------------------------------------------------------- drafts -- */
  App.draft = {
    key: (k) => `tw:draft:${k}`,
    save(k, data) { try { localStorage.setItem(this.key(k), JSON.stringify({ t: Date.now(), data })); App.emit('draft-saved', k); } catch {} },
    load(k) { try { const raw = localStorage.getItem(this.key(k)); return raw ? JSON.parse(raw).data : null; } catch { return null; } },
    clear(k) { localStorage.removeItem(this.key(k)); },
  };

  /* ----------------------------------------------------------- field utils -- */
  App.setInvalid = (input, msg) => {
    const field = input.closest('.field') || input.parentElement;
    input.classList.add('invalid');
    if (field) { field.classList.add('invalid'); const em = field.querySelector('.err-msg'); if (em && msg) em.textContent = msg; }
  };
  App.clearInvalid = (rootEl) => {
    (rootEl || document).querySelectorAll('.field.invalid, .input.invalid, .select.invalid').forEach((el) => el.classList.remove('invalid'));
    (rootEl || document).querySelectorAll('.err-msg').forEach((el) => (el.textContent = ''));
  };
  App.applyFieldErrors = (rootEl, errors) => {
    Object.entries(errors || {}).forEach(([key, msg]) => {
      const input = (rootEl || document).querySelector(`#${key}, [data-field="${key}"]`);
      if (input) App.setInvalid(input, msg);
    });
  };

  /* ------------------------------------------------------------ overlay UI -- */
  App.confirm = (title, text, icon = 'question') => window.Swal
    ? Swal.fire({ title, text, icon, showCancelButton: true, confirmButtonColor: '#1a237e', cancelButtonColor: '#64748b', confirmButtonText: 'Yes, proceed' })
    : Promise.resolve({ isConfirmed: confirm(`${title}\n${text}`) });

  App.loading = (btn, on, label) => {
    if (!btn) return;
    if (on) {
      btn.dataset.orig = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span> ${label || 'Saving…'}`;
    } else {
      btn.disabled = false;
      if (btn.dataset.orig) btn.innerHTML = btn.dataset.orig;
    }
  };

  /* --------------------------------------------------------- voucher chips -- */
  App.vtChip = (type) => `<span class="vt-chip vt-${esc(String(type).toLowerCase().replace(/\s+/g, '-'))}">${esc(type)}</span>`;

  console.log('%c Tally Web App ', 'background:#1a237e;color:#00bcd4;font-weight:bold;border-radius:3px', 'core loaded');
})();
