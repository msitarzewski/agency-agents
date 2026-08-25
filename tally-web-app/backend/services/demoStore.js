/**
 * ============================================================================
 * DEMO STORE — offline / fallback dataset
 * ============================================================================
 * WHY THIS EXISTS (important):
 *   • Tally Prime runs on a Windows box on the LAN. When this Node server
 *     cannot reach Tally (shop closed, network issue, deploying to cloud),
 *     `demoMode: 'auto'` (config/tallyConfig.js) transparently falls back to
 *     this in-memory dataset so the whole UI keeps working.
 *   • Vouchers created while in fallback are queued by syncService and pushed
 *     to Tally the moment the connection returns.
 *   • It also powers a fully-working demo without any Tally installation
 *     (demoMode: 'always').
 *
 * The store mimics the canonical JSON shapes produced by tallyXMLService's
 * XML parsers, so every consumer above it is source-agnostic.
 * ============================================================================
 */
const { round2, fyStart, fyEnd, fmtYmd, tallyToDisplay } = require('../utils/helpers');

/* -------------------------------------------------------------------------- */
/*  Seeded PRNG — same "random" data on every boot so charts stay stable       */
/* -------------------------------------------------------------------------- */
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rnd = mulberry32(20260825);
const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
const randInt = (a, b) => a + Math.floor(rnd() * (b - a + 1));

/* -------------------------------------------------------------------------- */
/*  Static masters                                                             */
/* -------------------------------------------------------------------------- */
const COMPANY = {
  name: 'Sunrise Traders Pvt Ltd',
  address: '402, Solitaire Corporate Park, Andheri East',
  city: 'Mumbai', state: 'Maharashtra', pincode: '400093',
  gstin: '27AAACS1867F1Z5',
  phone: '022-48901234',
  email: 'accounts@sunrisetraders.in',
  financialYearFrom: tallyToDisplay(fyStart()),
  booksEndingOn: tallyToDisplay(fyEnd()),
  currency: 'INR',
};

// Standard Tally reserved groups (subset with the ones the UI offers).
const GROUPS = [
  { name: 'Primary', parent: '', nature: 'Primary' },
  ...[
    ['Capital Account', 'Primary', 'Liability'],
    ['Loans (Liability)', 'Primary', 'Liability'],
    ['Current Liabilities', 'Primary', 'Liability'],
    ['Sundry Creditors', 'Current Liabilities', 'Liability'],
    ['Duties & Taxes', 'Current Liabilities', 'Liability'],
    ['Provisions', 'Current Liabilities', 'Liability'],
    ['Fixed Assets', 'Primary', 'Asset'],
    ['Investments', 'Primary', 'Asset'],
    ['Current Assets', 'Primary', 'Asset'],
    ['Sundry Debtors', 'Current Assets', 'Asset'],
    ['Cash-in-Hand', 'Current Assets', 'Asset'],
    ['Bank Accounts', 'Current Assets', 'Asset'],
    ['Stock-in-Hand', 'Current Assets', 'Asset'],
    ['Loans & Advances (Asset)', 'Current Assets', 'Asset'],
    ['Sales Accounts', 'Primary', 'Income'],
    ['Purchase Accounts', 'Primary', 'Expense'],
    ['Direct Incomes', 'Primary', 'Income'],
    ['Direct Expenses', 'Primary', 'Expense'],
    ['Indirect Incomes', 'Primary', 'Income'],
    ['Indirect Expenses', 'Primary', 'Expense'],
  ].map(([name, parent, nature]) => ({ name, parent, nature })),
];

const PARTIES = [
  ['Sharma Electronics LLP', 'Sundry Debtors', '27AABCS1429B1Z1', 'Maharashtra', 'Mumbai'],
  ['Verma Retail Pvt Ltd', 'Sundry Debtors', '29AACCV3399K1Z1', 'Karnataka', 'Bengaluru'],
  ['Krishna Traders', 'Sundry Debtors', '24AAECK7712R1ZP', 'Gujarat', 'Surat'],
  ['Mehta Distributors', 'Sundry Debtors', '27AAECM8845J1Z4', 'Maharashtra', 'Pune'],
  ['Rajesh Global Exim', 'Sundry Debtors', '36AAFCR5567L1Z8', 'Telangana', 'Hyderabad'],
  ['Coastal Supplies Co', 'Sundry Debtors', '32AAGFC9023M1Z2', 'Kerala', 'Kochi'],
  ['Nova Impex Pvt Ltd', 'Sundry Creditors', '07AABCN1123D1Z5', 'Delhi', 'New Delhi'],
  ['Glow Industries', 'Sundry Creditors', '27AABCG7789F1Z9', 'Maharashtra', 'Mumbai'],
  ['Vertex Components', 'Sundry Creditors', '33AAGCV5521H1Z6', 'Tamil Nadu', 'Chennai'],
  ['Sunlight Wholesale', 'Sundry Creditors', '09AAJCS3456P1Z2', 'Uttar Pradesh', 'Kanpur'],
  ['Apex Metals Pvt Ltd', 'Sundry Creditors', '27AAACA2234Q1ZX', 'Maharashtra', 'Nashik'],
];

