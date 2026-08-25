/**
 * ============================================================================
 * LEDGERMASTER.JS — create / edit / delete ledgers + group tree view
 * ============================================================================
 */
(function () {
  'use strict';
  const { $, $$, esc, fmtINR, toast } = App;

  let allLedgers = [];
  let editing = null; // original name while editing

  /* ------------------------------------------------------------- loading -- */
  async function loadLedgers() {
    try {
      allLedgers = await App.api('/ledgers?channel=xml');
      renderTable();
      renderTree();
      $('#ledgerCount').textContent = `${allLedgers.length} ledgers`;
      const groups = [...new Set(allLedgers.map((l) => l.parent).filter(Boolean))].sort();
      const sel = $('#ledgerGroupFilter');
      sel.innerHTML = '<option value="">All groups</option>' + groups.map((g) => `<option>${esc(g)}</option>`).join('');
    } catch (e) {
      $('#ledgerTable tbody').innerHTML = `<tr><td colspan="7"><div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i>${esc(e.message)}</div></td></tr>`;
    }
  }

  async function loadGroups() {
    try {
      const groups = await App.api('/ledger-groups');
      $('#lg-parent').innerHTML = '<option value="">— Select group —</option>' +
        groups.filter((g) => g.name && g.name !== 'Primary').map((g) =>
          `<option value="${esc(g.name)}">${esc(g.name)}${g.nature && g.nature !== 'Primary' ? ` · ${esc(g.nature)}` : ''}</option>`).join('');
      $('#lg-state').innerHTML = '<option value="">— Select —</option>' +
        Object.values(App.GST_STATES).map((s) => `<option>${s}</option>`).join('');
    } catch { /* leave placeholders */ }
  }

  /* ------------------------------------------------------------- table --- */
  function renderTable() {
    const q = $('#ledgerSearch').value.toLowerCase();
    const group = $('#ledgerGroupFilter').value;
    const sort = $('#ledgerSort').value;
    let rows = allLedgers.filter((l) =>
      (!q || l.name.toLowerCase().includes(q) || (l.gstin || '').toLowerCase().includes(q) || (l.city || '').toLowerCase().includes(q)) &&
      (!group || l.parent === group));
    rows.sort((a, b) =>
      sort === 'name-desc' ? b.name.localeCompare(a.name)
        : sort === 'group' ? (a.parent || '').localeCompare(b.parent || '')
          : a.name.localeCompare(b.name));
    const tbody = $('#ledgerTable tbody');
    tbody.innerHTML = rows.length ? rows.map((l) => `
      <tr data-name="${esc(l.name)}">
        <td style="font-weight:600">${esc(l.name)}</td>
        <td><span class="badge badge-muted">${esc(l.parent || '—')}</span></td>
        <td style="font-family:var(--mono);font-size:11.5px">${esc(l.gstin || '—')}</td>
        <td>${esc(l.state || '—')}</td>
        <td>${esc(l.phone || '—')}</td>
        <td class="num">${l.openingBalance?.amount ? `${App.fmtNum(l.openingBalance.amount)} ${l.openingBalance.drCr || ''}` : '—'}</td>
        <td style="white-space:nowrap">
          <button class="icon-btn" style="width:32px;height:32px" data-edit="${esc(l.name)}" title="Edit"><i class="fa-solid fa-pen"></i></button>
          <button class="icon-btn" style="width:32px;height:32px" data-del="${esc(l.name)}" title="Delete"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`).join('')
      : `<tr><td colspan="7"><div class="empty-state"><i class="fa-solid fa-magnifying-glass"></i>No ledgers match the filters</div></td></tr>`;
    tbody.querySelectorAll('[data-edit]').forEach((b) => b.addEventListener('click', () => startEdit(b.dataset.edit)));
    tbody.querySelectorAll('[data-del]').forEach((b) => b.addEventListener('click', () => delLedger(b.dataset.del)));
  }

  /* -------------------------------------------------------------- tree --- */
  function renderTree() {
    const byGroup = {};
    allLedgers.forEach((l) => { (byGroup[l.parent || 'Others'] = byGroup[l.parent || 'Others'] || []).push(l); });
    const box = $('#ledgerTreeView');
    box.innerHTML = Object.keys(byGroup).sort().map((g) => `
      <div class="tree-group">
        <div class="tree-group-head" data-group="${esc(g)}">
          <i class="fa-solid fa-caret-right caret"></i>
          <i class="fa-solid fa-folder" style="color:var(--accent);font-size:12px"></i>
          ${esc(g)}
          <span class="tree-count">${byGroup[g].length}</span>
        </div>
        <div class="tree-ledgers">
          ${byGroup[g].map((l) => `
            <div class="tree-ledger" data-edit="${esc(l.name)}">
              <i class="fa-solid fa-book" style="opacity:.5;font-size:11px"></i>
              ${esc(l.name)}
              <span class="amt">${l.gstin ? esc(l.gstin) : ''}</span>
            </div>`).join('')}
        </div>
      </div>`).join('');
    box.querySelectorAll('.tree-group-head').forEach((h) =>
      h.addEventListener('click', () => h.parentElement.classList.toggle('open')));
    box.querySelectorAll('[data-edit]').forEach((el) =>
      el.addEventListener('click', () => startEdit(el.dataset.edit)));
  }

  /* -------------------------------------------------------- create/edit -- */
  function startEdit(name) {
    const l = allLedgers.find((x) => x.name === name);
    if (!l) return;
    editing = name;
    $('#ledgerFormTitle').innerHTML = `<i class="fa-solid fa-pen" style="color:var(--accent)"></i> Edit Ledger`;
    $('#ledgerSubmit').innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Update Ledger`;
    $('#ledgerFormReset').style.display = '';
    $('#lg-name').value = l.name;
    $('#lg-parent').value = l.parent || '';
    $('#lg-opening').value = l.openingBalance?.amount || '';
    $('#lg-drcr').value = l.openingBalance?.drCr || 'Dr';
    $('#lg-gstin').value = l.gstin || '';
    $('#lg-state').value = l.state || '';
    $('#lg-regtype').value = l.regType || 'Regular';
    $('#lg-address').value = l.address || '';
    $('#lg-city').value = l.city || '';
    $('#lg-pincode').value = l.pincode || '';
    $('#lg-phone').value = l.phone || '';
    $('#lg-email').value = l.email || '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function resetForm() {
    editing = null;
    $('#ledgerForm').reset();
    $('#ledgerFormTitle').innerHTML = `<i class="fa-solid fa-user-plus" style="color:var(--accent)"></i> Create Ledger`;
    $('#ledgerSubmit').innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Create Ledger`;
    $('#ledgerFormReset').style.display = 'none';
    App.clearInvalid($('#ledgerForm'));
  }

  async function submit(e) {
    e.preventDefault();
    App.clearInvalid($('#ledgerForm'));
    const body = {
      name: $('#lg-name').value.trim(),
      parent: $('#lg-parent').value,
      openingBalance: Number($('#lg-opening').value) || 0,
      drCr: $('#lg-drcr').value,
      gstin: $('#lg-gstin').value.trim().toUpperCase(),
      state: $('#lg-state').value,
      regType: $('#lg-regtype').value,
      address: $('#lg-address').value.trim(),
      city: $('#lg-city').value.trim(),
      pincode: $('#lg-pincode').value.trim(),
      phone: $('#lg-phone').value.trim(),
      email: $('#lg-email').value.trim(),
    };
    // client-side checks
    const bad = [];
    if (!body.name) bad.push(['#lg-name', 'Ledger name is required']);
    if (!body.parent) bad.push(['#lg-parent', 'Under group is required']);
    if (body.gstin && !App.validGSTIN(body.gstin)) bad.push(['#lg-gstin', 'Invalid GSTIN (15 chars, e.g. 27AAACS1867F1Z5)']);
    if (body.pincode && !/^\d{6}$/.test(body.pincode)) bad.push(['#lg-pincode', '6 digits']);
    if (body.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email)) bad.push(['#lg-email', 'Invalid email']);
    if (bad.length) {
      bad.forEach(([sel, msg]) => App.setInvalid($(sel), msg));
      return;
    }
    const btn = $('#ledgerSubmit');
    App.loading(btn, true, 'Saving…');
    try {
      const res = await App.apiRaw('/ledgers' + (editing ? `/${encodeURIComponent(editing)}` : ''), {
        method: editing ? 'PUT' : 'POST', body,
      });
      if (res.success === false) {
        App.applyFieldErrors($('#ledgerForm'), res.error?.errors);
        App.toast('error', 'Could not save', res.error?.message);
        return;
      }
      App.toast('success', editing ? 'Ledger updated' : 'Ledger created', `${body.name} → ${body.parent}`);
      resetForm();
      await loadLedgers();
      App.ledgers(true); // bust cache for other pages
    } catch (err) { /* toast shown by api layer */ }
    finally { App.loading(btn, false); }
  }

  async function delLedger(name) {
    const ok = await App.confirm(`Delete “${name}”?`, 'The ledger will be removed from Tally. Vouchers referencing it must be deleted first.', 'warning');
    if (!ok.isConfirmed) return;
    try {
      const res = await App.apiRaw(`/ledgers/${encodeURIComponent(name)}`, { method: 'DELETE' });
      if (res.success) {
        App.toast('success', 'Ledger deleted', name);
        await loadLedgers();
        App.ledgers(true);
      } else App.toast('error', 'Could not delete', res.error?.message);
    } catch { /* handled */ }
  }

  /* --------------------------------------------------------------- boot -- */
  document.addEventListener('DOMContentLoaded', () => {
    loadGroups();
    loadLedgers();
    $('#ledgerForm').addEventListener('submit', submit);
    $('#ledgerFormReset').addEventListener('click', resetForm);
    $('#ledgerSearch').addEventListener('input', App.debounce(renderTable, 150));
    $('#ledgerGroupFilter').addEventListener('change', renderTable);
    $('#ledgerSort').addEventListener('change', renderTable);
    $$('.tab-btn[data-view]').forEach((b) => b.addEventListener('click', () => {
      $$('.tab-btn[data-view]').forEach((x) => x.classList.toggle('active', x === b));
      $('#ledgerTableView').style.display = b.dataset.view === 'table' ? '' : 'none';
      $('#ledgerTreeView').style.display = b.dataset.view === 'tree' ? '' : 'none';
    }));
    $('#ledgerExport').addEventListener('click', () => {
      if (typeof XLSX === 'undefined') return App.toast('warning', 'Excel library not loaded');
      const rows = allLedgers.map((l) => ({
        Name: l.name, Group: l.parent, GSTIN: l.gstin, State: l.state, City: l.city,
        PIN: l.pincode, Phone: l.phone, Email: l.email,
        'Opening Balance': l.openingBalance?.amount || 0, 'Dr/Cr': l.openingBalance?.drCr || '',
      }));
      const ws = XLSX.utils.json_to_sheet(rows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Ledgers');
      XLSX.writeFile(wb, `ledgers-${new Date().toISOString().slice(0, 10)}.xlsx`);
    });
  });
})();
