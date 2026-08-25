/**
 * ============================================================================
 * TALLY XML SERVICE — the integration core
 * ============================================================================
 * Responsibilities:
 *   1. HTTP transport  → POST raw XML envelopes to Tally's XML server (:9000)
 *   2. Response parsing→ xml2js + defensive deep-search extractors
 *   3. Business API    → ledgers / vouchers / stock / reports / company
 *   4. Fallback logic  → demo dataset when Tally is unreachable & demoMode=auto
 *
 * TALLY RESPONSE FACTS the parser relies on:
 *   • Success (import): response contains <CREATED>n</CREATED>,
 *     <ALTERED>n</ALTERED>, <DELETED>n</DELETED>
 *   • Failure (import): a <LINEERROR> node carries the human-readable reason
 *     (e.g. "'Ledger X' does not exist") — we surface it verbatim.
 *   • Exports return nested <TALLYMESSAGE> objects (LEDGER, VOUCHER, ...).
 *     Node layout varies slightly across Tally builds, so every extractor
 *     uses a recursive deep-collect instead of fixed paths.
 * ============================================================================
 */
const axios = require('axios');
const xml2js = require('xml2js');
const { getTallyConfig } = require('../config/tallyConfig');
const xmlb = require('../utils/xmlBuilder');
const {
  toTallyDate, todayTally, fyStart, fyEnd, round2, computeGst, fmtYmd, tallyToDisplay,
} = require('../utils/helpers');
const demo = require('./demoStore');

/* -------------------------------------------------------------------------- */
/*  Transport                                                                  */
/* -------------------------------------------------------------------------- */

const state = {
  lastConnectedAt: null,
  lastError: null,
  demoActive: false, // true while we are serving demo data (auto fallback)
};

/** Mark connection-type errors so the fallback layer can detect them. */
function tagUnreachable(err) {
  err.tallyUnreachable = true;
  return err;
}

/** POST an XML envelope to Tally. Returns the raw XML string body. */
async function postXml(xml) {
  const cfg = getTallyConfig();
  try {
    const res = await axios.post(cfg.baseUrl, xml, {
      headers: { 'Content-Type': 'text/xml;charset=utf-8' },
      timeout: cfg.timeoutMs,
      // Tally never validates content-type; keep response as text.
      responseType: 'text',
      transformResponse: [(d) => d],
    });
    state.lastConnectedAt = new Date();
    state.lastError = null;
    state.demoActive = false;
    return res.data;
  } catch (err) {
    const msg = err.code || err.message;
    if (err.code === 'ECONNREFUSED' || err.code === 'ETIMEDOUT' || err.code === 'ENOTFOUND' ||
        err.code === 'ECONNABORTED' || err.message?.includes('timeout') || !err.response) {
      state.lastError = `Cannot reach Tally at ${cfg.baseUrl} (${msg})`;
      throw tagUnreachable(err);
    }
    state.lastError = err.message;
    throw err;
  }
}

const parser = new xml2js.Parser({ explicitArray: false, ignoreAttrs: false, trim: true });

async function parseXml(xmlText) {
  try {
    return await parser.parseStringPromise(xmlText);
  } catch {
    throw new Error('Tally returned malformed XML (is another service on that port?)');
  }
}

/* -------------------------------------------------------------------------- */
/*  Defensive extractors (deep search — survives layout differences)           */
/* -------------------------------------------------------------------------- */

/** Recursively collect every value stored under `tagName`. */
function deepCollect(node, tagName, out = []) {
  if (!node || typeof node !== 'object') return out;
  if (Array.isArray(node)) { node.forEach((n) => deepCollect(n, tagName, out)); return out; }
  for (const [k, v] of Object.entries(node)) {
    if (k === tagName) {
      if (Array.isArray(v)) v.forEach((x) => out.push(x)); else out.push(v);
    }
    deepCollect(v, tagName, out);
  }
  return out;
}

const text = (v) => (v == null ? '' : typeof v === 'object' ? (v._ || '') : String(v));

/** Find the first <LINEERROR> anywhere in a parsed Tally response. */
function findLineError(parsed) {
  const errs = deepCollect(parsed, 'LINEERROR').map(text).filter(Boolean);
  return errs.length ? errs.join(' | ') : null;
}

/** Import-response outcome: {created, altered, deleted, error}. */
function importOutcome(parsed) {
  const lineErr = findLineError(parsed);
  const num = (tag) => {
    const v = deepCollect(parsed, tag).map(text).find((x) => /^\d+$/.test(x));
    return v ? parseInt(v, 10) : 0;
  };
  return {
    created: num('CREATED'),
    altered: num('ALTERED'),
    deleted: num('DELETED'),
    error: num('EXCEPTIONS') ? 'Tally reported an exception' : null,
    lineError: lineErr,
  };
}

