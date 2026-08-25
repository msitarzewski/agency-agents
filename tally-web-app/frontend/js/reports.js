/**
 * ============================================================================
 * REPORTS.JS — Trial Balance, P&L, Balance Sheet, Day Book, Ledger,
 *              Outstanding, GST (GSTR-1 / GSTR-3B) + exports
 * ============================================================================
 * Each report renders into #reportBody. Exports:
 *   PDF   → html2pdf (client-side, pixel-perfect print bundle)
 *   Excel → SheetJS with the report's raw rows
 *   Print → window.print() with print CSS
 * ============================================================================
 */
(function () {
  'use strict';
  const { $, $$, esc, fmtINR, fmtNum, toast } = App;

  let current = 'trial-balance';
  let lastData = null;
  let lastTitle = '';

  const fyRange = () => {
    const now = new Date();
    const y = now.getMonth() + 1 >= 4 ? now.getFullYear() : now.getFullYear() - 1;
    return { from: `${y}-04-01`, to: new Date().toISOString().slice(0, 10) };
  };

  function qs() { return {
    from: val('#reportFrom') || fyRange().from,
    to: val('#reportTo') || fyRange().to,
  }; }
  const val = (id) => ($(id)?.value || '');
  const dmy = (iso) => App.fmtDate(iso);

  function setTitle(t) {
    lastTitle = t;
    $('#reportTitle')?.remove();
  }

  /* ------------------------------------------------------------- fetchers -- */
  const ENDPOINTS = {
    'trial-balance': (p) => `/reports/trial-balance?from=${p.from}&to=${p.to}`,
    'profit-loss': (p) => `/reports/profit-loss?from=${p.from}&to=${p.to}`,
    'balance-sheet': (p) => `/reports/balance-sheet?to=${p.to}`,
    daybook: (p) => `/reports/daybook?from=${p.from}&to=${p.to}&limit=500`,
    ledger: (p) => `/reports/ledger/${encodeURIComponent(val('#reportLedger'))}?from=${p.from}&to=${p.to}`,
    outstanding: (p) => `/reports/outstanding?to=${p.to}`,
    gst: (p) => `/reports/gst-summary?from=${p.from}&to=${p.to}`,
  };

  /* ------------------------------------------------------------- renderers -- */
  function head(title, sub) {
    return `<div class="report-title-row no-print" style="display:none"></div>
      <div class="report-title-row"><h3>${title}</h3><span class="period">${sub}</span></div>`;
  }

  const R = {
    'trial-balance': (d) => {
      const rows = d.rows.map((r) => `<tr><td>${esc(r.name)}</td><td><span class="badge badge-muted">${esc(r.group || '')}</span></td>
        <td class="num">${r.debit ? fmtNum(r.debit) : ''}</td><td class="num">${r.credit ? fmtNum(r.credit) : ''}</td></tr>`).join('');
      return `${head('<i class="fa-solid fa-scale-balanced" style="color:var(--accent)"></i> Trial Balance', `as on ${dmy(val('#reportTo'))}`)}
        <div class="table-wrap"><table class="data-table"><thead><tr><th>Ledger</th><th>Group</th><th class="num">Debit</th><th class="num">Credit</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr class="row-total"><td colspan="2">Total</td><td class="num">${fmtNum(d.totalDebit)}</td><td class="num">${fmtNum(d.totalCredit)}</td></tr></tfoot></table></div>
        <p style="margin-top:10px">${d.balanced
          ? '<span class="badge badge-success"><i class="fa-solid fa-check"></i> Balanced</span>'
          : '<span class="badge badge-danger">Difference: ' + fmtINR(Math.abs(d.totalDebit - d.totalCredit)) + '</span>'}</p>`;
    },

    'profit-loss': (d) => `${head('<i class="fa-solid fa-chart-line" style="color:var(--accent)"></i> Profit &amp; Loss Statement', `${d.from} → ${d.to}`)}
      <div class="statement"><div class="statement-cols">
        <div>
          <h4>Trading Account</h4>
          <div class="srow"><span>To Purchases</span><span class="amt">${fmtNum(d.purchases)}</span></div>
          <div class="srow"><span>To Direct Expenses</span><span class="amt">${fmtNum(d.directExpenses)}</span></div>
          ${(d.directExpenseDetail || []).map((x) => `<div class="srow" style="padding-left:18px;color:var(--muted)"><span>↳ ${esc(x.name)}</span><span class="amt">${fmtNum(x.amount)}</span></div>`).join('')}
          <div class="srow subtotal"><span>Gross Profit c/f</span><span class="amt">${fmtNum(d.grossProfit)}</span></div>
        </div>
        <div>
          <h4>&nbsp;</h4>
          <div class="srow"><span>By Sales</span><span class="amt">${fmtNum(d.sales)}</span></div>
          <div class="srow subtotal"><span>Gross Profit b/f</span><span class="amt">${fmtNum(d.grossProfit)}</span></div>
          <h4 style="margin-top:18px">Profit &amp; Loss Account</h4>
          <div class="srow"><span>To Indirect Expenses</span><span class="amt">${fmtNum(d.indirectExpenses)}</span></div>
          ${(d.indirectExpenseDetail || []).map((x) => `<div class="srow" style="padding-left:18px;color:var(--muted)"><span>↳ ${esc(x.name)}</span><span class="amt">${fmtNum(x.amount)}</span></div>`).join('')}
          <div class="srow"><span>By Indirect Incomes</span><span class="amt">${fmtNum(d.indirectIncomes)}</span></div>
          ${(d.indirectIncomeDetail || []).map((x) => `<div class="srow" style="padding-left:18px;color:var(--muted)"><span>↳ ${esc(x.name)}</span><span class="amt">${fmtNum(x.amount)}</span></div>`).join('')}
        </div>
      </div>
      <div class="srow total" style="margin-top:16px;max-width:420px;margin-left:auto">
        <span>Net ${d.netProfit >= 0 ? 'Profit' : 'Loss'}</span><span class="amt" style="color:${d.netProfit >= 0 ? 'var(--success)' : 'var(--danger)'}">${fmtINR(d.netProfit)}</span></div></div>`,

    'balance-sheet': (d) => {
      const side = (rows) => {
        const groups = {};
        rows.forEach((r) => { (groups[r.group] = groups[r.group] || []).push(r); });
        return Object.entries(groups).map(([g, items]) => `
          <div class="sgroup">${esc(g)}</div>
          ${items.map((r) => `<div class="srow"><span>${esc(r.name)}</span><span class="amt">${fmtNum(r.amount)}</span></div>`).join('')}
          <div class="srow" style="color:var(--muted);font-size:12px"><span>${esc(g)} total</span><span class="amt">${fmtNum(items.reduce((s, r) => s + r.amount, 0))}</span></div>`).join('');
      };
      return `${head('<i class="fa-solid fa-table-columns" style="color:var(--accent)"></i> Balance Sheet', `as on ${dmy(val('#reportTo'))}`)}
        <div class="statement"><div class="statement-cols">
          <div><h4>Liabilities</h4>${side(d.liabilities)}
            <div class="srow"><span>Profit &amp; Loss A/c</span><span class="amt">${fmtNum(d.netProfit)}</span></div>
            <div class="srow total"><span>Total Liabilities + P&amp;L</span><span class="amt">${fmtNum(d.totalLiabilities + d.netProfit)}</span></div></div>
          <div><h4>Assets</h4>${side(d.assets)}
            <div class="srow total"><span>Total Assets</span><span class="amt">${fmtNum(d.totalAssets)}</span></div></div>
        </div>
        ${Math.abs(d.differenceInOpeningBalances) > 1 ? `<p class="badge badge-warning">Difference in opening balances: ${fmtINR(d.differenceInOpeningBalances)}</p>` : '<p class="badge badge-success"><i class="fa-solid fa-check"></i> Balanced</p>'}</div>`;
    },

    daybook: (d) => {
      const rows = d.map((v) => `<tr><td>${esc(v.dateDisplay || App.fmtDate(v.date))}</td><td>${App.vtChip(v.voucherType)}</td>
        <td style="font-family:var(--mono);font-size:12px">${esc(v.voucherNumber)}</td><td>${esc(v.party || '—')}</td>
        <td style="color:var(--muted)">${esc(v.narration || '')}</td><td class="num">${fmtNum(v.amount)}</td></tr>`).join('');
      return `${head('<i class="fa-solid fa-book-open" style="color:var(--accent)"></i> Day Book', `${dmy(val('#reportFrom'))} → ${dmy(val('#reportTo'))} · ${d.length} vouchers`)}
        <div class="table-wrap" style="max-height:560px"><table class="data-table">
        <thead><tr><th>Date</th><th>Type</th><th>Vch No.</th><th>Party</th><th>Narration</th><th class="num">Amount</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6"><div class="empty-state"><i class="fa-solid fa-inbox"></i>No vouchers in this period</div></td></tr>'}</tbody></table></div>`;
    },

    ledger: (d) => {
      const rows = (d.rows || []).map((r) => `<tr><td>${esc(r.dateDisplay || App.fmtDate(r.date))}</td><td>${App.vtChip(r.voucherType)}</td>
        <td style="font-family:var(--mono);font-size:12px">${esc(r.voucherNumber)}</td>
        <td class="num">${r.debit ? fmtNum(r.debit) : ''}</td><td class="num">${r.credit ? fmtNum(r.credit) : ''}</td>
        <td style="color:var(--muted)">${esc(r.narration || '')}</td></tr>`).join('');
      return `${head(`<i class="fa-solid fa-file-lines" style="color:var(--accent)"></i> Ledger: ${esc(d.ledger)}`, `${esc(d.group || '')} · ${d.from || dmy(val('#reportFrom'))} → ${d.to || dmy(val('#reportTo'))}`)}
        <div class="gst-tiles" style="margin-bottom:14px">
          <div class="gst-tile"><div class="l">Opening</div><div class="v">${fmtNum(d.opening)}</div></div>
          <div class="gst-tile"><div class="l">Total Dr</div><div class="v">${fmtNum(d.totalDr)}</div></div>
          <div class="gst-tile"><div class="l">Total Cr</div><div class="v">${fmtNum(d.totalCr)}</div></div>
          <div class="gst-tile"><div class="l">Closing</div><div class="v">${fmtNum(Math.abs(d.closing))} ${d.closingDrCr}</div></div>
        </div>
        ${d.gstin ? `<p style="font-size:12px;color:var(--muted)">GSTIN ${esc(d.gstin)} · ${esc(d.state || '')}</p>` : ''}
        <div class="table-wrap" style="max-height:520px"><table class="data-table">
        <thead><tr><th>Date</th><th>Type</th><th>Vch No.</th><th class="num">Debit</th><th class="num">Credit</th><th>Narration</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6"><div class="empty-state"><i class="fa-solid fa-inbox"></i>No transactions in this period</div></td></tr>'}</tbody></table></div>`;
    },

    outstanding: (d) => `${head('<i class="fa-solid fa-hourglass-half" style="color:var(--accent)"></i> Outstanding', `as on ${dmy(val('#reportTo'))}`)}
      <div class="gst-tiles">
        <div class="gst-tile"><div class="l">Receivables</div><div class="v" style="color:var(--success)">${fmtNum(d.totalReceivables)}</div></div>
        <div class="gst-tile"><div class="l">Payables</div><div class="v" style="color:var(--danger)">${fmtNum(d.totalPayables)}</div></div>
        <div class="gst-tile"><div class="l">Net Position</div><div class="v">${fmtNum(d.totalReceivables - d.totalPayables)}</div></div>
      </div>
      <div class="statement-cols">
        <div><h4>Receivables (Sundry Debtors)</h4>
          ${d.receivables.map((r) => `<div class="srow"><span>${esc(r.name)} <small style="color:var(--muted)">${esc(r.gstin || '')}</small></span><span class="amt">${fmtNum(r.amount)}</span></div>`).join('') || '<p style="color:var(--muted)">Nothing pending 🎉</p>'}
          <div class="srow total"><span>Total</span><span class="amt">${fmtNum(d.totalReceivables)}</span></div></div>
        <div><h4>Payables (Sundry Creditors)</h4>
          ${d.payables.map((r) => `<div class="srow"><span>${esc(r.name)} <small style="color:var(--muted)">${esc(r.gstin || '')}</small></span><span class="amt">${fmtNum(r.amount)}</span></div>`).join('') || '<p style="color:var(--muted)">Nothing pending 🎉</p>'}
          <div class="srow total"><span>Total</span><span class="amt">${fmtNum(d.totalPayables)}</span></div></div>
      </div>`,

    gst: (d) => {
      const which = val('#gstKind') || 'gstr1';
      const src = which === 'gstr1' ? d.gstr1 : d.gstr3b;
      const t = src.totals;
      const rows = src.invoices.map((r) => `<tr><td>${esc(r.date)}</td><td style="font-family:var(--mono);font-size:12px">${esc(r.number)}</td>
        <td>${esc(r.party)}</td><td style="font-family:var(--mono);font-size:11.5px">${esc(r.gstin || '—')}</td>
        <td class="num">${fmtNum(r.taxable)}</td><td class="num">${fmtNum(r.cgst)}</td><td class="num">${fmtNum(r.sgst)}</td><td class="num">${fmtNum(r.igst)}</td>
        <td class="num">${fmtNum(r.total)}</td></tr>`).join('');
      return `${head(`<i class="fa-solid fa-percent" style="color:var(--accent)"></i> ${which === 'gstr1' ? 'GSTR-1 — Outward Supplies' : 'GSTR-3B Summary — Inward Supplies'}`, `${d.from} → ${d.to}`)}
        <div class="gst-tiles">
          <div class="gst-tile"><div class="l">Taxable Value</div><div class="v">${fmtNum(t.taxable)}</div></div>
          <div class="gst-tile"><div class="l">CGST</div><div class="v">${fmtNum(t.cgst)}</div></div>
          <div class="gst-tile"><div class="l">SGST</div><div class="v">${fmtNum(t.sgst)}</div></div>
          <div class="gst-tile"><div class="l">IGST</div><div class="v">${fmtNum(t.igst)}</div></div>
          <div class="gst-tile"><div class="l">Total Tax</div><div class="v">${fmtNum(t.cgst + t.sgst + t.igst)}</div></div>
        </div>
        <div class="table-wrap" style="max-height:460px"><table class="data-table">
        <thead><tr><th>Date</th><th>Invoice</th><th>Party</th><th>GSTIN</th><th class="num">Taxable</th>
        <th class="num">CGST</th><th class="num">SGST</th><th class="num">IGST</th><th class="num">Invoice Value</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="9"><div class="empty-state"><i class="fa-solid fa-inbox"></i>No supplies in this period</div></td></tr>'}</tbody></table></div>`;
    },
  };

  /* ----------------------------------------------------------------- run -- */
  async function run() {
    if (current === 'ledger' && !val('#reportLedger')) {
      return toast('warning', 'Pick a ledger', 'Choose the ledger account to run the statement');
    }
    const body = $('#reportBody');
    body.innerHTML = `<div class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i>Fetching from Tally…</div>`;
    try {
      const data = await App.api(ENDPOINTS[current](qs()));
      lastData = data;
      body.innerHTML = R[current](data);
    } catch (e) {
      body.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation" style="color:var(--danger)"></i>${esc(e.message)}</div>`;
    }
  }

  /* -------------------------------------------------------------- exports -- */
  function exportPdf() {
    if (typeof html2pdf === 'undefined') return toast('warning', 'PDF library not loaded');
    const el = document.createElement('div');
    el.style.background = '#fff';
    el.style.color = '#111';
    el.style.padding = '24px';
    el.innerHTML = `<h2 style="font-family:Poppins,Inter,sans-serif;color:#1a237e;margin:0">${lastTitle}</h2>
      <div style="margin:12px 0 4px;color:#555">${val('#reportFrom') ? dmy(val('#reportFrom')) + ' → ' : ''}${dmy(val('#reportTo'))} · Generated ${new Date().toLocaleString('en-IN')}</div><hr>
      <div class="pdf-body">${$('#reportBody').innerHTML}</div>`;
    // clone styles for tables
    document.body.appendChild(el);
    html2pdf().set({
      margin: [10, 8], filename: `${current}-${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.96 },
      html2canvas: { scale: 2, backgroundColor: '#ffffff', useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: current === 'balance-sheet' || current === 'profit-loss' ? 'portrait' : 'landscape' },
    }).from(el).save().then(() => el.remove());
  }

  function exportExcel() {
    if (typeof XLSX === 'undefined') return toast('warning', 'Excel library not loaded');
    const wb = XLSX.utils.book_new();
    const add = (name, rows, cols) => {
      const ws = XLSX.utils.json_to_sheet(rows, { header: cols });
      XLSX.utils.book_append_sheet(wb, ws, name.slice(0, 30));
    };
    if (current === 'trial-balance' && lastData) {
      add('Trial Balance', lastData.rows.map((r) => ({ Ledger: r.name, Group: r.group, Debit: r.debit, Credit: r.credit })),
        ['Ledger', 'Group', 'Debit', 'Credit']);
    } else if (current === 'daybook' && lastData) {
      add('Day Book', lastData.map((v) => ({ Date: v.dateDisplay, Type: v.voucherType, Voucher: v.voucherNumber, Party: v.party, Amount: v.amount, Narration: v.narration })));
    } else if (current === 'ledger' && lastData) {
      add('Ledger', (lastData.rows || []).map((r) => ({ Date: r.dateDisplay, Type: r.voucherType, Voucher: r.voucherNumber, Debit: r.debit, Credit: r.credit, Narration: r.narration })));
    } else if (current === 'outstanding' && lastData) {
      add('Receivables', lastData.receivables, ['name', 'amount', 'gstin', 'state']);
      add('Payables', lastData.payables, ['name', 'amount', 'gstin', 'state']);
    } else if (current === 'gst' && lastData) {
      add('Outward', lastData.gstr1.invoices); add('Inward', lastData.gstr3b.supplies);
    } else if (current === 'profit-loss' && lastData) {
      add('P&L', [
        { Particulars: 'Sales', Amount: lastData.sales },
        { Particulars: 'Purchases', Amount: -lastData.purchases },
        { Particulars: 'Direct Expenses', Amount: -lastData.directExpenses },
        { Particulars: 'Gross Profit', Amount: lastData.grossProfit },
        { Particulars: 'Indirect Incomes', Amount: lastData.indirectIncomes },
        { Particulars: 'Indirect Expenses', Amount: -lastData.indirectExpenses },
        { Particulars: 'Net Profit', Amount: lastData.netProfit },
      ]);
    } else if (current === 'balance-sheet' && lastData) {
      add('Assets', lastData.assets, ['group', 'name', 'amount']);
      add('Liabilities', lastData.liabilities, ['group', 'name', 'amount']);
    } else {
      // generic: scrape table
      const rows = Array.from($('#reportBody table tr')).map((tr) =>
        Array.from(tr.children).map((td) => td.textContent.trim()));
      const ws = XLSX.utils.aoa_to_sheet(rows);
      XLSX.utils.book_append_sheet(wb, ws, 'Report');
    }
    XLSX.writeFile(wb, `${current}-${new Date().toISOString().slice(0, 10)}.xlsx`);
    toast('success', 'Excel exported');
  }

  /* ----------------------------------------------------------------- boot -- */
  document.addEventListener('DOMContentLoaded', async () => {
    const fy = fyRange();
    $('#reportFrom').value = fy.from;
    $('#reportTo').value = fy.to;

    // nav
    $$('.report-nav-btn').forEach((b) => b.addEventListener('click', () => {
      $$('.report-nav-btn').forEach((x) => x.classList.toggle('active', x === b));
      current = b.dataset.report;
      $('#ledgerPickerField').style.display = current === 'ledger' ? '' : 'none';
      $('#gstKindField').style.display = current === 'gst' ? '' : 'none';
    }));

    // deep links: ?report=ledger&ledger=X
    const params = new URLSearchParams(location.search);
    const rep = params.get('report');
    if (rep) {
      const btn = document.querySelector(`.report-nav-btn[data-report="${rep}"]`);
      if (btn) btn.click();
      if (rep === 'ledger' && params.get('ledger')) {
        $('#reportLedger').value = params.get('ledger');
        setTimeout(run, 400);
      } else if (btn) setTimeout(run, 100);
    } else {
      run();
    }

    // ledger picker autocomplete
    App.autocomplete($('#reportLedger'), {
      source: async (q) => {
        const all = await App.ledgers();
        const lq = (q || '').toLowerCase();
        return all.filter((l) => l.name.toLowerCase().includes(lq)).slice(0, 20)
          .map((l) => ({ label: l.name, sub: l.parent, value: l.name }));
      },
      select: (it) => { $('#reportLedger').value = it.value; },
    });

    $('#reportRun').addEventListener('click', run);
    $('#gstKind').addEventListener('change', () => { if (lastData) $('#reportBody').innerHTML = R[current](lastData); });
    $('#reportPdf').addEventListener('click', exportPdf);
    $('#reportExcel').addEventListener('click', exportExcel);
    $('#reportPrint').addEventListener('click', () => window.print());
  });
})();