const OTHER_LEDGERS = [
  ['Cash', 'Cash-in-Hand', 'Dr', 250000],
  ['HDFC Bank — Current A/c 5512', 'Bank Accounts', 'Dr', 1850000],
  ['ICICI Bank — OD A/c 9930', 'Bank Accounts', 'Dr', 620000],
  ['Sales Account — Local', 'Sales Accounts', 'Cr', 0],
  ['Sales Account — Interstate', 'Sales Accounts', 'Cr', 0],
  ['Purchase Account — Local', 'Purchase Accounts', 'Dr', 0],
  ['Purchase Account — Interstate', 'Purchase Accounts', 'Dr', 0],
  ['Output CGST 9%', 'Duties & Taxes', 'Cr', 0],
  ['Output SGST 9%', 'Duties & Taxes', 'Cr', 0],
  ['Output IGST 18%', 'Duties & Taxes', 'Cr', 0],
  ['Input CGST 9%', 'Duties & Taxes', 'Dr', 0],
  ['Input SGST 9%', 'Duties & Taxes', 'Dr', 0],
  ['Input IGST 18%', 'Duties & Taxes', 'Dr', 0],
  ['Round Off', 'Indirect Expenses', 'Cr', 0],
  ['Rent', 'Indirect Expenses', 'Dr', 0],
  ['Salaries & Wages', 'Indirect Expenses', 'Dr', 0],
  ['Electricity Charges', 'Indirect Expenses', 'Dr', 0],
  ['Telephone & Internet', 'Indirect Expenses', 'Dr', 0],
  ['Travelling Expenses', 'Indirect Expenses', 'Dr', 0],
  ['Professional Fees', 'Indirect Expenses', 'Dr', 0],
  ['Freight & Courier', 'Direct Expenses', 'Dr', 0],
  ['Discount Allowed', 'Direct Expenses', 'Dr', 0],
  ['Commission Received', 'Indirect Incomes', 'Cr', 0],
  ['Interest on FD', 'Indirect Incomes', 'Cr', 0],
  ['Capital — A. Mehta', 'Capital Account', 'Cr', 5500000],
  ['Drawings — A. Mehta', 'Capital Account', 'Dr', 0],
  ['Office Equipment', 'Fixed Assets', 'Dr', 480000],
  ['Computer & Peripherals', 'Fixed Assets', 'Dr', 355000],
  ['Furniture & Fixtures', 'Fixed Assets', 'Dr', 210000],
  ['TDS Receivable', 'Loans & Advances (Asset)', 'Dr', 42000],
  ['GST Input Credit Carry Forward', 'Loans & Advances (Asset)', 'Dr', 0],
];

const ledgers = [];
for (const [name, parent, gstin, state, city] of PARTIES) {
  ledgers.push({
    name, parent, openingBalance: { amount: randInt(-400000, 850000), drCr: null },
    gstin, state, regType: 'Regular', address: `${randInt(1, 99)}, ${pick(['MG Road', 'Station Road', 'Industrial Area', 'Sector 11', 'Park Street'])}`,
    city, pincode: String(randInt(110001, 799999)), phone: `9${randInt(100000000, 999999999)}`,
    email: `billing@${name.toLowerCase().replace(/[^a-z]+/g, '')}.com`,
  });
}
for (const [name, parent, drCr, amt] of OTHER_LEDGERS) {
  ledgers.push({
    name, parent, openingBalance: { amount: amt, drCr }, gstin: '', state: 'Maharashtra',
    regType: 'Not Applicable', address: '', city: 'Mumbai', pincode: '400093',
    phone: '', email: '',
  });
}

// Balance the opening trial balance: plug the net difference into Capital so
// Σ(opening Dr) == Σ(opening Cr) — exactly as a real Tally opening does.
{
  const signed = (l) => (l.openingBalance.drCr === 'Cr' ? -1 : 1) * (l.openingBalance.amount || 0);
  let total = 0;
  for (const l of ledgers) if (l.name !== 'Capital — A. Mehta') total += signed(l);
  // Capital absorbs the exact difference so the opening books balance.
  const capital = ledgers.find((l) => l.name === 'Capital — A. Mehta');
  capital.openingBalance = {
    amount: round2(Math.abs(total)),
    drCr: total >= 0 ? 'Cr' : 'Dr', // credit when the rest of the books are Dr-heavy
  };
}