/** Sign convention back from Tally: ISDEEMEDPOSITIVE=Yes + negative = Debit. */
function entryFromNode(n) {
  const ledger = text(n.LEDGERNAME);
  const amount = Math.abs(Number(text(n.AMOUNT)) || 0);
  const deemedPositive = String(text(n.ISDEEMEDPOSITIVE)).toLowerCase() === 'yes';
  const negative = Number(text(n.AMOUNT)) < 0;
  return { ledger, amount: round2(amount), debit: deemedPositive || negative, billAllocation: text(n.BILLNAME) || null };
}

/* -------------------------------------------------------------------------- */
/*  Fallback wrapper                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Run `realFn` against Tally; if Tally is unreachable and demoMode='auto',
 * transparently serve `demoFn` instead and flag it on the result.
 * `forceReal` (queue replay from syncService) disables the fallback so an
 * offline-queued write NEVER silently lands in the demo dataset.
 */
async function withFallback(label, realFn, demoFn, { forceReal = false } = {}) {
  const cfg = getTallyConfig();
  if (cfg.demoMode === 'always' && !forceReal) {
    return { data: await demoFn(), source: 'demo' };
  }
  try {
    const data = await realFn();
    return { data, source: 'tally' };
  } catch (err) {
    const canFallback = !forceReal && cfg.demoMode === 'auto' && err.tallyUnreachable;
    if (!canFallback) throw err;
    state.demoActive = true;
    state.lastError = `${label}: ${err.message || err.code} — serving demo data`;
    return { data: await demoFn(), source: 'demo' };
  }
}

/* -------------------------------------------------------------------------- */
/*  Connection & company                                                       */
/* -------------------------------------------------------------------------- */

/** Cheap liveness probe — fetch Company Info. */
async function testConnection() {
  const cfg = getTallyConfig();
  const body = await postXml(xmlb.fetchCompanyInfo(cfg.companyName));
  const parsed = await parseXml(body);
  const names = deepCollect(parsed, 'NAME').map(text).filter(Boolean);
  const firms = deepCollect(parsed, 'COMPANYNAME').map(text).filter(Boolean);
  return {
    connected: true,
    baseUrl: cfg.baseUrl,
    companies: [...new Set([...firms, ...names])].slice(0, 10),
  };
}

async function getCompanyInfo() {
  return withFallback('company info', async () => {
    const cfg = getTallyConfig();
    const parsed = await parseXml(await postXml(xmlb.fetchCompanyInfo(cfg.companyName)));
    const get1 = (tag) => text(deepCollect(parsed, tag)[0]);
    const info = {
      name: get1('COMPANYNAME') || cfg.companyName,
      address: get1('ADDRESS'),
      city: get1('CITY') || get1('ADDRESS.LIST'),
      state: get1('STATENAME'),
      gstin: get1('PARTYGSTIN') || get1('GSTNUMBER'),
      phone: get1('PHONENUMBER'),
      email: get1('EMAIL'),
      financialYearFrom: get1('FINANCIALYEARFROM') || get1('BEGINDATE'),
      booksEndingOn: get1('BOOKSENDINGFROM') || get1('ENDDATE'),
    };
    if (!info.name) throw new Error('Tally reachable but company info not recognised');
    return info;
  }, () => demo.companyInfo());
}

/* -------------------------------------------------------------------------- */
/*  Masters — ledgers, groups, stock                                           */
/* -------------------------------------------------------------------------- */

async function getLedgers() {
  return withFallback('ledgers', async () => {
    const cfg = getTallyConfig();
    const parsed = await parseXml(await postXml(xmlb.fetchLedgers(cfg.companyName)));
    // Preferred: full LEDGER master objects.
    const ledgers = deepCollect(parsed, 'LEDGER').map((n) => {
      const ob = Number(text(n.OPENINGBALANCE)) || 0;
      return {
        name: text(n.NAME?._ ?? n.NAME) || text(n.$?.NAME) || text(n.LEDGERNAME),
        parent: text(n.PARENT),
        openingBalance: { amount: Math.abs(ob), drCr: ob >= 0 ? 'Dr' : 'Cr' },
        gstin: text(n.PARTYGSTIN) || text(n.GSTNUMBER),
        state: text(n.STATENAME),
        regType: text(n.GSTREGISTRATIONTYPE),
        address: [text(n.ADDRESS)].filter(Boolean).join(', '),
        city: text(n.CITY),
        pincode: text(n.PINCODE),
        phone: text(n.PHONENUMBER) || text(n.LEDGERPHONE),
        email: text(n.EMAIL) || text(n['E-MAIL']),
      };
    }).filter((l) => l.name);
    if (ledgers.length) return ledgers;
    // Fallback: flat "List of Accounts" table rows (name/parent tuples).
    const names = deepCollect(parsed, 'ACCOUNTNAME').map(text).filter(Boolean);
    const parents = deepCollect(parsed, 'PARENT').map(text);
    if (names.length) {
      return names.map((nm, i) => ({
        name: nm, parent: parents[i] || '',
        openingBalance: { amount: 0, drCr: 'Dr' },
        gstin: '', state: '', regType: '', address: '', city: '', pincode: '', phone: '', email: '',
      }));
    }
    throw new Error('Tally returned no ledgers (check that a company is open)');
  }, () => demo.listLedgers());
}

