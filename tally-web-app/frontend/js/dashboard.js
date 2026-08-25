/**
 * ============================================================================
 * DASHBOARD.JS — stats bar, charts, recent transactions, sync panel
 * ============================================================================
 * Data source: GET /api/dashboard/summary (one round-trip for everything).
 * Refreshes automatically when the sync engine reports Tally-side changes.
 * ============================================================================
 */
(function () {
  'use strict';
  const { $, esc, fmtINR, fmtDate, toast, vtChip, timeAgo } = App;

  const charts = {};
  let summary = null;

  /* ------------------------------------------------------------- counters -- */
  function countUp(el, target, prefix = '₹') {
    const start = performance.now();
    const from = 0;
    const dur = 700;
    function tick(t) {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = prefix + App.fmtNum(Math.round(from + (target - from) * eased));
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = fmtINR(target);
    }
    requestAnimationFrame(tick);
  }

  /* ------------------------------------------------------------ chart base -- */
  function chartTheme() {
    const dark = App.theme.get() === 'dark';
    return { grid: dark ? 'rgba(255,255,255,.07)' : 'rgba(23,32,58,.07)', text: dark ? '#9aa3c0' : '#5c6577' };
  }
  App.on('theme', () => { if (summary) drawCharts(summary); });

  function drawCharts(data) {
    if (typeof Chart === 'undefined') return;
    const th = chartTheme();
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.color = th.text;

    /* --- Sales vs Purchase grouped bars --- */
    const labels = data.months.map((m) => m.label);
    if (charts.sales) charts.sales.destroy();
    charts.sales = new Chart($('#salesChart'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Sales', data: data.months.map((m) => m.sales), backgroundColor: '#00bcd4', borderRadius: 7, maxBarThickness: 34 },
          { label: 'Purchases', data: data.months.map((m) => m.purchase), backgroundColor: '#1a237e', borderRadius: 7, maxBarThickness: 34 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { grid: { color: th.grid }, ticks: { callback: (v) => '₹' + App.fmtNum(v / 100000) + 'L' } },
          x: { grid: { display: false } },
        },
        tooltips: { callbacks: { label: (c) => `${c.dataset.label}: ${fmtINR(c.parsed.y)}` } },
      },
    });

    /* --- Expense doughnut --- */
    const exp = data.expenses.slice(0, 9);
    const palette = ['#00bcd4', '#1a237e', '#7c5cf0', '#f6a521', '#0eab6c', '#f0567a', '#0899b0', '#d92e58', '#5b3fd6'];
    if (charts.expense) charts.expense.destroy();
    charts.expense = new Chart($('#expenseChart'), {
      type: 'doughnut',
      data: {
        labels: exp.map((e) => e.name),
        datasets: [{ data: exp.map((e) => e.amount), backgroundColor: palette, borderWidth: 0, hoverOffset: 8 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '62%',
        plugins: {
          legend: { position: 'right', labels: { boxWidth: 10, boxHeight: 10, font: { size: 11 } } },
          tooltip: { callbacks: { label: (c) => ` ${c.label}: ${fmtINR(c.parsed)} (${exp[c.dataIndex].share}%)` } },
        },
      },
    });

    /* --- Cash flow lines --- */
    if (charts.cashflow) charts.cashflow.destroy();
    charts.cashflow = new Chart($('#cashflowChart'), {
      type: 'line',
      data: {
        labels: data.cashflow.map((d) => d.date.slice(0, 5)),
        datasets: [
          { label: 'Inflow', data: data.cashflow.map((d) => d.inflow), borderColor: '#0eab6c', backgroundColor: 'rgba(14,171,108,.12)', fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2 },
          { label: 'Outflow', data: data.cashflow.map((d) => d.outflow), borderColor: '#e5484d', backgroundColor: 'rgba(229,72,77,.10)', fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { boxWidth: 10, boxHeight: 10 } } },
        scales: {
          y: { grid: { color: th.grid }, ticks: { callback: (v) => '₹' + App.fmtNum(v / 1000) + 'K' } },
          x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
        },
      },
    });
  }

  /* ------------------------------------------------------------ rendering -- */
  function render(data) {
    summary = data;
    const s = data.stats;

    countUp($('#statSales'), s.salesMonth);
    $('#salesToday').textContent = fmtINR(s.salesToday);
    $('#salesMonth').textContent = fmtINR(s.salesMonth);
    $('#salesYear').textContent = fmtINR(s.salesYear);

    $('#statPurchase').textContent = fmtINR(s.purchaseMonth);
    $('#purchaseToday').textContent = fmtINR(s.purchaseToday);
    $('#purchaseMonth').textContent = fmtINR(s.purchaseMonth);
    $('#purchaseYear').textContent = fmtINR(s.purchaseYear);

    $('#statCash').textContent = fmtINR(s.cashInHand);
    const liquid = (s.cashInHand || 0) + (s.bankBalance || 0);
    $('#cashPct').textContent = liquid ? `${Math.round((s.cashInHand / liquid) * 100)}%` : '—';

    $('#statBank').textContent = fmtINR(s.bankBalance);
    $('#bankNames').textContent = (s.banks || []).map((b) => `${b.name.split('—')[0].trim()} ${fmtINR(b.balance)}`).join(' · ') || '—';

    $('#statRecv').textContent = fmtINR(s.receivables);
    $('#statPay').textContent = fmtINR(s.payables);

    const cfIn = data.cashflow.reduce((a, d) => a + d.inflow, 0);
    const cfOut = data.cashflow.reduce((a, d) => a + d.outflow, 0);
    $('#cfIn').textContent = fmtINR(cfIn);
    $('#cfOut').textContent = fmtINR(cfOut);
    $('#cfNet').textContent = fmtINR(cfIn - cfOut);

    const tbody = $('#recentTable tbody');
    if (!data.recent.length) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i class="fa-solid fa-inbox"></i>No transactions yet — create your first voucher</div></td></tr>`;
    } else {
      tbody.innerHTML = data.recent.map((v) => `
        <tr class="clk" data-vch="${esc(v.id || v.voucherNumber)}">
          <td style="white-space:nowrap">${esc(v.date)}</td>
          <td>${vtChip(v.voucherType)}</td>
          <td style="font-family:var(--mono);font-size:12px">${esc(v.voucherNumber)}</td>
          <td>${esc(v.party || '—')}</td>
          <td style="color:var(--muted);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(v.narration || '')}</td>
          <td class="num tx-amt">${fmtINR(v.amount)}</td>
        </tr>`).join('');
      tbody.querySelectorAll('tr.clk').forEach((tr) =>
        tr.addEventListener('click', () => toast('info', `Voucher ${tr.dataset.vch}`, 'Full voucher drill-down opens in the Day Book report')));
    }
    drawCharts(data);
  }

  async function load() {
    try {
      const data = await App.api('/dashboard/summary', { quiet: true });
      render(data);
    } catch (e) {
      toast('error', 'Could not load dashboard', e.message);
    }
  }

  /* ------------------------------------------------------------ sync panel -- */
  function renderSyncTiles(st) {
    const map = {
      connected: ['Connected to Tally', 'ok'], syncing: ['Sync in progress…', ''],
      demo: ['Demo data (Tally offline)', 'err'], disconnected: ['Disconnected', 'err'],
    };
    const [label, cls] = map[st.status] || ['—', ''];
    $('#syncTileStatus').textContent = label;
    $('#syncTileStatus').className = cls;
    $('#syncTileTime').textContent = st.lastSyncAt ? new Date(st.lastSyncAt).toLocaleTimeString('en-IN') : '—';
    $('#syncTileQueue').textContent = `${st.queueCount} ops`;
    $('#syncTileConflicts').textContent = st.conflictCount;
    $('#syncTileInterval').textContent = `${st.intervalSec}s`;
    $('#syncSourceBadge').textContent = `source: ${st.source || '—'}`;
  }

  function renderLogRow(e) {
    const tb = $('#syncLogTable tbody');
    const tr = document.createElement('tr');
    const icon = { Push: 'fa-arrow-up', Pull: 'fa-arrow-down', System: 'fa-gear', Conflict: 'fa-code-branch' }[e.action] || 'fa-circle';
    const stCls = e.status === 'Success' ? 'badge-success' : e.status === 'Error' ? 'badge-danger' : e.status === 'Queued' ? 'badge-warning' : 'badge-info';
    tr.innerHTML = `
      <td class="mono">${new Date(e.timestamp).toLocaleString('en-IN')}</td>
      <td><i class="fa-solid ${icon}" style="opacity:.7"></i> ${esc(e.action)}</td>
      <td>${esc(e.dataType)}</td>
      <td><span class="badge ${stCls}">${esc(e.status)}</span></td>
      <td class="details" title="${esc(e.details)}">${esc(e.details)}</td>`;
    tb.prepend(tr);
    while (tb.rows.length > 60) tb.deleteRow(-1);
  }

  async function loadLogs() {
    try {
      const logs = await App.api('/sync/logs?limit=40', { quiet: true });
      const tb = $('#syncLogTable tbody');
      tb.innerHTML = '';
      if (!logs.length) {
        tb.innerHTML = `<tr><td colspan="5" style="color:var(--muted);padding:14px">Waiting for sync activity…</td></tr>`;
        return;
      }
      logs.forEach((e) => renderLogRow(e));
    } catch { /* ignore */ }
  }

  /* ------------------------------------------------------------------ boot -- */
  document.addEventListener('DOMContentLoaded', () => {
    $('#crumbDate').textContent = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    load();
    loadLogs();
    App.sync.onChange((status, st) => { if (st) renderSyncTiles(st); });
    App.on('sync-log', renderLogRow);
    App.on('sync-manual', () => { load(); loadLogs(); });
    // Live refresh when Tally changes (keyed directly in Tally by someone else)
    let refreshTimer = null;
    App.on('tally-changed', () => {
      clearTimeout(refreshTimer);
      refreshTimer = setTimeout(load, 600);
    });
  });
})();