const STOCK_ITEMS = [
  ['LED Smart TV 43"', 'TV & Electronics', '8528', 'Pcs', 24500, 18],
  ['Bluetooth Speaker Pro', 'Audio Devices', '8518', 'Pcs', 3200, 18],
  ['Wireless Earbuds X2', 'Audio Devices', '8518', 'Pcs', 1850, 18],
  ['Smartphone 5G 128GB', 'Mobiles', '8517', 'Pcs', 15900, 18],
  ['Laptop Core i5 12th Gen', 'Computers', '8471', 'Pcs', 52400, 18],
  ['Mechanical Keyboard RGB', 'Computers', '8471', 'Pcs', 4450, 18],
  ['27" IPS Monitor', 'Computers', '8528', 'Pcs', 12750, 18],
  ['Inverter 1100VA', 'Home Appliances', '8504', 'Pcs', 8900, 18],
  ['Mixer Grinder 750W', 'Home Appliances', '8509', 'Pcs', 3650, 12],
  ['Air Fryer 4L', 'Home Appliances', '8516', 'Pcs', 5890, 18],
  ['Copper Bottle 1L', 'Kitchenware', '7411', 'Pcs', 720, 12],
  ['Steam Iron 1600W', 'Home Appliances', '8516', 'Pcs', 1490, 18],
].map(([name, group, hsn, unit, rate, gst]) => ({
  name, group, hsn, unit, rate, gst,
  closingQty: randInt(4, 90),
}));

/* -------------------------------------------------------------------------- */
/*  Voucher generation (last ~150 days)                                        */
/* -------------------------------------------------------------------------- */
const vouchers = [];
let vchSeq = { Sales: 0, Purchase: 0, Payment: 0, Receipt: 0, Contra: 0, Journal: 0, 'Credit Note': 0, 'Debit Note': 0 };

function addDays(ymd, days) {
  const y = +ymd.slice(0, 4), m = +ymd.slice(4, 6) - 1, d = +ymd.slice(6, 8);
  const dt = new Date(y, m, d + days);
  return fmtYmd(dt);
}

function pushVoucher(v) {
  v.id = `demo-${v.voucherType.toLowerCase().replace(' ', '-')}-${v.voucherNumber}`;
  v.dateDisplay = tallyToDisplay(v.date);
  vouchers.push(v);
}

function makeTradingVoucher(type /* Sales | Purchase | Credit Note */, date, party) {
  const isSale = type === 'Sales';
  const custs = ledgers.filter((l) => l.parent === (isSale ? 'Sundry Debtors' : 'Sundry Creditors'));
  const p = party ? ledgers.find((l) => l.name === party) : pick(custs);
  if (!p) return null;
  const intra = p.state === COMPANY.state;
  const nItems = randInt(1, 4);
  const items = [];
  for (let i = 0; i < nItems; i++) {
    const st = pick(STOCK_ITEMS);
    if (items.some((x) => x.name === st.name)) continue;
    const qty = randInt(1, isSale ? 12 : 30);
    const disc = pick([0, 0, 0, 2.5, 5]);
    const gross = qty * st.rate;
    const taxable = round2(gross * (1 - disc / 100));
    const tax = round2((taxable * st.gst) / 100);
    items.push({
      name: st.name, hsn: st.hsn, unit: st.unit, qty, rate: st.rate,
      discountPercent: disc, taxableValue: taxable, gstRate: st.gst,
      gst: intra
        ? { cgst: round2(tax / 2), sgst: round2(tax / 2), igst: 0 }
        : { cgst: 0, sgst: 0, igst: tax },
      total: round2(taxable + tax),
    });
  }
  const taxable = round2(items.reduce((s, i) => s + i.taxableValue, 0));
  const cgst = round2(items.reduce((s, i) => s + i.gst.cgst, 0));
  const sgst = round2(items.reduce((s, i) => s + i.gst.sgst, 0));
  const igst = round2(items.reduce((s, i) => s + i.gst.igst, 0));
  const grand = round2(taxable + cgst + sgst + igst);

  const salesLedger = intra
    ? (isSale ? 'Sales Account — Local' : 'Purchase Account — Local')
    : (isSale ? 'Sales Account — Interstate' : 'Purchase Account — Interstate');

  // Double entry: Sales → party Dr, sales Cr, taxes Cr.
  //               Purchase → purchase Dr, taxes Dr, party Cr.
  const entries = isSale
    ? [
        { ledger: p.name, amount: grand, debit: true, billAllocation: null },
        { ledger: salesLedger, amount: taxable, debit: false },
        ...(cgst ? [{ ledger: 'Output CGST 9%', amount: cgst, debit: false }] : []),
        ...(sgst ? [{ ledger: 'Output SGST 9%', amount: sgst, debit: false }] : []),
        ...(igst ? [{ ledger: 'Output IGST 18%', amount: igst, debit: false }] : []),
      ]
    : [
        { ledger: salesLedger, amount: taxable, debit: true },
        ...(cgst ? [{ ledger: 'Input CGST 9%', amount: cgst, debit: true }] : []),
        ...(sgst ? [{ ledger: 'Input SGST 9%', amount: sgst, debit: true }] : []),
        ...(igst ? [{ ledger: 'Input IGST 18%', amount: igst, debit: true }] : []),
        { ledger: p.name, amount: grand, debit: false, billAllocation: null },
      ];

  vchSeq[type] += 1;
  const v = {
    voucherType: type,
    voucherNumber: `${type === 'Sales' ? 'INV' : 'PUR'}/${String(vchSeq[type]).padStart(4, '0')}`,
    date,
    party: p.name, partyGstin: p.gstin, partyState: p.state,
    reference: isSale ? '' : `SUP/${randInt(1000, 9999)}`,
    narration: isSale ? 'Sold against invoice' : 'Goods purchased',
    amount: grand, taxable, cgst, sgst, igst, interState: !intra,
    items, entries, status: 'Active', createdAt: new Date().toISOString(),
  };
  // Credit note = sales return → flip the entry sides.
  if (type === 'Credit Note') {
    v.entries = v.entries.map((e) => ({ ...e, debit: !e.debit, amount: e.amount }));
    v.voucherNumber = `CR/${String(vchSeq['Credit Note']).padStart(4, '0')}`;
    v.reference = pick(vouchers.filter((x) => x.voucherType === 'Sales'))?.voucherNumber || '';
    v.narration = 'Sales return — damaged goods';
    v.amount = grand;
  }
  pushVoucher(v);
  return v;
}