async function getLedger(name) {
  return withFallback('ledger detail', async () => {
    const all = (await getLedgers()).data;
    const hit = all.find((l) => l.name.toLowerCase() === name.toLowerCase());
    if (!hit) throw Object.assign(new Error(`Ledger "${name}" not found`), { statusCode: 404 });
    return hit;
  }, () => {
    const hit = demo.findLedger(name);
    if (!hit) throw Object.assign(new Error(`Ledger "${name}" not found`), { statusCode: 404 });
    return hit;
  });
}

async function getGroups() {
  return withFallback('groups', async () => {
    const cfg = getTallyConfig();
    const parsed = await parseXml(await postXml(xmlb.fetchGroups(cfg.companyName)));
    const names = deepCollect(parsed, 'GROUPNAME').map(text).filter(Boolean);
    const fromLedgerNodes = deepCollect(parsed, 'GROUP').map((n) => ({
      name: text(n.$?.NAME || n.NAME), parent: text(n.PARENT),
      nature: text(n.NATUREOFGROUP) || text(n.RESERVEDNAME),
    })).filter((g) => g.name);
    if (fromLedgerNodes.length) return fromLedgerNodes;
    if (names.length) return names.map((nm) => ({ name: nm, parent: 'Primary', nature: '' }));
    throw new Error('No groups returned from Tally');
  }, () => demo.listGroups());
}

async function getStockItems() {
  return withFallback('stock items', async () => {
    const cfg = getTallyConfig();
    const parsed = await parseXml(await postXml(xmlb.fetchStockItems(cfg.companyName)));
    const items = deepCollect(parsed, 'STOCKITEM').map((n) => {
      const closing = Number(text(n.CLOSINGBALANCE)) || 0;
      const rate = Number(text(n.CLOSINGRATE)) || 0;
      return {
        name: text(n.$?.NAME || n.NAME),
        group: text(n.PARENT),
        unit: text(n.BASEUNITS),
        hsn: text(n.GSTHSNCODE) || text(n.HSNCODE),
        rate: round2(rate),
        closingBalance: closing,
        closingValue: round2(Math.abs(closing) * rate),
      };
    }).filter((i) => i.name);
    if (items.length) return items;
    throw new Error('No stock items returned from Tally');
  }, () => demo.listStockItems());
}

async function getStockGroups() {
  return withFallback('stock groups', async () => {
    const cfg = getTallyConfig();
    const parsed = await parseXml(await postXml(xmlb.fetchStockGroups(cfg.companyName)));
    const names = deepCollect(parsed, 'STOCKGROUPNAME').map(text).filter(Boolean);
    return names.length ? names.map((nm) => ({ name: nm })) : demo.listStockGroups();
  }, () => demo.listStockGroups());
}

/* -------------------------------------------------------------------------- */
/*  Vouchers — read                                                            */
/* -------------------------------------------------------------------------- */

function voucherFromNode(n) {
  const entriesRaw = n.ALLLEDGERENTRIES?.LIST
    ? (Array.isArray(n.ALLLEDGERENTRIES.LIST) ? n.ALLLEDGERENTRIES.LIST : [n.ALLLEDGERENTRIES.LIST])
    : [];
  const entries = entriesRaw.map(entryFromNode).filter((e) => e.ledger);
  const amount = Math.abs(Number(text(n.AMOUNT)) || 0) || round2(entries.reduce((s, e) => (e.debit ? s + e.amount : s), 0));
  return {
    id: text(n.REMOTEID) || text(n.MASTERID) || `${text(n.VOUCHERTYPENAME)}/${text(n.VOUCHERNUMBER)}`,
    voucherType: text(n.VOUCHERTYPENAME),
    voucherNumber: text(n.VOUCHERNUMBER),
    date: text(n.DATE),
    dateDisplay: `${text(n.DATE).slice(6, 8)}-${text(n.DATE).slice(4, 6)}-${text(n.DATE).slice(0, 4)}`,
    party: text(n.PARTYLEDGERNAME) || entries.find((e) => /sundry/i.test(e.ledger))?.ledger || '',
    narration: text(n.NARRATION),
    reference: text(n.REFERENCE),
    amount: round2(amount),
    entries,
    status: text(n.ISCANCELLED) === 'Yes' ? 'Cancelled' : 'Active',
  };
}

