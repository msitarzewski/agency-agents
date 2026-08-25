/**
 * ============================================================================
 * TALLYSYNC.JS — client half of the real-time sync engine
 * ============================================================================
 * Socket.IO events from the Node middleware:
 *   sync:status   { status: connected|syncing|demo|disconnected, lastSyncAt,
 *                   queueCount, conflictCount, error }
 *   sync:log      one journal row
 *   tally:changed { areas }  → someone keyed data in Tally → refresh page data
 *   sync:conflict { ... }    → side-by-side dialog: keep mine / keep theirs
 *   sync:queue    { count }  → offline queue badge
 *
 * If WebSocket cannot connect, a 10s REST poll keeps the badge honest.
 * ============================================================================
 */
(function () {
  'use strict';
  const { $, $$, esc, toast, timeAgo, emit } = App;

  const Sync = (App.sync = {
    status: 'connecting',
    state: null,
    listeners: [],
    onChange(fn) { this.listeners.push(fn); },
    setStatus(status, textOverride) {
      this.status = status;
      const map = {
        connected: { dot: 'green', text: 'Connected', badge: 'badge-success' },
        syncing: { dot: 'yellow', text: 'Syncing…', badge: 'badge-warning' },
        demo: { dot: 'blue', text: 'Demo Mode', badge: 'badge-info' },
        disconnected: { dot: 'red', text: 'Disconnected', badge: 'badge-danger' },
        connecting: { dot: 'yellow', text: 'Connecting…', badge: 'badge-muted' },
      };
      const c = map[status] || map.connecting;
      const text = textOverride || c.text;
      // topbar badge
      $$('#syncDot, #sideSyncDot').forEach((d) => { d.className = `sync-dot ${c.dot}`; });
      $$('#syncText, #sideSyncText').forEach((t) => (t.textContent = text));
      const badge = $('#syncBadge');
      if (badge) badge.title = App.sync.state?.error || '';
      this.listeners.forEach((fn) => fn(status, this.state));
    },
    applyState(st) {
      this.state = st;
      this.setStatus(st.status);
      // queue badge
      $$('#queueBadge').forEach((b) => {
        b.style.display = st.queueCount > 0 ? '' : 'none';
        b.textContent = `${st.queueCount} queued`;
      });
      // sidebar company + FY
      const company = $('#sideCompany');
      if (company && st.companyName) company.textContent = st.companyName;
      if (st.lastSyncAt) {
        $$('#sideLastSync').forEach((el) => (el.textContent = `Last sync: ${timeAgo(st.lastSyncAt)}`));
      }
      if (st.companyName) $$('#sideCompany').forEach((el) => (el.textContent = st.companyName));
      if (st.financialYear) $$('#sideFy').forEach((el) => (el.textContent = st.financialYear));
      this.listeners.forEach((fn) => fn(st.status, st));
    },
  });

  /* ---------------------------------------------------------- REST fallback -- */
  async function pollStatus() {
    try {
      const st = await App.api('/sync/status', { quiet: true });
      st.companyName = st.companyName || st.company; // populated by company fetch below
      Sync.applyState(st);
      if (st.conflictCount > 0) await checkConflicts();
    } catch {
      Sync.setStatus('disconnected', 'Server unreachable');
    }
  }

  /* ---------------------------------------------------------------- socket -- */
  function connectSocket() {
    if (typeof io === 'undefined') { setInterval(pollStatus, 10000); pollStatus(); return; }
    const socket = io({ path: '/socket.io', reconnectionDelayMax: 10000 });
    Sync.socket = socket;

    socket.on('sync:status', (st) => Sync.applyState(st));
    socket.on('sync:log', (entry) => emit('sync-log', entry));
    socket.on('sync:queue', ({ count, flushed }) => {
      if (flushed) toast('success', 'Offline queue flushed', `${flushed} queued entries pushed to Tally`);
      $$('#queueBadge').forEach((b) => { b.style.display = count > 0 ? '' : 'none'; b.textContent = `${count} queued`; });
    });
    socket.on('tally:changed', (payload) => {
      toast('info', 'Tally data changed', 'Refreshing with the latest entries from Tally…', 2500);
      emit('tally-changed', payload);
    });
    socket.on('sync:conflict', (conflict) => showConflictDialog(conflict));

    socket.on('connect', () => { Sync.setStatus('syncing'); socket.emit('sync:hello'); });
    socket.on('disconnect', () => Sync.setStatus('disconnected'));
  }

  /* -------------------------------------------------------- manual actions -- */
  App.manualSync = async function () {
    const btn = $('#manualSyncBtn') || $('#panelSyncNow');
    App.loading(btn, true, 'Syncing…');
    Sync.setStatus('syncing');
    try {
      const st = await App.api('/sync/manual', { method: 'POST' });
      Sync.applyState(st);
      emit('sync-manual', st);
      toast(st.status === 'connected' ? 'success' : st.status === 'demo' ? 'info' : 'warning',
        'Sync complete', st.status === 'connected' ? 'Tally is up to date' : st.status === 'demo' ? 'Tally unreachable — demo data active' : (st.error || 'Tally unreachable'));
    } catch (e) { /* toast already shown */ }
    finally { App.loading(btn, false); }
  };

  App.viewQueue = async function () {
    const [st, logs] = await Promise.all([App.api('/sync/status'), App.api('/sync/logs?limit=50')]);
    const queueRows = st.queue.length ? st.queue.map((q) => `
      <tr><td>${esc(q.label)}</td><td>${esc(q.kind)} ${esc(q.op)}</td>
      <td>${new Date(q.queuedAt).toLocaleString('en-IN')}</td><td>${q.attempts}</td>
      <td><button class="btn btn-ghost btn-sm" data-discard="${esc(q.id)}"><i class="fa-solid fa-trash"></i></button></td></tr>`).join('')
      : `<tr><td colspan="5" style="padding:18px;color:var(--muted)">Queue is empty — entries push to Tally instantly while connected.</td></tr>`;
    window.Swal && Swal.fire({
      title: `<i class="fa-solid fa-list-check"></i> Offline Queue (${st.queue.length})`,
      html: `<div class="table-wrap" style="max-height:300px;overflow:auto;text-align:left">
        <table class="data-table"><thead><tr><th>Entry</th><th>Kind</th><th>Queued</th><th>Tries</th><th></th></tr></thead>
        <tbody>${queueRows}</tbody></table></div>
        <p style="text-align:left;font-size:12px;color:var(--muted);margin-top:10px">Queued entries replay automatically the moment Tally reconnects.</p>`,
      width: 640, confirmButtonText: 'Close',
      didOpen: () => {
        document.querySelectorAll('[data-discard]').forEach((b) => b.addEventListener('click', async () => {
          await App.api(`/sync/queue/${b.dataset.discard}/discard`, { method: 'POST' });
          b.closest('tr').remove();
          toast('info', 'Queue item discarded');
          pollStatus();
        }));
      },
    });
    void logs;
  };

  /* ------------------------------------------------------- conflict dialog -- */
  let knownConflicts = new Set();
  async function checkConflicts() {
    try {
      const conflicts = await App.api('/sync/conflicts');
      conflicts.forEach((c) => { if (!knownConflicts.has(c.id)) { knownConflicts.add(c.id); showConflictDialog(c); } });
    } catch { /* ignore */ }
  }
  function showConflictDialog(c) {
    const local = c.conflict?.local || {};
    const tallyV = c.conflict?.tally || {};
    const rows = ['voucherNumber', 'party', 'date', 'amount', 'narration'].map((k) => `
      <tr><td style="font-weight:600">${k}</td>
      <td>${esc(local[k] ?? (local.items ? `${local.items.length} item(s)` : '—'))}</td>
      <td>${esc(tallyV[k] ?? (k === 'date' ? tallyV.dateDisplay : '—'))}</td></tr>`).join('');
    window.Swal && Swal.fire({
      title: '<i class="fa-solid fa-triangle-exclamation" style="color:#e8a013"></i> Edit Conflict',
      html: `<p style="text-align:left;font-size:13px">This entry was edited here <b>and</b> changed in Tally while offline. Which version should win?</p>
        <div class="table-wrap"><table class="data-table"><thead><tr><th>Field</th><th>Your version</th><th>Tally version</th></tr></thead><tbody>${rows}</tbody></table></div>`,
      width: 620, showCancelButton: true,
      confirmButtonText: 'Keep my version', cancelButtonText: 'Keep Tally’s',
      confirmButtonColor: '#1a237e', cancelButtonColor: '#0899b0',
    }).then(async (r) => {
      const resolution = r.isConfirmed ? 'mine' : 'theirs';
      await App.api(`/sync/conflicts/${c.id}/resolve`, { method: 'POST', body: { resolution } });
      knownConflicts.add(c.id);
      toast('success', 'Conflict resolved', resolution === 'mine' ? 'Your version was pushed to Tally' : 'Tally’s version kept');
      pollStatus();
    }).catch(() => {});
  }

  /* -------------------------------------------------------------- company -- */
  async function loadCompany() {
    try {
      const info = await App.api('/company/info', { quiet: true });
      $$('#sideCompany').forEach((el) => (el.textContent = info.name || '—'));
      $$('#sideFy').forEach((el) => (el.textContent = info.financialYearFrom ? `${info.financialYearFrom} → ${info.booksEndingOn || ''}` : '—'));
      App.company = info;
      emit('company', info);
    } catch { /* sidebar keeps placeholder */ }
  }

  /* ----------------------------------------------------------------- boot -- */
  document.addEventListener('DOMContentLoaded', () => {
    connectSocket();
    loadCompany();
    $('#manualSyncBtn')?.addEventListener('click', App.manualSync);
    $('#panelSyncNow')?.addEventListener('click', App.manualSync);
    $('#panelViewQueue')?.addEventListener('click', App.viewQueue);
    // safety poll every 30s even with sockets (catches socket failures)
    setInterval(pollStatus, 30000);
    setTimeout(pollStatus, 800);
  });
})();