function generateHistory() {
  const today = fmtYmd(new Date());
  const start = fyStart();
  let d = start;
  let guard = 0;
  while (d <= today && guard++ < 400) {
    const wd = new Date(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8)).getDay();
    const working = wd !== 0; // closed Sundays
    if (working) {
      const nSales = randInt(0, 3);
      for (let i = 0; i < nSales; i++) makeTradingVoucher('Sales', d);
      if (rnd() < 0.35) makeTradingVoucher('Purchase', d);
      if (rnd() < 0.2) makeTradingVoucher('Credit Note', d);
      // Receipts from debtors
      if (rnd() < 0.7) {
        const debtors = ledgers.filter((l) => l.parent === 'Sundry Debtors');
        const p = pick(debtors);
        const amt = round2(randInt(20000, 300000) / 100 * 100);
        const bank = pick(['Cash', 'HDFC Bank — Current A/c 5512', 'ICICI Bank — OD A/c 9930']);
        vchSeq['Receipt'] += 1;
        pushVoucher({
          voucherType: 'Receipt', voucherNumber: `RCPT/${String(vchSeq['Receipt']).padStart(4, '0')}`,
          date: d, party: p.name, amount: amt, mode: pick(['Cash', 'NEFT', 'UPI', 'Cheque']),
          narration: 'Against bills', entries: [
            { ledger: bank, amount: amt, debit: true },
            { ledger: p.name, amount: amt, debit: false, billAllocation: 'On Account' },
          ], status: 'Active', createdAt: new Date().toISOString(),
        });
      }
      // Payments
      if (rnd() < 0.6) {
        const targets = ['Rent', 'Salaries & Wages', 'Electricity Charges', 'Telephone & Internet',
          'Travelling Expenses', 'Professional Fees', 'Freight & Courier', 'Nova Impex Pvt Ltd', 'Glow Industries'];
        const t = pick(targets);
        const amt = round2(randInt(5000, 120000) / 100 * 100);
        const src = pick(['Cash', 'HDFC Bank — Current A/c 5512', 'ICICI Bank — OD A/c 9930']);
        vchSeq['Payment'] += 1;
        pushVoucher({
          voucherType: 'Payment', voucherNumber: `PMT/${String(vchSeq['Payment']).padStart(4, '0')}`,
          date: d, party: t, amount: amt, mode: pick(['Cash', 'NEFT', 'UPI', 'Cheque']),
          narration: pick(['Monthly expenses', 'Bill settlement', 'Utilities', 'Operational']),
          entries: [
            { ledger: t, amount: amt, debit: true },
            { ledger: src, amount: amt, debit: false },
          ], status: 'Active', createdAt: new Date().toISOString(),
        });
      }
      // Contra (cash deposit/withdrawal)
      if (rnd() < 0.18) {
        const deposit = rnd() < 0.5;
        const amt = round2(randInt(30000, 150000) / 100 * 100);
        const bank = pick(['HDFC Bank — Current A/c 5512', 'ICICI Bank — OD A/c 9930']);
        vchSeq['Contra'] += 1;
        pushVoucher({
          voucherType: 'Contra', voucherNumber: `CTR/${String(vchSeq['Contra']).padStart(4, '0')}`,
          date: d, party: deposit ? 'Cash' : bank, amount: amt, mode: 'Transfer',
          narration: deposit ? 'Cash deposited' : 'Cash withdrawn',
          entries: deposit
            ? [{ ledger: bank, amount: amt, debit: true }, { ledger: 'Cash', amount: amt, debit: false }]
            : [{ ledger: 'Cash', amount: amt, debit: true }, { ledger: bank, amount: amt, debit: false }],
          status: 'Active', createdAt: new Date().toISOString(),
        });
      }
    }
    d = addDays(d, 1);
  }
  vouchers.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
}
generateHistory();