async function getVouchers(filters = {}) {
  const from = toTallyDate(filters.from || fyStart());
  const to = toTallyDate(filters.to || todayTally());
  const type = filters.type || '';
  return withFallback('vouchers', async () => {
    const cfg = getTallyConfig();
    const parsed = await parseXml(await postXml(xmlb.fetchVouchers(from, to, type, cfg.companyName)));
    let list = deepCollect(parsed, 'VOUCHER').map(voucherFromNode);
    if (filters.party) list = list.filter((v) => (v.party || '').toLowerCase().includes(filters.party.toLowerCase()));
    if (filters.limit) list = list.slice(0, Number(filters.limit));
    return list;
  }, () => demo.listVouchers({ from, to, type: filters.voucherTypeName || type, party: filters.party, limit: filters.limit }));
}

async function getVoucherById(id) {
  return withFallback('voucher', async () => {
    const all = (await getVouchers({})).data;
    const hit = all.find((v) => v.id === id || v.voucherNumber === id);
    if (!hit) throw Object.assign(new Error(`Voucher "${id}" not found`), { statusCode: 404 });
    return hit;
  }, () => {
    const hit = demo.getVoucher(id);
    if (!hit) throw Object.assign(new Error(`Voucher "${id}" not found`), { statusCode: 404 });
    return hit;
  });
}

/** Next available voucher number for a type (best-effort against Tally). */
async function getNextVoucherNumber(voucherTypeName, prefix = '') {
  return withFallback('voucher number', async () => {
    const list = (await getVouchers({ voucherTypeName, limit: 500 })).data
      .filter((v) => v.voucherType.toLowerCase() === voucherTypeName.toLowerCase());
    const last = list[0]?.voucherNumber || '';
    const m = last.match(/(\d+)\s*$/);
    const next = (m ? parseInt(m[1], 10) : 0) + 1;
    const tag = { Sales: 'INV', Purchase: 'PUR', Payment: 'PMT', Receipt: 'RCPT', Contra: 'CTR', Journal: 'JV', 'Credit Note': 'CR', 'Debit Note': 'DR' }[voucherTypeName] || 'VCH';
    return `${prefix}${tag}/${String(next).padStart(4, '0')}`;
  }, () => demo.nextVoucherNumber(voucherTypeName, prefix));
}

/* -------------------------------------------------------------------------- */
/*  Vouchers — write (the double-entry engine)                                 */
/* -------------------------------------------------------------------------- */

/**
 * Convert a friendly browser payload into a balanced double entry, then build
 * the Import XML. This is where GST is computed/split and the Dr/Cr sign
 * convention is applied.
 */
