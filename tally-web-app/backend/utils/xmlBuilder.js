/**
 * ============================================================================
 * TALLY XML BUILDER — every XML template the app needs
 * ============================================================================
 * Tally Prime's XML API works like this:
 *
 *   PULL (read)  → <TALLYREQUEST>Export Data</TALLYREQUEST>
 *                   The REPORTNAME + STATICVARIABLES select what comes back.
 *                   SVFROMDATE/SVTODATE use YYYYMMDD.
 *
 *   PUSH (write) → <TALLYREQUEST>Import Data</TALLYREQUEST>
 *                   REQUESTDATA holds <TALLYMESSAGE> payloads.
 *                   Actions: "Create" | "Alter" | "Delete".
 *
 * LEDGER-ENTRY SIGN CONVENTION (critical!):
 *   Debit  → <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE> + NEGATIVE <AMOUNT>
 *   Credit → <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>  + POSITIVE <AMOUNT>
 *
 * NOTE: Tally's exact tag set varies slightly between builds. Every request
 * this builder emits is answered by Tally with either data or a <LINEERROR> —
 * tallyXMLService parses that response and surfaces errors verbatim.
 * ============================================================================
 */
const { escapeXml, tallyAmount, round2, toTallyDate } = require('./helpers');

/* -------------------------------------------------------------------------- */
/*  Generic wrappers                                                           */
/* -------------------------------------------------------------------------- */

/** Skeleton for an Export (read) request. */
function exportEnvelope(reportName, staticVariables = {}) {
  const vars = Object.entries(staticVariables)
    .map(([k, v]) => `            <${k}>${escapeXml(v)}</${k}>`)
    .join('\n');
  return `<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>${escapeXml(reportName)}</REPORTNAME>
        <STATICVARIABLES>
${vars}
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>`;
}

/** Skeleton for an Import (write) request carrying one TALLYMESSAGE. */
function importEnvelope(reportName, companyName, tallyMessageXml) {
  const companyVar = companyName
    ? `            <SVCURRENTCOMPANY>${escapeXml(companyName)}</SVCURRENTCOMPANY>`
    : '';
  return `<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Import Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>${escapeXml(reportName)}</REPORTNAME>
        <STATICVARIABLES>
${companyVar}
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
${tallyMessageXml}
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>`;
}

/* -------------------------------------------------------------------------- */
/*  FETCH (Export) requests                                                    */
/* -------------------------------------------------------------------------- */

/** All ledger masters (List of Accounts → Ledgers). */
const fetchLedgers = (company) =>
  exportEnvelope('List of Accounts', { SVFROMDATE: '19000101', ACCOUNTTYPE: 'Ledgers', ...(company ? { SVCURRENTCOMPANY: company } : {}) });

/** All groups. */
const fetchGroups = (company) =>
  exportEnvelope('List of Accounts', { SVFROMDATE: '19000101', ACCOUNTTYPE: 'Groups', ...(company ? { SVCURRENTCOMPANY: company } : {}) });

/** All stock items. */
const fetchStockItems = (company) =>
  exportEnvelope('Stock Summary', { SVEXPORTFORMAT: '$$SysName:XML', ...(company ? { SVCURRENTCOMPANY: company } : {}) });

/** All stock groups. */
const fetchStockGroups = (company) =>
  exportEnvelope('List of Accounts', { SVFROMDATE: '19000101', ACCOUNTTYPE: 'Stock Groups', ...(company ? { SVCURRENTCOMPANY: company } : {}) });

/** Vouchers between two dates (YYYYMMDD), optionally filtered by type. */
const fetchVouchers = (fromYmd, toYmd, voucherType = '', company = '') =>
  exportEnvelope('Voucher Register', {
    SVFROMDATE: fromYmd,
    SVTODATE: toYmd,
    ...(voucherType ? { SVVOUCHERTYPENAME: voucherType } : {}),
    ...(company ? { SVCURRENTCOMPANY: company } : {}),
  });

/** Day Book (all vouchers for a date range). */
const fetchDayBook = (fromYmd, toYmd, company = '') =>
  exportEnvelope('Day Book', {
    SVFROMDATE: fromYmd,
    SVTODATE: toYmd,
    ...(company ? { SVCURRENTCOMPANY: company } : {}),
  });

/** Period-scoped statement reports. */
const fetchTrialBalance = (fromYmd, toYmd, company = '') =>
  exportEnvelope('Trial Balance', { SVFROMDATE: fromYmd, SVTODATE: toYmd, ...(company ? { SVCURRENTCOMPANY: company } : {}) });

