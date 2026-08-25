/**
 * ============================================================================
 * VOUCHERENTRY.JS — all 8 Tally voucher types
 * ============================================================================
 * Key flows implemented here:
 *   • Party pick → GSTIN + State autofill → intra/inter-state GST mode
 *   • Item grid  → live taxable / CGST / SGST / IGST math per line
 *   • Journal    → dynamic multi-Dr/Cr rows with live balancing
 *   • Drafts     → debounced localStorage autosave per voucher type
 *   • Saving     → POST /api/vouchers/<type> → toast + queue awareness;
 *                  409 DUPLICATE → confirm → re-post with force:true
 *   • Printing   → A4 / 80mm thermal invoice in a clean print window
 * ============================================================================
 */
(function () {
  'use strict';
  const { $, $$, esc, fmtINR, toast, round2, debounce } = App;

  let activeType = 'sales';
  let stockItems = [];
  const GST_RATES = [0, 5, 12, 18, 28];

  const companyState = () => (App.company?.state) || 'Maharashtra';

  /* ====================================================================== */
  /*  VOUCHER TYPE SWITCHING                                                */
  /* ====================================================================== */
  function setType(type, silent) {
    activeType = type;
    $$('.vtype-btn').forEach((b) => b.classList.toggle('active', b.dataset.type === type));
    $$('.voucher-panel').forEach((p) => p.classList.toggle('active', p.id === `panel-${type}`));
    if (!silent) {
      const draft = App.draft.load(`vch:${type}`);
      if (draft) restoreDraft(type, draft);
    }
  }

  /* ====================================================================== */
  /*  AUTO NUMBERING                                                        */
  /* ====================================================================== */
  async function autonumber(type) {
    const map = { sales: 'Sales', purchase: 'Purchase', payment: 'Payment', receipt: 'Receipt', contra: 'Contra', journal: 'Journal', 'credit-note': 'Credit Note', 'debit-note': 'Debit Note' };
    try {
      const d = await App.api(`/vouchers/next-number?voucherType=${encodeURIComponent(map[type])}`, { quiet: true });
      const el = $(`#${type}-number`);
      if (el && !el.value) el.value = d.voucherNumber;
    } catch { /* leave blank — Tally assigns on push */ }
  }

  /* ====================================================================== */
  /*  ITEM TABLES (sales / purchase / notes)                                */
  /* ====================================================================== */
  function itemRowHtml(tbodyId, i) {
    const idp = tbodyId.replace('-items', '');
    return `<tr data-row>
      <td class="sno">${i}</td>
      <td><input class="input item-name" placeholder="Search stock item…" autocomplete="off"></td>
      <td><input class="input item-hsn" style="width:82px" placeholder="HSN"></td>
      <td><input class="input item-qty" type="number" min="0" step="any" style="width:72px" value="1"></td>
      <td><input class="input item-rate" type="number" min="0" step="0.01" style="width:104px" placeholder="0.00"></td>
      <td><input class="input item-disc" type="number" min="0" max="100" step="0.1" style="width:64px" value="0"></td>
      <td class="calc c-taxable">—</td>
      <td><select class="select item-gstrate">${GST_RATES.map((r) => `<option value="${r}" ${r === 18 ? 'selected' : ''}>${r}%</option>`).join('')}</select></td>
      <td class="calc c-cgst">—</td>
      <td class="calc c-sgst">—</td>
      <td class="calc c-igst">—</td>
      <td class="calc c-total" style="font-weight:700">—</td>
      <td><button class="rm row-del" title="Remove line" type="button"><i class="fa-solid fa-xmark"></i></button></td>
    </tr>`;
  }

  function addItemRow(tbodyId, focus = true) {
    const tbody = document.getElementById(tbodyId);
    const i = tbody.rows.length + 1;
    tbody.insertAdjacentHTML('beforeend', itemRowHtml(tbodyId, i));
    const row = tbody.lastElementChild;
    wireItemRow(row, tbodyId);
    if (focus) row.querySelector('.item-name').focus();
    recalcItems(tbodyId);
  }

  function wireItemRow(row, tbodyId) {
    // stock item autocomplete
    const nameInput = row.querySelector('.item-name');
    App.autocomplete(nameInput, {
      emptyText: 'No stock items — type free-text for a non-inventory line',
      source: async (q) => {
        const lq = (q || '').toLowerCase();
        return stockItems
          .filter((s) => s.name.toLowerCase().includes(lq))
          .slice(0, 12)
          .map((s) => ({ label: s.name, sub: s.hsn ? `HSN ${s.hsn} · ₹${s.rate}` : `₹${s.rate}`, value: s.name, item: s }));
      },
      select: (it) => {
        const r = nameInput.closest('tr');
        if (it.item.hsn) r.querySelector('.item-hsn').value = it.item.hsn;
        r.querySelector('.item-rate').value = it.item.rate ?? '';
        recalcItems(tbodyId);
      },
    });
    row.querySelectorAll('input, select').forEach((inp) => {
      inp.addEventListener('input', () => recalcItems(tbodyId));
      inp.addEventListener('change', () => recalcItems(tbodyId));
    });
    row.querySelector('.rm').addEventListener('click', () => {
      row.remove();
      renumber(tbodyId);
      recalcItems(tbodyId);
    });
    // Enter on rate/disc jumps to a new row (fast keyboard entry)
    row.querySelector('.item-disc').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); addItemRow(tbodyId); }
    });
    row.querySelector('.item-gstrate').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); addItemRow(tbodyId); }
    });
  }

  function renumber(tbodyId) {
    $$('#' + tbodyId + ' tr').forEach((tr, i) => (tr.querySelector('.sno').textContent = i + 1));
  }

  /** Recompute every line + totals + words for one item table. */
  function recalcItems(tbodyId) {
    const idp = tbodyId.replace('-items', '');
    const partyState = $(`#${idp}-state`)?.value || '';
    const inter = partyState && partyState.toLowerCase() !== companyState().toLowerCase();
    const badge = $(`#gstMode${idp === 'sales' ? 'Sales' : idp === 'purchase' ? 'Purchase' : ''}`);
    if (badge) badge.textContent = inter ? 'IGST (Inter-state)' : 'CGST + SGST (Intra-state)';

    let tTax = 0, tCgst = 0, tSgst = 0, tIgst = 0;
    $$('#' + tbodyId + ' tr').forEach((tr) => {
      const qty = Number(tr.querySelector('.item-qty').value) || 0;
      const rate = Number(tr.querySelector('.item-rate').value) || 0;
      const disc = Number(tr.querySelector('.item-disc').value) || 0;
      const g = Number(tr.querySelector('.item-gstrate').value) || 0;
      const taxable = round2(qty * rate * (1 - disc / 100));
      const tax = round2((taxable * g) / 100);
      let cgst = 0, sgst = 0, igst = 0;
      if (inter) igst = tax; else { cgst = round2(tax / 2); sgst = round2(tax - cgst); }
      tr.querySelector('.c-taxable').textContent = taxable ? App.fmtNum(taxable) : '—';
      tr.querySelector('.c-cgst').textContent = cgst ? App.fmtNum(cgst) : '—';
      tr.querySelector('.c-sgst').textContent = sgst ? App.fmtNum(sgst) : '—';
      tr.querySelector('.c-igst').textContent = igst ? App.fmtNum(igst) : '—';
      tr.querySelector('.c-total').textContent = taxable + tax ? App.fmtNum(round2(taxable + tax)) : '—';
      tTax = round2(tTax + taxable); tCgst = round2(tCgst + cgst);
      tSgst = round2(tSgst + sgst); tIgst = round2(tIgst + igst);
    });
    const set = (id, v) => { const el = $(id); if (el) el.textContent = App.fmtNum(v); };
    set(`#${idp}-t-taxable`, tTax); set(`#${idp}-t-cgst`, tCgst);
    set(`#${idp}-t-sgst`, tSgst); set(`#${idp}-t-igst`, tIgst);
    const grand = round2(tTax + tCgst + tSgst + tIgst);
    $(`#${idp}-t-grand`).textContent = fmtINR(grand);
    $(`#${idp}-words`).textContent = App.toWords(grand);
    saveDraftDebounced();
  }

  /* ====================================================================== */
  /*  PARTY AUTOCOMPLETE (GSTIN + state autofill)                           */
  /* ====================================================================== */
  function wireParty(idp, groupFilter) {
    const input = $(`#${idp}-party`);
    if (!input) return;
    App.autocomplete(input, {
      emptyText: 'No matching ledgers',
      source: App.partySource(groupFilter),
      select: (it) => {
        const l = it.ledger;
        const gstinEl = $(`#${idp}-gstin`);
        const stateEl = $(`#${idp}-state`);
        if (gstinEl) gstinEl.value = l.gstin || '';
        if (stateEl) {
          stateEl.value = l.state || App.stateFromGSTIN(l.gstin) || '';
          if (!stateEl.value) {
            // GSTIN absent → let user pick; still recalc
          }
        }
        const tbody = `${idp}-items`;
        if (document.getElementById(tbody)) recalcItems(tbody);
        toast('info', 'Party selected', `${l.name}${l.state ? ` · ${l.state}` : ''} — GST mode updated`, 2200);
      },
    });
  }

  /* ====================================================================== */
  /*  JOURNAL GRID                                                          */
  /* ====================================================================== */
  function journalRow() {
    const div = document.createElement('div');
    div.className = 'journal-row';
    div.innerHTML = `
      <div class="searchable" data-searchable><input class="input j-ledger" placeholder="Ledger…" autocomplete="off"><i class="fa-solid fa-chevron-down chev"></i><div class="dd"></div></div>
      <input class="input j-dr" type="number" min="0" step="0.01" placeholder="0.00" style="text-align:right">
      <input class="input j-cr" type="number" min="0" step="0.01" placeholder="0.00" style="text-align:right">
      <button class="rm" type="button" title="Remove"><i class="fa-solid fa-xmark"></i></button>`;
    const ledgerInput = div.querySelector('.j-ledger');
    App.autocomplete(ledgerInput, { source: App.partySource(), emptyText: 'No matching ledgers' });
    div.querySelectorAll('input').forEach((i) => i.addEventListener('input', journalCheck));
    div.querySelector('.rm').addEventListener('click', () => { div.remove(); journalCheck(); });
    // Only one side per row: typing Dr clears Cr and vice versa
    const dr = div.querySelector('.j-dr'), cr = div.querySelector('.j-cr');
    dr.addEventListener('input', () => { if (dr.value) cr.value = ''; journalCheck(); });
    cr.addEventListener('input', () => { if (cr.value) dr.value = ''; journalCheck(); });
    return div;
  }

  function journalCheck() {
    let dr = 0, cr = 0, filled = 0;
    $$('#journal-rows .journal-row').forEach((r) => {
      const d = Number(r.querySelector('.j-dr').value) || 0;
      const c = Number(r.querySelector('.j-cr').value) || 0;
      dr = round2(dr + d); cr = round2(cr + c);
      if ((r.querySelector('.j-ledger').value || '') && (d || c)) filled++;
    });
    const ok = dr > 0 && Math.abs(dr - cr) < 0.01;
    $('#journal-check').innerHTML = `
      <span class="${dr === cr && dr > 0 ? 'ok' : 'bad'}">
        <i class="fa-solid ${ok ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i>
        Debit ${fmtINR(dr)} = Credit ${fmtINR(cr)} ${ok ? '· balanced ✓' : '· must balance to save'}</span>
      <span style="color:var(--muted);font-weight:400">${filled} line(s)</span>`;
    saveDraftDebounced();
  }

  /* ====================================================================== */
  /*  DRAFTS                                                                */
  /* ====================================================================== */
  const saveDraftDebounced = debounce(() => saveDraft(), 900);
  function saveDraft() {
    const d = collectPayload(activeType, true);
    App.draft.save(`vch:${activeType}`, d);
    const note = $(`#draftNote-${activeType}`);
    if (note) {
      note.innerHTML = `<i class="fa-solid fa-check"></i> Draft saved ${new Date().toLocaleTimeString('en-IN')}`;
      note.style.color = 'var(--success)';
    }
  }
  function restoreDraft(type, d) {
    try {
      Object.entries(d).forEach(([k, v]) => {
        const el = $(`#${type}-${k}`);
        if (el && v != null && !(k === 'items' || k === 'entries' || k === 'instrument')) {
          if (el.type === 'date') el.value = App.toISODate(v);
          else el.value = v;
        }
      });
      (d.items || []).forEach((it, idx) => {
        const tbody = document.getElementById(`${type}-items`);
        if (!tbody) return;
        if (tbody.rows.length <= idx) addItemRow(`${type}-items`, false);
        const row = tbody.rows[idx];
        row.querySelector('.item-name').value = it.name || '';
        row.querySelector('.item-hsn').value = it.hsn || '';
        row.querySelector('.item-qty').value = it.qty ?? 1;
        row.querySelector('.item-rate').value = it.rate ?? '';
        row.querySelector('.item-disc').value = it.discountPercent ?? 0;
        row.querySelector('.item-gstrate').value = it.gstRate ?? 18;
      });
      if (d.entries && type === 'journal') {
        $('#journal-rows').innerHTML = '';
        d.entries.forEach((e) => {
          const row = journalRow();
          row.querySelector('.j-ledger').value = e.ledger || '';
          if (e.debit) row.querySelector('.j-dr').value = e.amount; else row.querySelector('.j-cr').value = e.amount;
          $('#journal-rows').appendChild(row);
        });
        journalCheck();
      }
      if (document.getElementById(`${type}-items`)) recalcItems(`${type}-items`);
      toast('info', 'Draft restored', 'Unsaved draft for this voucher type was recovered');
    } catch { /* drafts are best-effort */ }
  }

  /* ====================================================================== */
  /*  COLLECT → PAYLOAD                                                     */
  /* ====================================================================== */
  function val(id) { const el = $(id); return el ? el.value.trim() : ''; }

  function collectItems(type) {
    return $$('#' + type + '-items tr').map((tr, i) => ({
      sno: i + 1,
      name: tr.querySelector('.item-name').value.trim(),
      hsn: tr.querySelector('.item-hsn').value.trim(),
      unit: tr.dataset.unit || 'Nos',
      qty: Number(tr.querySelector('.item-qty').value) || 0,
      rate: Number(tr.querySelector('.item-rate').value) || 0,
      discountPercent: Number(tr.querySelector('.item-disc').value) || 0,
      gstRate: Number(tr.querySelector('.item-gstrate').value) || 0,
    })).filter((it) => it.name || it.qty > 0);
  }

  function collectPayload(type, forDraft = false) {
    const date = val(`#${type}-date`) || new Date().toISOString().slice(0, 10);
    const narration = val(`#${type}-narration`);
    if (['sales', 'purchase', 'credit-note', 'debit-note'].includes(type)) {
      const p = {
        date, narration,
        voucherNumber: val(`#${type}-number`),
        party: val(`#${type}-party`),
        partyGstin: val(`#${type}-gstin`).toUpperCase(),
        partyState: val(`#${type}-state`),
        items: collectItems(type),
      };
      if (type === 'sales') p.salesLedger = val(`#${type}-ledger`);
      if (type === 'purchase') {
        p.purchaseLedger = val(`#${type}-ledger`);
        p.reference = val(`#${type}-ref`);
        p.referenceDate = val(`#${type}-refdate`) || undefined;
      }
      if (type === 'credit-note' || type === 'debit-note') {
        p.originalInvoice = val(`#${type}-orig`);
        p.reason = val(`#${type}-reason`);
      }
      return p;
    }
    if (type === 'payment') {
      const mode = val('#payment-mode');
      const amount = Number(val('#payment-amount')) || 0;
      const cheque = { mode, chequeNo: val('#payment-chequeno'), chequeDate: val('#payment-chequedate'), bank: val('#payment-bank') };
      let narr = narration;
      if (mode === 'Cheque' && cheque.chequeNo) narr = `${narr}${narr ? ' · ' : ''}Chq ${cheque.chequeNo}${cheque.bank ? ` (${cheque.bank})` : ''}`;
      if (['NEFT/RTGS', 'UPI', 'Card'].includes(mode)) narr = `${narr}${narr ? ' · ' : ''}${mode}${cheque.chequeNo ? ` ref ${cheque.chequeNo}` : ''}`;
      return {
        date, narration: narr, voucherNumber: val('#payment-number'), instrument: cheque,
        entries: [
          { ledger: val('#payment-to'), amount, debit: true },
          { ledger: val('#payment-from'), amount, debit: false },
        ],
      };
    }
    if (type === 'receipt') {
      const mode = val('#receipt-mode');
      const amount = Number(val('#receipt-amount')) || 0;
      let narr = narration;
      const ref = val('#receipt-chequeno');
      if (ref) narr = `${narr}${narr ? ' · ' : ''}${mode} ref ${ref}`;
      return {
        date, narration: narr, voucherNumber: val('#receipt-number'),
        instrument: { mode, chequeNo: ref, bank: val('#receipt-bank') },
        entries: [
          { ledger: val('#receipt-in'), amount, debit: true },
          { ledger: val('#receipt-from'), amount, debit: false },
        ],
      };
    }
    if (type === 'contra') {
      const amount = Number(val('#contra-amount')) || 0;
      const dir = val('#contra-direction');
      let from = val('#contra-from'), to = val('#contra-to');
      if (dir === 'deposit' && !from) from = 'Cash';
      return {
        date, narration: val('#contra-narration'), voucherNumber: val('#contra-number'),
        entries: [
          { ledger: from, amount, debit: true },
          { ledger: to, amount, debit: false },
        ],
      };
    }
    if (type === 'journal') {
      const entries = $$('#journal-rows .journal-row').map((r) => ({
        ledger: r.querySelector('.j-ledger').value.trim(),
        amount: Number(r.querySelector('.j-dr').value) || Number(r.querySelector('.j-cr').value) || 0,
        debit: !!Number(r.querySelector('.j-dr').value),
      })).filter((e) => e.ledger && e.amount > 0);
      return { date, narration: val('#journal-narration'), voucherNumber: val('#journal-number'), entries };
    }
    return {};
  }

  /* ====================================================================== */
  /*  SAVE                                                                  */
  /* ====================================================================== */
  async function save(type, opts = {}) {
    const payload = collectPayload(type);
    // light client-side validation first
    App.clearInvalid($(`#panel-${type}`));
    const problems = [];
    if (['sales', 'purchase', 'credit-note', 'debit-note'].includes(type) && !payload.party) {
      problems.push([`#${type}-party`, 'Party is required']);
    }
    if (problems.length) {
      problems.forEach(([sel, msg]) => { const el = $(sel); if (el) App.setInvalid(el, msg); });
      toast('error', 'Incomplete form', 'Please fix the highlighted fields');
      return;
    }
    if (opts.print) { payload._printAfter = true; }

    const btn = opts.btn || $(`[data-save="${type}"]`);
    App.loading(btn, true, 'Pushing to Tally…');
    try {
      let res;
      try {
        res = await App.apiRaw(`/vouchers/${type}`, { method: 'POST', body: payload });
      } catch (e) { throw e; }
      if (res.success === false && res.error?.code === 'DUPLICATE') {
        const ask = await App.confirm('Possible duplicate!', res.error.message + '\n\nSave anyway?', 'warning');
        if (!ask.isConfirmed) { App.loading(btn, false); return; }
        res = await App.apiRaw(`/vouchers/${type}`, { method: 'POST', body: { ...payload, force: true } });
      }
      if (res.success === false) {
        App.applyFieldErrors($(`#panel-${type}`), res.error?.errors);
        toast('error', 'Could not save', res.error?.message || 'Unknown error');
        App.loading(btn, false);
        return;
      }
      App.loading(btn, false);
      App.draft.clear(`vch:${type}`);
      toast(res.queued ? 'warning' : 'success',
        res.queued ? 'Saved — queued for Tally' : 'Voucher saved',
        res.message || `Pushed to ${res.source === 'tally' ? 'Tally' : 'demo store'}`);
      App.emit('voucher-saved', { type, payload, res });
      App.sync.socket?.emit('voucher:created', { label: `${type} ${payload.voucherNumber || payload.party}` });
      if (opts.print) printInvoice(type, payload, res);
      if (opts.thenNew) resetForm(type);
      autonumber(type);
    } catch (e) {
      App.loading(btn, false);
      toast('error', 'Save failed', e.message);
    }
  }

  function resetForm(type) {
    const panel = $(`#panel-${type}`);
    // clear everything except dates (dates reset to today)
    panel.querySelectorAll('input:not([type=hidden])').forEach((i) => {
      if (i.type === 'date') i.value = new Date().toISOString().slice(0, 10);
      else i.value = '';
    });
    panel.querySelectorAll('select').forEach((s) => { s.selectedIndex = 0; });
    if (document.getElementById(`${type}-items`)) {
      document.getElementById(`${type}-items`).innerHTML = '';
      addItemRow(`${type}-items`, false);
    }
    if (type === 'journal') {
      $('#journal-rows').innerHTML = '';
      addJournalRow(); addJournalRow();
      journalCheck();
    }
    autonumber(type);
    toast('info', 'Form cleared', 'Ready for a new entry', 1800);
  }

  /* ====================================================================== */
  /*  INVOICE PRINT (A4 + thermal 80mm)                                     */
  /* ====================================================================== */
  function printInvoice(type, payload, res) {
    const co = App.company || {};
    const party = payload.party || '';
    const inter = payload.partyState && payload.partyState.toLowerCase() !== companyState().toLowerCase();
    const rows = (payload.items || []).map((it, i) => {
      const taxable = round2(it.qty * it.rate * (1 - (it.discountPercent || 0) / 100));
      const tax = round2((taxable * (it.gstRate || 0)) / 100);
      return `<tr><td>${i + 1}</td><td>${esc(it.name)}</td><td>${esc(it.hsn || '')}</td>
        <td style="text-align:right">${it.qty}</td><td style="text-align:right">${App.fmtNum(it.rate)}</td>
        <td style="text-align:right">${App.fmtNum(taxable)}</td><td style="text-align:right">${it.gstRate}%</td>
        <td style="text-align:right">${inter ? App.fmtNum(tax) + ' (IGST)' : App.fmtNum(tax / 2) + ' + ' + App.fmtNum(tax / 2)}</td>
        <td style="text-align:right">${App.fmtNum(round2(taxable + tax))}</td></tr>`;
    }).join('');
    const tTax = round2((payload.items || []).reduce((s, it) => s + it.qty * it.rate * (1 - (it.discountPercent || 0) / 100), 0));
    const tTaxAmt = round2((payload.items || []).reduce((s, it) => {
      const tx = round2(it.qty * it.rate * (1 - (it.discountPercent || 0) / 100));
      return s + tx * (it.gstRate || 0) / 100;
    }, 0));
    const grand = round2(tTax + tTaxAmt);

    // Ask for the physical format, then render the invoice in a print window.
    window.Swal && Swal.fire({
      title: '<i class="fa-solid fa-print"></i> Print format', icon: 'question',
      showDenyButton: true, showCancelButton: true,
      confirmButtonText: 'A4 sheet', denyButtonText: '80mm Thermal', cancelButtonText: 'Cancel',
    }).then((fmt) => {
      if (fmt.isDismissed) return;
      const isThermal = fmt.isDenied;
      const css = isThermal
        ? `@page{size:80mm auto;margin:3mm} body{font:9px monospace;width:74mm}`
        : `@page{size:A4;margin:14mm} body{font:12px 'Segoe UI',Arial}`;
      const w = window.open('', '_blank', 'width=900,height=700');
      w.document.write(`<!DOCTYPE html><html><head><title>${esc(payload.voucherNumber || 'Invoice')}</title>
          <style>${css}
          body{color:#111;margin:0;padding:0}
          h1{font-size:${isThermal ? '13px' : '22px'};margin:0 0 2px;color:#1a237e}
          table{width:100%;border-collapse:collapse;margin-top:8px}
          th,td{border:1px solid #ccc;padding:${isThermal ? '2px 3px' : '5px 8px'};font-size:${isThermal ? '8.5px' : '11.5px'}}
          th{background:#eef1fa;text-align:left}
          .r{text-align:right}
          .tot{margin-top:10px;width:280px;margin-left:auto}
          .tot td{border:none;padding:2px 6px}
          .words{margin-top:10px;font-style:italic;font-size:${isThermal ? '8.5px' : '12px'}}
          .hdr{display:flex;justify-content:space-between;align-items:start}
          </style></head><body>
          <div class="hdr"><div><h1>${esc(co.name || 'Tally Web App')}</h1>
            <div>${esc(co.address || '')} ${esc(co.city || '')}</div>
            <div>GSTIN: ${esc(co.gstin || '—')}</div></div>
            <div style="text-align:right"><b>TAX INVOICE</b><br>No: ${esc(payload.voucherNumber || res?.data?.voucherNumber || '')}<br>
            Date: ${App.fmtDate(payload.date)}</div></div>
          <hr>
          <div><b>Bill to:</b> ${esc(party)} · ${esc(payload.partyGstin || 'Unregistered')} · ${esc(payload.partyState || '')}</div>
          <table><thead><tr><th>#</th><th>Item</th><th>HSN</th><th class="r">Qty</th><th class="r">Rate</th>
            <th class="r">Taxable</th><th class="r">GST</th><th class="r">Tax</th><th class="r">Total</th></tr></thead>
            <tbody>${rows}</tbody></table>
          <table class="tot">
            <tr><td>Taxable Value</td><td class="r">${App.fmtNum(tTax)}</td></tr>
            <tr><td>${inter ? 'IGST' : 'CGST + SGST'}</td><td class="r">${App.fmtNum(tTaxAmt)}</td></tr>
            <tr><td><b>Grand Total</b></td><td class="r"><b>${fmtINR(grand)}</b></td></tr></table>
          <div class="words">${App.toWords(grand)}</div>
          <div style="margin-top:${isThermal ? '10px' : '46px'};display:flex;justify-content:space-between">
            <span>Received by ____________</span><span>For ${esc(co.name || '')} ____________</span></div>
          </body></html>`);
      w.document.close();
      w.focus();
      setTimeout(() => w.print(), 350);
    });
  }

  /* ====================================================================== */
  /*  WIRING                                                                */
  /* ====================================================================== */
  function addJournalRow() { $('#journal-rows').appendChild(journalRow()); }

  document.addEventListener('DOMContentLoaded', async () => {
    // defaults
    const today = new Date().toISOString().slice(0, 10);
    $$('input[type=date]').forEach((i) => { if (!i.value) i.value = today; });

    // stock items for autocomplete
    try { stockItems = await App.api('/stock-items?channel=xml', { quiet: true }); } catch { stockItems = []; }

    // state datalists
    const dl = $('#stateList');
    if (dl) dl.innerHTML = Object.values(App.GST_STATES).map((s) => `<option value="${s}">`).join('');

    // voucher type switching + deep link (?type=)
    $$('.vtype-btn').forEach((b) => b.addEventListener('click', () => setType(b.dataset.type)));
    const urlType = new URLSearchParams(location.search).get('type');
    const defaultView = (await App.api('/settings', { quiet: true }).catch(() => ({})))?.defaultVoucherView || 'sales';
    setType(urlType && document.getElementById(`panel-${urlType}`) ? urlType : defaultView, true);

    // auto numbers
    ['sales', 'purchase', 'payment', 'receipt', 'contra', 'journal', 'credit-note', 'debit-note'].forEach(autonumber);

    // item tables: 1 blank row each
    ['sales-items', 'purchase-items', 'credit-note-items', 'debit-note-items'].forEach((t) => addItemRow(t, false));

    // party pickers
    wireParty('sales', (l) => l.parent === 'Sundry Debtors');
    wireParty('purchase', (l) => l.parent === 'Sundry Creditors');
    wireParty('credit-note', (l) => l.parent === 'Sundry Debtors');
    wireParty('debit-note', (l) => l.parent === 'Sundry Creditors');

    // simple-voucher pickers
    App.autocomplete($('#payment-from'), { source: App.cashBankSource(), emptyText: 'No cash/bank ledgers' });
    App.autocomplete($('#payment-to'), { source: App.partySource(), emptyText: 'No matching ledgers' });
    App.autocomplete($('#receipt-from'), { source: App.partySource(), emptyText: 'No matching ledgers' });
    App.autocomplete($('#receipt-in'), { source: App.cashBankSource(), emptyText: 'No cash/bank ledgers' });
    App.autocomplete($('#contra-from'), { source: App.cashBankSource(), emptyText: 'Cash / bank ledgers' });
    App.autocomplete($('#contra-to'), { source: App.cashBankSource(), emptyText: 'Cash / bank ledgers' });

    // payment/receipt mode conditional fields
    const modeToggle = (sel, box) => {
      const el = $(sel);
      el?.addEventListener('change', () => {
        $(box).classList.toggle('show', ['Cheque', 'NEFT/RTGS', 'UPI', 'Card'].includes(el.value));
      });
    };
    modeToggle('#payment-mode', '#payment-cheque-fields');
    modeToggle('#receipt-mode', '#receipt-cheque-fields');

    // contra direction → labels
    $('#contra-direction')?.addEventListener('change', (e) => {
      const labels = {
        deposit: ['From (Cash)', 'To (Bank)'],
        withdraw: ['From (Bank)', 'To (Cash)'],
        transfer: ['From (Bank)', 'To (Bank)'],
      }[e.target.value];
      $('#contra-from-label').textContent = labels[0];
      $('#contra-to-label').textContent = labels[1];
    });

    // journal seed rows
    addJournalRow(); addJournalRow();
    journalCheck();

    // add/clear row buttons
    $$('[data-add-row]').forEach((b) => b.addEventListener('click', () => addItemRow(b.dataset.addRow)));
    $$('[data-clear-rows]').forEach((b) => b.addEventListener('click', () => {
      document.getElementById(b.dataset.clearRows).innerHTML = '';
      addItemRow(b.dataset.clearRows);
    }));
    $('#journal-add')?.addEventListener('click', addJournalRow);

    // state input changes → GST mode recalc
    ['#sales-state', '#purchase-state', '#credit-note-state', '#debit-note-state'].forEach((sel) => {
      $(sel)?.addEventListener('change', () => {
        const idp = sel.replace('-state', '');
        if (document.getElementById(`${idp}-items`)) recalcItems(`${idp}-items`);
      });
    });

    // save buttons
    $$('[data-save]').forEach((b) => b.addEventListener('click', () => save(b.dataset.save, { btn: b })));
    $$('[data-save-new]').forEach((b) => b.addEventListener('click', () => save(b.dataset.saveNew, { btn: b, thenNew: true })));
    $$('[data-save-print]').forEach((b) => b.addEventListener('click', () => save(b.dataset.savePrint, { btn: b, print: true })));

    // keyboard: Ctrl+S → save active, Ctrl+Alt+N → new
    App.on('save', () => save(activeType, { btn: $(`[data-save="${activeType}"]`) }));
    App.on('new', () => resetForm(activeType));

    // any input → draft autosave (covers simple vouchers)
    $$('.voucher-panel').forEach((p) => p.addEventListener('input', saveDraftDebounced));
  });
})();