function normalizeVoucherPayload(p) {
  const cfg = getTallyConfig();
  const companyState = 'Maharashtra'; // overridden below by company info when available
  const v = {
    type: p.type,
    date: toTallyDate(p.date),
    voucherNumber: p.voucherNumber || '',
    narration: p.narration || '',
    reference: p.reference || '',
    referenceDate: p.referenceDate,
    party: p.party || '',
    partyGstin: p.partyGstin || '',
    partyState: p.partyState || '',
    partyAddress: p.partyAddress || '',
    partyCity: p.partyCity || '',
    partyPincode: p.partyPincode || '',
    partyEmail: p.partyEmail || '',
    partyPhone: p.partyPhone || '',
    company: p.company || cfg.companyName,
    items: p.items || [],
    entries: [],
    instrument: p.instrument,
    force: !!p.force,
  };
  const companyStateUsed = p.companyState || companyState;

  /* ---- Trading vouchers: rebuild entries from item lines + GST settings ---- */
  if (['sales', 'purchase', 'credit-note', 'debit-note'].includes(p.type)) {
    const interState = !!v.partyState && v.partyState.toLowerCase() !== companyStateUsed.toLowerCase();
    let taxable = 0, cgst = 0, sgst = 0, igst = 0;
    v.items = p.items.filter((it) => it.name && Number(it.qty) > 0).map((it) => {
      const gross = round2(Number(it.qty) * Number(it.rate));
      const lineTaxable = round2(gross * (1 - (Number(it.discountPercent) || 0) / 100));
      const g = computeGst(lineTaxable, it.gstRate ?? it.gstRatePercent, v.partyState, companyStateUsed);
      taxable = round2(taxable + g.taxable);
      cgst = round2(cgst + g.cgst); sgst = round2(sgst + g.sgst); igst = round2(igst + g.igst);
      return { ...it, taxableValue: g.taxable, gst: { cgst: g.cgst, sgst: g.sgst, igst: g.igst } };
    });
    if (!v.items.length) throw Object.assign(new Error('At least one item line with quantity is required'), { statusCode: 422 });

    const grand = round2(taxable + cgst + sgst + igst);
    const salesAcct = p.salesLedger || (interState ? 'Sales Account' : 'Sales Account');
    const purchAcct = p.purchaseLedger || 'Purchase Account';
    const taxLed = (intra, out) => {
      const pre = out ? 'Output' : 'Input';
      if (intra) return { cgst: `${pre} CGST`, sgst: `${pre} SGST` };
      return { igst: `${pre} IGST` };
    };

    if (p.type === 'sales') {
      v.entries.push({ ledger: v.party, amount: grand, debit: true, billAllocation: v.voucherNumber || 'New Ref' });
      v.entries.push({ ledger: salesAcct, amount: taxable, debit: false });
      if (cgst) v.entries.push({ ledger: taxLed(true, true).cgst, amount: cgst, debit: false });
      if (sgst) v.entries.push({ ledger: taxLed(true, true).sgst, amount: sgst, debit: false });
      if (igst) v.entries.push({ ledger: taxLed(false, true).igst, amount: igst, debit: false });
    } else if (p.type === 'purchase') {
      v.entries.push({ ledger: purchAcct, amount: taxable, debit: true });
      if (cgst) v.entries.push({ ledger: taxLed(true, false).cgst, amount: cgst, debit: true });
      if (sgst) v.entries.push({ ledger: taxLed(true, false).sgst, amount: sgst, debit: true });
      if (igst) v.entries.push({ ledger: taxLed(false, false).igst, amount: igst, debit: true });
      v.entries.push({ ledger: v.party, amount: grand, debit: false, billAllocation: v.reference || 'New Ref' });
    } else {
      // Credit Note (sales return) / Debit Note (purchase return) — mirror images.
      const isCredit = p.type === 'credit-note';
      const flip = (e) => ({ ...e, debit: !e.debit });
      if (isCredit) {
        v.entries.push({ ledger: v.party, amount: grand, debit: false, billAllocation: p.originalInvoice || 'New Ref' });
        v.entries.push({ ledger: salesAcct, amount: taxable, debit: true });
        if (cgst) v.entries.push({ ledger: 'Output CGST', amount: cgst, debit: true });
        if (sgst) v.entries.push({ ledger: 'Output SGST', amount: sgst, debit: true });
        if (igst) v.entries.push({ ledger: 'Output IGST', amount: igst, debit: true });
      } else {
        v.entries.push({ ledger: purchAcct, amount: taxable, debit: false });
        if (cgst) v.entries.push({ ledger: 'Input CGST', amount: cgst, debit: false });
        if (sgst) v.entries.push({ ledger: 'Input SGST', amount: sgst, debit: false });
        if (igst) v.entries.push({ ledger: 'Input IGST', amount: igst, debit: false });
        v.entries.push({ ledger: v.party, amount: grand, debit: true, billAllocation: p.originalInvoice || 'New Ref' });
      }
      void flip;
    }
    v.amount = grand; v.taxable = taxable; v.cgst = cgst; v.sgst = sgst; v.igst = igst; v.interState = interState;
  }

  /* ---- Simple vouchers: browser posts ready-made entries ------------------ */
  if (['payment', 'receipt', 'contra', 'journal'].includes(p.type)) {
    v.entries = (p.entries || []).map((e) => ({
      ledger: e.ledger, amount: round2(Math.abs(Number(e.amount))),
      debit: !!e.debit, billAllocation: e.billAllocation || null,
    }));
    v.amount = round2(v.entries.filter((e) => e.debit).reduce((s, e) => s + e.amount, 0));
  }

  /* ---- Balance validation: ΣDr MUST equal ΣCr before touching Tally ------- */
  const dr = round2(v.entries.filter((e) => e.debit).reduce((s, e) => s + e.amount, 0));
  const cr = round2(v.entries.filter((e) => !e.debit).reduce((s, e) => s + e.amount, 0));
  if (!v.entries.length) throw Object.assign(new Error('No ledger entries generated'), { statusCode: 422 });
  if (Math.abs(dr - cr) > 0.01) {
    throw Object.assign(new Error(`Unbalanced entry: Debit ${dr} ≠ Credit ${cr}`), { statusCode: 422 });
  }
  v.balanced = true;
  return v;
}