const fetchProfitLoss = (fromYmd, toYmd, company = '') =>
  exportEnvelope('Profit and Loss', { SVFROMDATE: fromYmd, SVTODATE: toYmd, ...(company ? { SVCURRENTCOMPANY: company } : {}) });

const fetchBalanceSheet = (asOnYmd, company = '') =>
  exportEnvelope('Balance Sheet', { SVFROMDATE: '19000101', SVTODATE: asOnYmd, ...(company ? { SVCURRENTCOMPANY: company } : {}) });

/** Receivables / Payables outstanding statements. */
const fetchOutstanding = (type /* 'receivables' | 'payables' */, asOnYmd, company = '') =>
  exportEnvelope(type === 'payables' ? 'Bills Payable' : 'Bills Receivable', {
    SVFROMDATE: '19000101',
    SVTODATE: asOnYmd,
    ...(company ? { SVCURRENTCOMPANY: company } : {}),
  });

/** Ledger account statement for one ledger between dates. */
const fetchLedgerReport = (ledgerName, fromYmd, toYmd, company = '') =>
  exportEnvelope('Ledger Vouchers', {
    LEDGERNAME: ledgerName,
    SVFROMDATE: fromYmd,
    SVTODATE: toYmd,
    ...(company ? { SVCURRENTCOMPANY: company } : {}),
  });

/** Company info (name, FY, GSTIN, address). */
const fetchCompanyInfo = (company = '') =>
  exportEnvelope('Company Info', { ...(company ? { SVCURRENTCOMPANY: company } : {}) });

/* -------------------------------------------------------------------------- */
/*  Internal helpers for building TALLYMESSAGE voucher chunks                  */
/* -------------------------------------------------------------------------- */

/**
 * One <ALLLEDGERENTRIES.LIST> block.
 * entry = { ledger, amount, debit, billAllocation? }
 */
function ledgerEntryXml(entry, indent = '          ') {
  const amount = tallyAmount(entry);
  let xml = `${indent}<ALLLEDGERENTRIES.LIST>
${indent}  <LEDGERNAME>${escapeXml(entry.ledger)}</LEDGERNAME>
${indent}  <ISDEEMEDPOSITIVE>${entry.debit ? 'Yes' : 'No'}</ISDEEMEDPOSITIVE>
${indent}  <AMOUNT>${amount}</AMOUNT>`;
  // Bill-wise allocation (New Reference) — enables outstanding tracking.
  if (entry.billAllocation) {
    xml += `
${indent}  <BILLALLOCATIONS.LIST>
${indent}    <NAME>${escapeXml(entry.billAllocation)}</NAME>
${indent}    <BILLTYPE>New Reference</BILLTYPE>
${indent}    <AMOUNT>${amount}</AMOUNT>
${indent}  </BILLALLOCATIONS.LIST>`;
  }
  xml += `\n${indent}</ALLLEDGERENTRIES.LIST>`;
  return xml;
}

/** Buyer/supplier party details block used by trading vouchers. */
function partyDetailsXml(v, indent = '      ') {
  const lines = [];
  if (v.partyAddress || v.partyCity) {
    const addr = [v.partyAddress, v.partyCity, v.partyState, v.partyPincode].filter(Boolean);
    lines.push(`${indent}<ADDRESS.LIST TYPE="String"><ADDRESS>${escapeXml(addr.join(', '))}</ADDRESS></ADDRESS.LIST>`);
  }
  if (v.partyGstin) lines.push(`${indent}<PARTYGSTIN>${escapeXml(v.partyGstin)}</PARTYGSTIN>`);
  if (v.partyState) {
    lines.push(`${indent}<STATENAME>${escapeXml(v.partyState)}</STATENAME>`);
    lines.push(`${indent}<COUNTRYNAME>India</COUNTRYNAME>`);
    lines.push(`${indent}<PLACEOFSUPPLY>${escapeXml(v.partyState)}</PLACEOFSUPPLY>`);
  }
  if (v.partyEmail) lines.push(`${indent}<EMAIL>${escapeXml(v.partyEmail)}</EMAIL>`);
  if (v.partyPhone) lines.push(`${indent}<PHONENUMBER>${escapeXml(v.partyPhone)}</PHONENUMBER>`);
  return lines.length ? lines.join('\n') : '';
}

/**
 * Inventory lines for Sales / Purchase / Credit Note / Debit Note.
 * item = { name, hsn, qty, unit, rate, discountPercent, taxableValue, gst: {cgst,sgst,igst} }
 */