/* -------------------------------------------------------------------------- */
/*  Balance / report computation                                               */
/* -------------------------------------------------------------------------- */

/** Dr-positive / Cr-negative closing balance for every ledger. */
function computeBalances(asOnYmd) {
  const bal = {};
  for (const l of ledgers) {
    bal[l.name] = l.openingBalance.drCr === 'Cr'
      ? -(l.openingBalance.amount || 0)
      : (l.openingBalance.amount || 0);
  }
  for (const v of vouchers) {
    if (asOnYmd && v.date > asOnYmd) continue;
    for (const e of v.entries) {
      bal[e.ledger] = (bal[e.ledger] || 0) + (e.debit ? round2(e.amount) : -round2(e.amount));
    }
  }
  return bal;
}

const groupNature = (name) => GROUPS.find((g) => g.name === name)?.nature || 'Primary';

function inRange(v, from, to) {
  return (!from || v.date >= from) && (!to || v.date <= to);
}

const api = {
  companyInfo: () => ({ ...COMPANY, ledgerCount: ledgers.length, voucherCount: vouchers.length }),

  listLedgers: () => ledgers.map((l) => ({ ...l })),
  findLedger: (name) => {
    const l = ledgers.find((x) => x.name.toLowerCase() === String(name).toLowerCase());
    return l ? { ...l } : null;
  },
  listGroups: () => GROUPS.map((g) => ({ ...g })),
  listStockItems: () => STOCK_ITEMS.map((s) => ({
    ...s,
    closingBalance: s.closingQty,
    closingValue: round2(s.closingQty * s.rate),
  })),
  listStockGroups: () => [...new Set(STOCK_ITEMS.map((s) => s.group))].map((g) => ({ name: g })),

  createLedger(data) {
    if (api.findLedger(data.name)) throw Object.assign(new Error(`Ledger "${data.name}" already exists`), { statusCode: 409 });
    ledgers.push({
      name: data.name, parent: data.parent || 'Sundry Debtors',
      openingBalance: { amount: Number(data.openingBalance) || 0, drCr: data.drCr || 'Dr' },
      gstin: data.gstin || '', state: data.state || '', regType: data.regType || 'Regular',
      address: data.address || '', city: data.city || '', pincode: data.pincode || '',
      phone: data.phone || '', email: data.email || '',
    });
    return { created: true, name: data.name };
  },
  updateLedger(name, patch) {
    const l = ledgers.find((x) => x.name === name);
    if (!l) throw Object.assign(new Error(`Ledger "${name}" not found`), { statusCode: 404 });
    Object.assign(l, patch);
    if (patch.openingBalance !== undefined) {
      l.openingBalance = { amount: Number(patch.openingBalance) || 0, drCr: patch.drCr || l.openingBalance.drCr };
    }
    return { altered: true, name: l.name };
  },
  deleteLedger(name) {
    const i = ledgers.findIndex((x) => x.name === name);
    if (i < 0) throw Object.assign(new Error(`Ledger "${name}" not found`), { statusCode: 404 });
    if (vouchers.some((v) => v.entries.some((e) => e.ledger === name))) {
      throw Object.assign(new Error(`Cannot delete "${name}" — vouchers reference it. Delete/disable those vouchers first.`), { statusCode: 409 });
    }
    ledgers.splice(i, 1);
    return { deleted: true };
  },

  listVouchers: (f = {}) => {
    let out = vouchers.filter((v) =>
      (!f.from || v.date >= f.from) && (!f.to || v.date <= f.to) &&
      (!f.type || v.voucherType.toLowerCase() === f.type.toLowerCase()) &&
      (!f.party || (v.party || '').toLowerCase().includes(f.party.toLowerCase())));
    if (f.limit) out = out.slice(0, Number(f.limit));
    return out.map((v) => ({ ...v, entries: v.entries.map((e) => ({ ...e })) }));
  },
  getVoucher: (id) => {
    const v = vouchers.find((x) => x.id === id || x.voucherNumber === id);
    return v ? JSON.parse(JSON.stringify(v)) : null;
  },
  nextVoucherNumber: (type, prefix = '') => {
    const t = type || 'Sales';
    const seq = vouchers.filter((v) => v.voucherType === t).length + 1;
    const tag = { Sales: 'INV', Purchase: 'PUR', Payment: 'PMT', Receipt: 'RCPT', Contra: 'CTR', Journal: 'JV', 'Credit Note': 'CR', 'Debit Note': 'DR' }[t] || 'VCH';
    return `${prefix || ''}${tag}/${String(seq).padStart(4, '0')}`;
  },
  insertVoucher(v) {
    // Duplicate detection: same type+party+amount+date
    const dupe = vouchers.find((x) => x.voucherType === v.voucherType && x.party === v.party &&
      x.amount === v.amount && x.date === v.date);
    if (dupe && !v.force) {
      throw Object.assign(new Error(`Possible duplicate: ${v.voucherType} #${dupe.voucherNumber} for ${v.party} with the same amount & date exists.`), { statusCode: 409, code: 'DUPLICATE' });
    }
    pushVoucher(v);
    vouchers.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
    return { created: true, voucherNumber: v.voucherNumber, id: v.id };
  },
  updateVoucher(id, patch) {
    const v = vouchers.find((x) => x.id === id);
    if (!v) throw Object.assign(new Error('Voucher not found'), { statusCode: 404 });
    Object.assign(v, patch);
    return { altered: true, voucherNumber: v.voucherNumber };
  },
  deleteVoucher(id) {
    const i = vouchers.findIndex((x) => x.id === id);
    if (i < 0) throw Object.assign(new Error('Voucher not found'), { statusCode: 404 });
    vouchers.splice(i, 1);
    return { deleted: true };
  },

  trialBalance: (from, to) => {
    const bal = computeBalances(to);
    const rows = ledgers
      .filter((l) => Math.abs(round2(bal[l.name] || 0)) >= 0.01)
      .map((l) => ({ name: l.name, group: l.parent, debit: bal[l.name] > 0 ? round2(bal[l.name]) : 0, credit: bal[l.name] < 0 ? round2(-bal[l.name]) : 0 }));
    const debit = round2(rows.reduce((s, r) => s + r.debit, 0));
    const credit = round2(rows.reduce((s, r) => s + r.credit, 0));
    return { asOn: tallyToDisplay(to || fmtYmd(new Date())), rows, totalDebit: debit, totalCredit: credit, balanced: Math.abs(debit - credit) < 1 };
  },

  profitLoss: (from, to) => {
    const vs = vouchers.filter((v) => inRange(v, from, to));
    // Dr-positive / Cr-negative net of every posting into a group.
    const sum = (group) => {
      let t = 0;
      for (const v of vs) {
        for (const e of v.entries) {
          const l = ledgers.find((x) => x.name === e.ledger);
          if (l && l.parent === group) t += e.debit ? e.amount : -e.amount;
        }
      }
      return round2(t);
    };
    const sales = -sum('Sales Accounts');          // credits → positive sales
    const purchases = sum('Purchase Accounts');    // debits  → positive purchases
    const directExp = sum('Direct Expenses');
    const grossProfit = round2(sales - purchases - directExp);
    const indirectInc = -sum('Indirect Incomes');
    const indirectExp = sum('Indirect Expenses');
    const netProfit = round2(grossProfit + indirectInc - indirectExp);
    const detail = (group) => {
      const m = {};
      for (const v of vs) for (const e of v.entries) {
        const l = ledgers.find((x) => x.name === e.ledger);
        if (l && l.parent === group) m[e.ledger] = round2((m[e.ledger] || 0) + (e.debit ? e.amount : -e.amount));
      }
      return Object.entries(m).map(([name, amt]) => ({ name, amount: round2(Math.abs(amt)) }));
    };
    return {
      from: tallyToDisplay(from), to: tallyToDisplay(to),
      sales, purchases, directExpenses: directExp, grossProfit,
      indirectIncomes: indirectInc, indirectExpenses: indirectExp, netProfit,
      indirectExpenseDetail: detail('Indirect Expenses'),
      indirectIncomeDetail: detail('Indirect Incomes'),
    };
  },

  balanceSheet: (asOn) => {
    const bal = computeBalances(asOn);
    const ASSET_GROUPS = ['Sundry Debtors', 'Cash-in-Hand', 'Bank Accounts', 'Fixed Assets', 'Investments', 'Stock-in-Hand', 'Loans & Advances (Asset)'];
    const LIAB_GROUPS = ['Capital Account', 'Loans (Liability)', 'Sundry Creditors', 'Duties & Taxes', 'Current Liabilities', 'Provisions'];
    const assets = [], liabilities = [];
    // Side classification uses the SIGN of the closing balance (Dr = asset,
    // Cr = liability) — so bank ODs sit on the liability side, drawings and
    // creditor-debits on the asset side, exactly like Tally presents them.
    for (const l of ledgers) {
      const b = round2(bal[l.name] || 0);
      if (Math.abs(b) < 0.01) continue;
      const isAssetGroup = ASSET_GROUPS.includes(l.parent);
      const isLiabGroup = LIAB_GROUPS.includes(l.parent);
      if (!isAssetGroup && !isLiabGroup) continue; // income/expense → P&L
      // A DEBIT balance is always shown on the asset side, a CREDIT balance
      // on the liability side — group membership only gates inclusion.
      const row = { group: l.parent, name: l.name, amount: Math.abs(b) };
      if (b > 0) assets.push(row); else liabilities.push(row);
    }
    const stockValue = round2(STOCK_ITEMS.reduce((s, i) => s + i.closingQty * i.rate, 0));
    if (stockValue) assets.push({ group: 'Stock-in-Hand', name: 'Closing Stock (computed)', amount: stockValue });
    const totalAssets = round2(assets.reduce((s, a) => s + a.amount, 0));
    const totalLiabilities = round2(liabilities.reduce((s, a) => s + a.amount, 0));
    // P&L as shown on a Tally balance sheet includes the closing-stock
    // adjustment (Dr Closing Stock / Cr P&L), which is why the sheet balances.
    const plLedger = api.profitLoss(fyStart(asOn), asOn).netProfit;
    const pl = round2(plLedger + stockValue);
    return {
      asOn: tallyToDisplay(asOn),
      assets, liabilities,
      totalAssets, totalLiabilities,
      netProfit: pl,
      differenceInOpeningBalances: round2(totalAssets - (totalLiabilities + pl)),
    };
  },

  daybook: (from, to, limit = 100) =>
    vouchers.filter((v) => inRange(v, from, to)).slice(0, Number(limit)).map((v) => ({
      id: v.id, date: v.date, dateDisplay: v.dateDisplay, voucherType: v.voucherType,
      voucherNumber: v.voucherNumber, party: v.party, amount: v.amount, narration: v.narration,
    })),

  ledgerReport: (name, from, to) => {
    const l = api.findLedger(name);
    if (!l) throw Object.assign(new Error(`Ledger "${name}" not found`), { statusCode: 404 });
    let opening = l.openingBalance.drCr === 'Cr' ? -(l.openingBalance.amount || 0) : (l.openingBalance.amount || 0);
    const rows = [];
    for (const v of vouchers) {
      for (const e of v.entries) {
        if (e.ledger !== l.name) continue;
        if (v.date < from) opening += e.debit ? e.amount : -e.amount;
        else if (v.date <= to) rows.push({ date: v.date, dateDisplay: v.dateDisplay, voucherType: v.voucherType, voucherNumber: v.voucherNumber, debit: e.debit ? e.amount : 0, credit: e.debit ? 0 : e.amount, narration: v.narration });
      }
    }
    rows.sort((a, b) => (a.date < b.date ? -1 : 1));
    const totalDr = round2(rows.reduce((s, r) => s + r.debit, 0));
    const totalCr = round2(rows.reduce((s, r) => s + r.credit, 0));
    const closing = round2(opening + totalDr - totalCr);
    return {
      ledger: l.name, group: l.parent, gstin: l.gstin, state: l.state,
      from: tallyToDisplay(from), to: tallyToDisplay(to),
      opening: round2(opening), rows, totalDr, totalCr, closing,
      closingDrCr: closing >= 0 ? 'Dr' : 'Cr',
    };
  },

  outstanding: (asOn) => {
    const bal = computeBalances(asOn);
    const receivables = ledgers.filter((l) => l.parent === 'Sundry Debtors' && (bal[l.name] || 0) > 0.01)
      .map((l) => ({ name: l.name, amount: round2(bal[l.name]), gstin: l.gstin, state: l.state, days: randInt(0, 90) }));
    const payables = ledgers.filter((l) => l.parent === 'Sundry Creditors' && (bal[l.name] || 0) < -0.01)
      .map((l) => ({ name: l.name, amount: round2(-bal[l.name]), gstin: l.gstin, state: l.state, days: randInt(0, 75) }));
    return {
      asOn: tallyToDisplay(asOn),
      receivables, payables,
      totalReceivables: round2(receivables.reduce((s, r) => s + r.amount, 0)),
      totalPayables: round2(payables.reduce((s, r) => s + r.amount, 0)),
    };
  },

  gstSummary: (from, to) => {
    const vs = vouchers.filter((v) => inRange(v, from, to) && ['Sales', 'Purchase', 'Credit Note', 'Debit Note'].includes(v.voucherType));
    const agg = { taxable: 0, cgst: 0, sgst: 0, igst: 0, invoices: 0 };
    const outward = [], inward = [];
    for (const v of vs) {
      const rec = { date: v.dateDisplay, number: v.voucherNumber, party: v.party, gstin: v.partyGstin || '', taxable: v.taxable || v.amount, cgst: v.cgst || 0, sgst: v.sgst || 0, igst: v.igst || 0, total: v.amount };
      if (['Sales', 'Credit Note'].includes(v.voucherType)) { outward.push(rec); if (v.voucherType === 'Sales') { agg.taxable += rec.taxable; agg.cgst += rec.cgst; agg.sgst += rec.sgst; agg.igst += rec.igst; agg.invoices++; } }
      else inward.push(rec);
    }
    const r2 = round2;
    return {
      from: tallyToDisplay(from), to: tallyToDisplay(to),
      gstr1: { invoices: outward, totals: { taxable: r2(outward.reduce((s, x) => s + x.taxable, 0)), cgst: r2(outward.reduce((s, x) => s + x.cgst, 0)), sgst: r2(outward.reduce((s, x) => s + x.sgst, 0)), igst: r2(outward.reduce((s, x) => s + x.igst, 0)) } },
      gstr3b: { supplies: inward, totals: { taxable: r2(inward.reduce((s, x) => s + x.taxable, 0)), igst: r2(inward.reduce((s, x) => s + x.igst, 0)), cgst: r2(inward.reduce((s, x) => s + x.cgst, 0)), sgst: r2(inward.reduce((s, x) => s + x.sgst, 0)) } },
    };
  },

  /** Everything the dashboard needs in one round-trip. */
  dashboardSummary: () => {
    const today = fmtYmd(new Date());
    const monthStart = today.slice(0, 6) + '01';
    const yearStart = fyStart();
    const sumType = (type, from) => round2(vouchers.filter((v) => v.voucherType === type && v.date >= from && v.date <= today).reduce((s, v) => s + v.amount, 0));
    const bal = computeBalances(today);
    const banks = ledgers.filter((l) => l.parent === 'Bank Accounts').map((l) => ({ name: l.name, balance: round2(bal[l.name] || 0) }));
    const out = api.outstanding(today);
    const cash = round2(bal['Cash'] || 0);

    // 6-month sales vs purchase
    const months = [];
    let m = addDays(today, -182);
    const byMonth = {};
    for (let i = 0; i < 7; i++) {
      const key = m.slice(0, 6);
      byMonth[key] = { label: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m.slice(4, 6) - 1], sales: 0, purchase: 0 };
      m = addDays(m, 31);
    }
    for (const v of vouchers) {
      const key = v.date.slice(0, 6);
      if (byMonth[key]) {
        if (v.voucherType === 'Sales') byMonth[key].sales = round2(byMonth[key].sales + v.amount);
        if (v.voucherType === 'Purchase') byMonth[key].purchase = round2(byMonth[key].purchase + v.amount);
      }
    }
    Object.entries(byMonth).forEach(([k, x]) => months.push(x));

    // Expense breakdown (this FY)
    const expenses = {};
    for (const v of vouchers.filter((x) => x.date >= yearStart)) {
      for (const e of v.entries) {
        const l = ledgers.find((x2) => x2.name === e.ledger);
        if (l && l.parent === 'Indirect Expenses' && e.debit) expenses[e.ledger] = round2((expenses[e.ledger] || 0) + e.amount);
      }
    }

    // Cash flow: last 30 days receipts minus payments
    const cashflow = [];
    for (let i = 29; i >= 0; i--) {
      const d = addDays(today, -i);
      let inflow = 0, outflow = 0;
      for (const v of vouchers.filter((x) => x.date === d)) {
        for (const e of v.entries) {
          if (['Cash', 'HDFC Bank — Current A/c 5512', 'ICICI Bank — OD A/c 9930'].includes(e.ledger)) {
            if (e.debit) inflow = round2(inflow + e.amount); else outflow = round2(outflow + e.amount);
          }
        }
      }
      cashflow.push({ date: tallyToDisplay(d), inflow, outflow, net: round2(inflow - outflow) });
    }

    const expenseTotal = round2(Object.values(expenses).reduce((s, x) => s + x, 0));
    return {
      company: COMPANY.name, financialYear: COMPANY.financialYearFrom + ' to ' + COMPANY.booksEndingOn,
      stats: {
        salesToday: sumType('Sales', today), salesMonth: sumType('Sales', monthStart), salesYear: sumType('Sales', yearStart),
        purchaseToday: sumType('Purchase', today), purchaseMonth: sumType('Purchase', monthStart), purchaseYear: sumType('Purchase', yearStart),
        cashInHand: cash,
        bankBalance: round2(banks.reduce((s, b) => s + b.balance, 0)), banks,
        receivables: out.totalReceivables, payables: out.totalPayables,
      },
      months, expenses: Object.entries(expenses).map(([name, amount]) => ({ name, amount, share: expenseTotal ? round2((amount / expenseTotal) * 100) : 0 })),
      cashflow,
      recent: vouchers.slice(0, 20).map((v) => ({
        id: v.id, date: v.dateDisplay, voucherType: v.voucherType, voucherNumber: v.voucherNumber,
        party: v.party, amount: v.amount, narration: v.narration,
      })),
    };
  },
};

module.exports = api;