/** Create any voucher type. Returns {voucherNumber, source, queued?}. */
async function createVoucher(payload) {
  const v = normalizeVoucherPayload(payload);

  const real = async () => {
    const xml = xmlb.buildVoucherXml(v);
    const parsed = await parseXml(await postXml(xml));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally rejected the voucher: ${out.lineError}`), { statusCode: 502, tallyError: true });
    if (!out.created && !out.altered) throw Object.assign(new Error('Tally did not confirm creation (no CREATED count) — verify in Tally'), { statusCode: 502 });
    return { created: true, voucherNumber: v.voucherNumber };
  };

  const demoFn = () => {
    // Demo insert mirrors the same double entry the XML path pushes.
    const doc = {
      voucherType: xmlb.VOUCHER_TYPES[v.type].vchType,
      voucherNumber: v.voucherNumber,
      date: v.date,
      party: v.party,
      partyGstin: v.partyGstin, partyState: v.partyState,
      reference: v.reference, narration: v.narration,
      amount: v.amount || round2(v.entries.filter((e) => e.debit).reduce((s, e) => s + e.amount, 0)),
      taxable: v.taxable, cgst: v.cgst, sgst: v.sgst, igst: v.igst, interState: v.interState,
      items: v.items, entries: v.entries, mode: payload.instrument?.mode,
      status: 'Active', createdAt: new Date().toISOString(), force: v.force,
    };
    return demo.insertVoucher(doc);
  };

  return withFallback('create voucher', real, demoFn, { forceReal: !!payload._forceReal });
}

async function updateVoucher(id, payload) {
  const v = normalizeVoucherPayload({ ...payload, type: payload.type });
  const real = async () => {
    const xml = xmlb.buildVoucherXml({ ...v, action: 'Alter', masterId: payload.masterId });
    const parsed = await parseXml(await postXml(xml));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally rejected the alteration: ${out.lineError}`), { statusCode: 502, tallyError: true });
    return { altered: true, voucherNumber: v.voucherNumber };
  };
  return withFallback('alter voucher', real, () => demo.updateVoucher(id, {
    voucherNumber: v.voucherNumber, date: v.date, party: v.party, amount: v.amount,
    narration: v.narration, reference: v.reference, entries: v.entries, items: v.items,
  }), { forceReal: !!payload._forceReal });
}

async function deleteVoucher(id, opts = {}) {
  const real = async () => {
    const existing = await getVoucherById(id);
    const xml = xmlb.buildVoucherDeleteXml({
      masterId: existing.id?.includes('-') ? undefined : existing.id,
      voucherNumber: existing.voucherNumber, date: existing.date,
      vchType: existing.voucherType, company: getTallyConfig().companyName,
    });
    const parsed = await parseXml(await postXml(xml));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally refused deletion: ${out.lineError}`), { statusCode: 502, tallyError: true });
    return { deleted: true };
  };
  return withFallback('delete voucher', real, () => demo.deleteVoucher(id), { forceReal: !!opts.forceReal });
}

/* -------------------------------------------------------------------------- */
/*  Ledger / stock writes                                                      */
/* -------------------------------------------------------------------------- */

async function createLedger(data) {
  const real = async () => {
    const parsed = await parseXml(await postXml(xmlb.buildLedgerXml(data, 'Create', getTallyConfig().companyName)));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally rejected the ledger: ${out.lineError}`), { statusCode: 502, tallyError: true });
    return { created: true, name: data.name };
  };
  return withFallback('create ledger', real, () => demo.createLedger(data), { forceReal: !!data._forceReal });
}

async function updateLedger(name, patch) {
  const real = async () => {
    const merged = { ...(await getLedger(name)).data, ...patch, name: patch.name || name };
    const parsed = await parseXml(await postXml(xmlb.buildLedgerXml(merged, 'Alter', getTallyConfig().companyName, name)));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally rejected the alteration: ${out.lineError}`), { statusCode: 502, tallyError: true });
    return { altered: true, name: merged.name };
  };
  return withFallback('alter ledger', real, () => demo.updateLedger(name, patch), { forceReal: !!patch._forceReal });
}

async function deleteLedger(name, opts = {}) {
  const real = async () => {
    const parsed = await parseXml(await postXml(xmlb.buildLedgerDeleteXml(name, getTallyConfig().companyName)));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally refused deletion: ${out.lineError}`), { statusCode: 502, tallyError: true });
    return { deleted: true };
  };
  return withFallback('delete ledger', real, () => demo.deleteLedger(name), { forceReal: !!opts.forceReal });
}

async function createStockItem(item) {
  const real = async () => {
    const parsed = await parseXml(await postXml(xmlb.buildStockItemXml(item, getTallyConfig().companyName)));
    const out = importOutcome(parsed);
    if (out.lineError) throw Object.assign(new Error(`Tally rejected the stock item: ${out.lineError}`), { statusCode: 502, tallyError: true });
    return { created: true, name: item.name };
  };
  return withFallback('create stock item', real, () => ({ created: true, name: item.name, note: 'Demo mode — stock items are static' }));
}