function inventoryEntriesXml(items, salesSide = true, indent = '        ') {
  // For SALES the stock goes OUT → inventory amount is negative (credit);
  // for PURCHASE stock comes IN → positive.
  return items
    .filter((it) => it.name)
    .map((it) => {
      const amt = salesSide ? -round2(it.taxableValue) : round2(it.taxableValue);
      return `${indent}<INVENTORYENTRIES.LIST>
${indent}  <STOCKITEMNAME>${escapeXml(it.name)}</STOCKITEMNAME>
${indent}  <ISDEEMEDPOSITIVE>${salesSide ? 'Yes' : 'No'}</ISDEEMEDPOSITIVE>
${indent}  <RATE>${round2(it.rate)}/${escapeXml(it.unit || 'Nos')}</RATE>
${indent}  <AMOUNT>${amt}</AMOUNT>
${indent}  <QTY>${Number(it.qty) || 0} ${escapeXml(it.unit || 'Nos')}</QTY>
${indent}  <GSTDETAILS.LIST>
${indent}    <GSTHSNCODE>${escapeXml(it.hsn || '')}</GSTHSNCODE>
${indent}    <CGSTAMT>${round2(it.gst?.cgst || 0)}</CGSTAMT>
${indent}    <SGSTAMT>${round2(it.gst?.sgst || 0)}</SGSTAMT>
${indent}    <IGSTAMT>${round2(it.gst?.igst || 0)}</IGSTAMT>
${indent}  </GSTDETAILS.LIST>
${indent}  <ACCOUNTINGALLOCATIONS.LIST>
${indent}    <LEDGERNAME>${escapeXml(it.salesLedger || 'Sales Account')}</LEDGERNAME>
${indent}    <ISDEEMEDPOSITIVE>${salesSide ? 'Yes' : 'No'}</ISDEEMEDPOSITIVE>
${indent}    <AMOUNT>${amt}</AMOUNT>
${indent}  </ACCOUNTINGALLOCATIONS.LIST>
${indent}</INVENTORYENTRIES.LIST>`;
    })
    .join('\n');
}

/* -------------------------------------------------------------------------- */
/*  VOUCHER IMPORT — one generic builder for all 8 voucher types               */
/* -------------------------------------------------------------------------- */

const VOUCHER_TYPES = {
  sales: { vchType: 'Sales', class: 'Sales' },
  purchase: { vchType: 'Purchase', class: 'Purchase' },
  payment: { vchType: 'Payment', class: 'Payment' },
  receipt: { vchType: 'Receipt', class: 'Receipt' },
  contra: { vchType: 'Contra', class: 'Contra' },
  journal: { vchType: 'Journal', class: 'Journal' },
  'credit-note': { vchType: 'Credit Note', class: 'Credit Note' },
  'debit-note': { vchType: 'Debit Note', class: 'Debit Note' },
};

/**
 * Build a full Import-Data envelope for any voucher.
 *
 * v = {
 *   type: 'sales'|'purchase'|'payment'|'receipt'|'contra'|'journal'|'credit-note'|'debit-note',
 *   date, voucherNumber, narration, reference,
 *   party, partyGstin, partyState, partyAddress..., company (Tally company name),
 *   entries: [{ ledger, amount, debit, billAllocation }],   ← pre-balanced double entry
 *   items: [...]                                           ← trading vouchers only
 * }
 *
 * The service layer (tallyXMLService) computes `entries` from the friendly
 * payload posted by the browser — this builder stays purely structural.
 */