/* -------------------------------------------------------------------------- */
/*  Reports (statement parsers)                                                */
/* -------------------------------------------------------------------------- */

/**
 * Statement extractor for Trial Balance / P&L / Balance Sheet.
 * Tally exports these as repeated rows; layouts differ per build, so we scan
 * for the well-known row-node families and pull (title, amount) pairs.
 */
function statementRows(parsed, titleTags, amountTags) {
  const rows = [];
  const titles = [];
  for (const t of titleTags) deepCollect(parsed, t).forEach((x) => titles.push(text(x)));
  const amounts = [];
  for (const a of amountTags) deepCollect(parsed, a).forEach((x) => amounts.push(Number(text(x)) || 0));
  titles.forEach((title, i) => {
    if (title) rows.push({ name: title, amount: round2(Math.abs(amounts[i] || 0)) });
  });
  return rows.filter((r) => r.name);
}

async function getReport(reportName, params = {}) {
  const from = toTallyDate(params.from || fyStart());
  const to = toTallyDate(params.to || todayTally());
  const cfg = getTallyConfig();

  const demoMap = {
    'trial-balance': () => demo.trialBalance(from, to),
    'profit-loss': () => demo.profitLoss(from, to),
    'balance-sheet': () => demo.balanceSheet(to),
    daybook: () => demo.daybook(from, to, params.limit || 100),
    outstanding: () => demo.outstanding(to),
    'gst-summary': () => demo.gstSummary(from, to),
    'ledger-report': () => demo.ledgerReport(params.ledger, from, to),
    dashboard: () => demo.dashboardSummary(),
  };

  const real = async () => {
    let xml;
    switch (reportName) {
      case 'dashboard': return assembleDashboardLive(); // composed, no single XML report
      case 'trial-balance': xml = xmlb.fetchTrialBalance(from, to, cfg.companyName); break;
      case 'profit-loss': xml = xmlb.fetchProfitLoss(from, to, cfg.companyName); break;
      case 'balance-sheet': xml = xmlb.fetchBalanceSheet(to, cfg.companyName); break;
      case 'daybook': xml = xmlb.fetchDayBook(from, to, cfg.companyName); break;
      case 'outstanding': xml = xmlb.fetchOutstanding(params.kind || 'receivables', to, cfg.companyName); break;
      case 'gst-summary': xml = xmlb.fetchVouchers(from, to, '', cfg.companyName); break;
      case 'ledger-report': xml = xmlb.fetchLedgerReport(params.ledger, from, to, cfg.companyName); break;
      default: throw new Error(`Unknown report: ${reportName}`);
    }
    const parsed = await parseXml(await postXml(xml));

    if (reportName === 'daybook' || reportName === 'gst-summary') {
      const list = deepCollect(parsed, 'VOUCHER').map(voucherFromNode);
      if (reportName === 'daybook') return list;
      // GST summary is aggregated client-side from voucher lines.
      const outward = [], inward = [];
      let t1 = { taxable: 0, cgst: 0, sgst: 0, igst: 0 }, t2 = { ...t1 };
      for (const v of list) {
        const rec = { date: v.dateDisplay, number: v.voucherNumber, party: v.party, gstin: '', taxable: v.amount, cgst: 0, sgst: 0, igst: 0, total: v.amount };
        if (['Sales', 'Credit Note'].includes(v.voucherType)) outward.push(rec);
        else if (['Purchase', 'Debit Note'].includes(v.voucherType)) inward.push(rec);
      }
      const r2 = round2;
      return {
        from: `${from.slice(6, 8)}-${from.slice(4, 6)}-${from.slice(0, 4)}`, to: `${to.slice(6, 8)}-${to.slice(4, 6)}-${to.slice(0, 4)}`,
        gstr1: { invoices: outward, totals: { taxable: r2(outward.reduce((s, x) => s + x.taxable, 0)), cgst: 0, sgst: 0, igst: 0 } },
        gstr3b: { supplies: inward, totals: { taxable: r2(inward.reduce((s, x) => s + x.taxable, 0)), cgst: 0, sgst: 0, igst: 0 } },
        note: 'GST tax-split requires duty-ledger level parsing — totals shown at invoice value. Enable ODBC for precise splits.',
      };
    }

    if (reportName === 'ledger-report') {
      const list = deepCollect(parsed, 'VOUCHER').map(voucherFromNode);
      return { ledger: params.ledger, from, to, rows: list, note: 'Ledger statement from voucher register' };
    }

    // Statement-shaped reports: Trial Balance / P&L / Balance Sheet.
    const rows = statementRows(parsed,
      ['DS_HNAME', 'DSPDISPNAME', 'DSPNAME', 'ACCNAME', 'BSNAME', 'PLNAME'],
      ['DS_AMOUNT', 'DSPCLOSINGBAL', 'BSPRIMARYAMT', 'PLAMOUNT']);
    if (!rows.length) throw new Error('Statement layout not recognised — prefer the ODBC channel for this report');
    return { rows, source: 'xml' };
  };

  return withFallback(`report ${reportName}`, real, demoMap[reportName] || (() => ({})));
}

/**
 * Live-Tally dashboard assembly (no single XML report exists for this, so we
 * compose it from cheap pulls: voucher register + trial balance + outstanding).
 */
async function assembleDashboardLive() {
  const cfg = getTallyConfig();
  const today = todayTally();
  const monthStart = today.slice(0, 6) + '01';
  const yearStart = fyStart();

  const [fy, out, tb] = await Promise.all([
    postXml(xmlb.fetchVouchers(yearStart, today, '', cfg.companyName)).then(parseXml),
    postXml(xmlb.fetchOutstanding('receivables', today, cfg.companyName)).then(parseXml),
    postXml(xmlb.fetchTrialBalance(yearStart, today, cfg.companyName)).then(parseXml),
  ]);

  const vouchers = deepCollect(fy, 'VOUCHER').map(voucherFromNode).filter((v) => v.status === 'Active');
  const sumType = (type, from) => round2(vouchers.filter((v) => v.voucherType === type && v.date >= from).reduce((s, v) => s + v.amount, 0));

  // Cash & bank closing balances from the trial-balance rows.
  const tbRows = statementRows(tb, ['DS_HNAME', 'DSPDISPNAME', 'DSPNAME', 'ACCNAME'], ['DS_AMOUNT', 'DSPCLOSINGBAL']);
  const cashLike = (re) => tbRows.filter((r) => re.test(r.name));
  const cashInHand = round2(cashLike(/^cash/i).reduce((s, r) => s + r.amount, 0));
  const banks = cashLike(/bank/i).map((b) => ({ name: b.name, balance: b.amount }));
  const bankBalance = round2(banks.reduce((s, b) => s + b.balance, 0));

  const recAmt = round2(deepCollect(out, 'BILLDUEAMT').reduce((s, x) => s + (Number(text(x)) || 0), 0));

  // Last 6 months sales/purchase split for the bar chart.
  const months = [];
  const byKey = {};
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const from6 = fyStart(); // simplest: current FY months present in the register
  for (const v of vouchers) {
    const k = v.date.slice(0, 6);
    if (!byKey[k]) byKey[k] = { label: MONTHS[+k.slice(4, 6) - 1] || k, sales: 0, purchase: 0 };
    if (v.voucherType === 'Sales') byKey[k].sales = round2(byKey[k].sales + v.amount);
    if (v.voucherType === 'Purchase') byKey[k].purchase = round2(byKey[k].purchase + v.amount);
  }
  Object.entries(byKey).sort().forEach(([, x]) => months.push(x));

  // Cash-flow approximation: Receipt/Payment/Contra vouchers, last 30 days.
  const cashflow = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000);
    const ymd = fmtYmd(d);
    const dayVs = vouchers.filter((v) => v.date === ymd);
    const inflow = round2(dayVs.filter((v) => v.voucherType === 'Receipt').reduce((s, v) => s + v.amount, 0));
    const outflow = round2(dayVs.filter((v) => v.voucherType === 'Payment').reduce((s, v) => s + v.amount, 0));
    cashflow.push({ date: `${ymd.slice(6, 8)}-${ymd.slice(4, 6)}-${ymd.slice(0, 4)}`, inflow, outflow, net: round2(inflow - outflow) });
  }

  return {
    company: cfg.companyName || 'Tally Company',
    financialYear: `${tallyToDisplay(yearStart)} to ${tallyToDisplay(fyEnd())}`,
    stats: {
      salesToday: sumType('Sales', today), salesMonth: sumType('Sales', monthStart), salesYear: sumType('Sales', yearStart),
      purchaseToday: sumType('Purchase', today), purchaseMonth: sumType('Purchase', monthStart), purchaseYear: sumType('Purchase', yearStart),
      cashInHand, bankBalance, banks,
      receivables: recAmt, payables: 0,
    },
    months, expenses: [], cashflow,
    recent: vouchers.slice(0, 20).map((v) => ({ id: v.id, date: v.dateDisplay, voucherType: v.voucherType, voucherNumber: v.voucherNumber, party: v.party, amount: v.amount, narration: v.narration })),
  };
}

module.exports = {
  state,
  testConnection,
  getCompanyInfo,
  getLedgers, getLedger, getGroups,
  getStockItems, getStockGroups,
  getVouchers, getVoucherById, getNextVoucherNumber,
  createVoucher, updateVoucher, deleteVoucher,
  createLedger, updateLedger, deleteLedger, createStockItem,
  getReport,
};