function buildVoucherXml(v) {
  const meta = VOUCHER_TYPES[v.type] || VOUCHER_TYPES.sales;
  const action = v.action || 'Create';
  const dateYmd = toTallyDate(v.date);

  const head = [
    `        <VOUCHER VCHTYPE="${escapeXml(meta.vchType)}" ACTION="${action}" OBJVIEW="Accounting Voucher View">`,
    `          <DATE>${dateYmd}</DATE>`,
    `          <EFFECTIVEDATE>${dateYmd}</EFFECTIVEDATE>`,
    `          <VOUCHERTYPENAME>${escapeXml(meta.vchType)}</VOUCHERTYPENAME>`,
    `          <VOUCHERCLASSNAME>${escapeXml(v.voucherClassName || meta.class)}</VOUCHERCLASSNAME>`,
    `          <VOUCHERNUMBER>${escapeXml(v.voucherNumber || '')}</VOUCHERNUMBER>`,
    `          <REFERENCE>${escapeXml(v.reference || '')}</REFERENCE>`,
    `          <NARRATION>${escapeXml(v.narration || '')}</NARRATION>`,
  ];
  if (v.referenceDate) head.push(`          <REFERENCEDATE>${toTallyDate(v.referenceDate)}</REFERENCEDATE>`);

  // Party ledger + GST context (trading vouchers)
  if (v.party && ['sales', 'purchase', 'credit-note', 'debit-note'].includes(v.type)) {
    head.push(`          <PARTYLEDGERNAME>${escapeXml(v.party)}</PARTYLEDGERNAME>`);
    head.push(`          <PARTYNAME>${escapeXml(v.party)}</PARTYNAME>`);
    const pd = partyDetailsXml(v);
    if (pd) head.push(pd);
    head.push(`          <BASICBUYERNAME.LIST TYPE="String"><BASICBUYERNAME>${escapeXml(v.party)}</BASICBUYERNAME></BASICBUYERNAME.LIST>`);
  }

  // Payment instrument info (cheque / NEFT / UPI) — Tally's bill-level fields
  // vary by build; the reference + narration carry the details reliably.
  if (v.instrument && v.instrument.chequeNo) {
    head.push(`          <CHEQUENUMBER>${escapeXml(v.instrument.chequeNo)}</CHEQUENUMBER>`);
    if (v.instrument.chequeDate) head.push(`          <CHEQUEDATE>${toTallyDate(v.instrument.chequeDate)}</CHEQUEDATE>`);
    if (v.instrument.bank) head.push(`          <CHEQUEBANKNAME>${escapeXml(v.instrument.bank)}</CHEQUEBANKNAME>`);
  }

  const body = [];

  // Inventory lines for trading vouchers (before ledger entries, Tally's order)
  if (v.items && v.items.length && ['sales', 'purchase', 'credit-note', 'debit-note'].includes(v.type)) {
    const salesSide = v.type === 'sales' || v.type === 'credit-note';
    body.push(inventoryEntriesXml(v.items, salesSide));
  }

  // Ledger entries (double entry, pre-balanced by the service layer)
  for (const e of v.entries || []) body.push(ledgerEntryXml(e));

  const message =
    `      <TALLYMESSAGE xmlns:UDF="TallyUDF">\n` +
    head.join('\n') + '\n' +
    body.filter(Boolean).join('\n') + '\n' +
    `        </VOUCHER>\n      </TALLYMESSAGE>`;

  return importEnvelope('Vouchers', v.company || '', message);
}

/* -------------------------------------------------------------------------- */
/*  LEDGER MASTER IMPORT                                                       */
/* -------------------------------------------------------------------------- */

/**
 * ledger = { name, parent, openingBalance, drCr ('Dr'|'Cr'), gstin, state,
 *            regType, address, city, pincode, phone, email }
 */
function buildLedgerXml(ledger, action = 'Create', oldName) {
  // Opening balance sign: Dr positive, Cr negative (Tally convention).
  let ob = Number(ledger.openingBalance || 0);
  if (ledger.drCr === 'Cr') ob = -ob;

  const rows = [];
  if (oldName && oldName !== ledger.name) rows.push(`          <NAME.LIST TYPE="String"><NAME>${escapeXml(oldName)}</NAME><NAME>${escapeXml(ledger.name)}</NAME></NAME.LIST>`);
  else rows.push(`          <NAME.LIST TYPE="String"><NAME>${escapeXml(ledger.name)}</NAME></NAME.LIST>`);
  if (ledger.parent) rows.push(`          <PARENT>${escapeXml(ledger.parent)}</PARENT>`);
  rows.push(`          <ISBILLWISEON>Yes</ISBILLWISEON>`);
  if (ob) rows.push(`          <OPENINGBALANCE>${round2(ob)}</OPENINGBALANCE>`);
  if (ledger.regType) rows.push(`          <GSTREGISTRATIONTYPE>${escapeXml(ledger.regType)}</GSTREGISTRATIONTYPE>`);
  if (ledger.gstin) rows.push(`          <PARTYGSTIN>${escapeXml(ledger.gstin)}</PARTYGSTIN>`);
  if (ledger.state) {
    rows.push(`          <STATENAME>${escapeXml(ledger.state)}</STATENAME>`);
    rows.push(`          <COUNTRYNAME>India</COUNTRYNAME>`);
  }
  rows.push(`          <MAILINGNAME.LIST TYPE="String"><MAILINGNAME>${escapeXml(ledger.name)}</MAILINGNAME></MAILINGNAME.LIST>`);
  const addr = [ledger.address, ledger.city, ledger.state, ledger.pincode].filter(Boolean).join(', ');
  if (addr) rows.push(`          <ADDRESS.LIST TYPE="String"><ADDRESS>${escapeXml(addr)}</ADDRESS></ADDRESS.LIST>`);
  if (ledger.phone) rows.push(`          <LEDGERPHONE>${escapeXml(ledger.phone)}</LEDGERPHONE>`);
  if (ledger.email) rows.push(`          <EMAIL>${escapeXml(ledger.email)}</EMAIL>`);

  const message =
    `      <TALLYMESSAGE>\n` +
    `        <LEDGER NAME="${escapeXml(oldName || ledger.name)}" ACTION="${action}">\n` +
    rows.join('\n') + '\n' +
    `        </LEDGER>\n      </TALLYMESSAGE>`;

  return importEnvelope('All Masters', ledger.company || '', message);
}

/** Delete a ledger by exact name. */
const buildLedgerDeleteXml = (name, company) =>
  importEnvelope('All Masters', company,
    `      <TALLYMESSAGE>\n        <LEDGER NAME="${escapeXml(name)}" ACTION="Delete">\n          <NAME.LIST TYPE="String"><NAME>${escapeXml(name)}</NAME></NAME.LIST>\n        </LEDGER>\n      </TALLYMESSAGE>`);

/* -------------------------------------------------------------------------- */
/*  STOCK ITEM IMPORT                                                          */
/* -------------------------------------------------------------------------- */

/** item = { name, group, unit, hsn, rate, openingQty, openingValue } */
function buildStockItemXml(item, company) {
  const rows = [
    `          <NAME.LIST TYPE="String"><NAME>${escapeXml(item.name)}</NAME></NAME.LIST>`,
  ];
  if (item.group) rows.push(`          <PARENT>${escapeXml(item.group)}</PARENT>`);
  rows.push(`          <BASEUNITS>${escapeXml(item.unit || 'Nos')}</BASEUNITS>`);
  if (item.hsn) rows.push(`          <GSTDETAILS.LIST><GSTHSNCODE>${escapeXml(item.hsn)}</GSTHSNCODE></GSTDETAILS.LIST>`);
  if (item.rate) rows.push(`          <STANDARDRATE>${round2(item.rate)}/${escapeXml(item.unit || 'Nos')}</STANDARDRATE>`);
  if (item.openingQty) {
    rows.push(`          <OPENINGBALANCE>${Number(item.openingQty) || 0} ${escapeXml(item.unit || 'Nos')}</OPENINGBALANCE>`);
    if (item.openingValue) rows.push(`          <RATE>${round2(item.openingValue / (Number(item.openingQty) || 1))}/${escapeXml(item.unit || 'Nos')}</RATE>`);
  }
  const message =
    `      <TALLYMESSAGE>\n        <STOCKITEM NAME="${escapeXml(item.name)}" ACTION="Create">\n` +
    rows.join('\n') + '\n' +
    `        </STOCKITEM>\n      </TALLYMESSAGE>`;
  return importEnvelope('All Masters', company || '', message);
}

/* -------------------------------------------------------------------------- */
/*  VOUCHER DELETE                                                             */
/* -------------------------------------------------------------------------- */

/** Delete by master-id, or by voucher number + date + type. */
function buildVoucherDeleteXml({ masterId, voucherNumber, date, vchType, company }) {
  const attrs = masterId
    ? `REMOTEID="${escapeXml(masterId)}"`
    : `VOUCHERNUMBER="${escapeXml(voucherNumber)}" VCHTYPE="${escapeXml(vchType)}" ACTION="Delete"`;
  const rows = [];
  if (!masterId) {
    rows.push(`          <DATE>${toTallyDate(date)}</DATE>`);
    rows.push(`          <VOUCHERTYPENAME>${escapeXml(vchType)}</VOUCHERTYPENAME>`);
    rows.push(`          <VOUCHERNUMBER>${escapeXml(voucherNumber)}</VOUCHERNUMBER>`);
  }
  return importEnvelope('Vouchers', company || '',
    `      <TALLYMESSAGE>\n        <VOUCHER ${attrs} ACTION="Delete">\n${rows.join('\n')}\n        </VOUCHER>\n      </TALLYMESSAGE>`);
}

module.exports = {
  exportEnvelope, importEnvelope,
  fetchLedgers, fetchGroups, fetchStockItems, fetchStockGroups, fetchVouchers,
  fetchDayBook, fetchTrialBalance, fetchProfitLoss, fetchBalanceSheet,
  fetchOutstanding, fetchLedgerReport, fetchCompanyInfo,
  ledgerEntryXml, buildVoucherXml, buildLedgerXml, buildLedgerDeleteXml,
  buildStockItemXml, buildVoucherDeleteXml, VOUCHER_TYPES,
};
