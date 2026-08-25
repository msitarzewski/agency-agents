/**
 * ============================================================================
 * SHARED HELPERS — dates, money, GST, GSTIN, words, async wrapper
 * ============================================================================
 * Tally-specific conventions handled here (see "IMPORTANT NOTES" in spec):
 *   • Display date format  : DD-MM-YYYY
 *   • Tally XML date format: YYYYMMDD
 *   • Debit  → ISDEEMEDPOSITIVE = Yes, AMOUNT negative
 *   • Credit → ISDEEMEDPOSITIVE = No,  AMOUNT positive
 * ============================================================================
 */

/* -------------------------------------------------------------------------- */
/*  Async route wrapper — forwards rejected promises to Express error handler  */
/* -------------------------------------------------------------------------- */
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

/* -------------------------------------------------------------------------- */
/*  DATES                                                                      */
/* -------------------------------------------------------------------------- */

/** DD-MM-YYYY | YYYY-MM-DD | Date → Tally's YYYYMMDD string. */
function toTallyDate(input) {
  if (!input) return todayTally();
  const s = String(input).trim();
  let m;
  if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/))) return `${m[1]}${m[2]}${m[3]}`;
  if ((m = s.match(/^(\d{2})-(\d{2})-(\d{4})$/))) return `${m[3]}${m[2]}${m[1]}`;
  if (/^\d{8}$/.test(s)) return s;
  const d = new Date(s);
  if (!isNaN(d)) return fmtYmd(d);
  throw new Error(`Unrecognised date: ${input}`);
}

/** YYYYMMDD → "DD-MM-YYYY" for display. */
function tallyToDisplay(ymd) {
  const s = String(ymd || '');
  if (!/^\d{8}$/.test(s)) return s;
  return `${s.slice(6, 8)}-${s.slice(4, 6)}-${s.slice(0, 4)}`;
}

function fmtYmd(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`;
}

function todayTally() {
  return fmtYmd(new Date());
}

/** Indian financial-year start (1 April) for a Date or YYYYMMDD string. */
function fyStart(date = new Date()) {
  const d = typeof date === 'string' && /^\d{8}$/.test(date)
    ? new Date(+date.slice(0, 4), +date.slice(4, 6) - 1, +date.slice(6, 8))
    : new Date(date);
  const y = d.getMonth() + 1 >= 4 ? d.getFullYear() : d.getFullYear() - 1;
  return fmtYmd(new Date(y, 3, 1)); // Apr 1
}

/** Indian financial-year end (31 March). */
function fyEnd(date = new Date()) {
  const d = typeof date === 'string' && /^\d{8}$/.test(date)
    ? new Date(+date.slice(0, 4), +date.slice(4, 6) - 1, +date.slice(6, 8))
    : new Date(date);
  const y = d.getMonth() + 1 >= 4 ? d.getFullYear() + 1 : d.getFullYear();
  return fmtYmd(new Date(y, 2, 31)); // Mar 31
}

/** Human-readable FY label, e.g. "1-Apr-2025 to 31-Mar-2026" (Tally style). */
function fyLabel(date = new Date()) {
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const parts = (ymd) => {
    const d = new Date(+ymd.slice(0, 4), +ymd.slice(4, 6) - 1, +ymd.slice(6, 8));
    return { day: d.getDate(), mon: MONTHS[d.getMonth()], year: d.getFullYear() };
  };
  const a = parts(fyStart(date));
  const b = parts(fyEnd(date));
  return `${a.day}-${a.mon}-${a.year} to ${b.day}-${b.mon}-${b.year}`;
}

/* -------------------------------------------------------------------------- */
/*  MONEY                                                                      */
/* -------------------------------------------------------------------------- */

/** Round to 2 decimals — use everywhere before pushing amounts to Tally. */
const round2 = (n) => Math.round((Number(n) + Number.EPSILON) * 100) / 100;

/**
 * Indian-format a number with ₹ grouping: 1,00,000.00
 * Used for server-side renders/logs; the browser has a matching formatter.
 */
function formatINR(n, withSymbol = true) {
  const neg = n < 0;
  const x = Math.abs(round2(n)).toFixed(2).split('.');
  let last3 = x[0].slice(-3);
  const rest = x[0].slice(0, -3);
  if (rest) last3 = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
  return `${neg ? '-' : ''}${withSymbol ? '₹' : ''}${last3}.${x[1]}`;
}

/* -------------------------------------------------------------------------- */
/*  GST / GSTIN                                                                */
/* -------------------------------------------------------------------------- */

/** GST state codes (first 2 digits of a GSTIN) → state name. */
const GST_STATE_CODES = {
  '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
  '04': 'Chandigarh', '05': 'Uttarakhand', '06': 'Haryana', '07': 'Delhi',
  '08': 'Rajasthan', '09': 'Uttar Pradesh', '10': 'Bihar', '11': 'Sikkim',
  '12': 'Arunachal Pradesh', '13': 'Nagaland', '14': 'Manipur',
  '15': 'Mizoram', '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam',
  '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha',
  '22': 'Chattisgarh', '23': 'Madhya Pradesh', '24': 'Gujarat',
  '26': 'Dadra and Nagar Haveli and Daman and Diu', '27': 'Maharashtra',
  '29': 'Karnataka', '30': 'Goa', '31': 'Lakshadweep', '32': 'Kerala',
  '33': 'Tamil Nadu', '34': 'Puducherry', '35': 'Andaman and Nicobar Islands',
  '36': 'Telangana', '37': 'Andhra Pradesh', '38': 'Ladakh',
  '97': 'Other Territory', '99': 'Centre Jurisdiction',
};

/** State name → GST code (reverse map). */
const STATE_TO_CODE = Object.fromEntries(
  Object.entries(GST_STATE_CODES).map(([c, s]) => [s.toLowerCase(), c])
);

/** Validate a 15-char GSTIN: 2-digit state + PAN + 3 chars + checksum digit. */
function isValidGSTIN(g) {
  if (!g) return false;
  return /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(g.toUpperCase());
}

/** Extract the state name from a GSTIN's first two digits. */
function stateFromGSTIN(g) {
  if (!g || g.length < 2) return null;
  return GST_STATE_CODES[String(g).slice(0, 2)] || null;
}

/**
 * Split GST for an invoice line.
 * Intra-state (party state == company state) → CGST + SGST (half each).
 * Inter-state (different states)              → IGST (full rate).
 */
function computeGst(taxableValue, gstRatePercent, partyState, companyState) {
  const taxable = round2(taxableValue);
  const rate = Number(gstRatePercent) || 0;
  const interState =
    !!partyState && !!companyState &&
    partyState.trim().toLowerCase() !== companyState.trim().toLowerCase();
  if (rate <= 0 || taxable <= 0) {
    return { taxable, rate, igst: 0, cgst: 0, sgst: 0, interState, total: taxable };
  }
  if (interState) {
    const igst = round2((taxable * rate) / 100);
    return { taxable, rate, igst, cgst: 0, sgst: 0, interState, total: round2(taxable + igst) };
  }
  const half = round2((taxable * rate) / 100 / 2);
  // Keep CGST/SGST symmetric; absorb rounding diff into SGST.
  const cgst = half;
  const sgst = round2((taxable * rate) / 100) - cgst;
  return { taxable, rate, igst: 0, cgst, sgst, interState, total: round2(taxable + cgst + sgst) };
}

/* -------------------------------------------------------------------------- */
/*  NUMBER TO WORDS (Indian system — for invoice footers / cheque printing)    */
/* -------------------------------------------------------------------------- */
const ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
  'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen',
  'Eighteen', 'Nineteen'];
const TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

function twoDigits(n) {
  if (n < 20) return ONES[n];
  return `${TENS[Math.floor(n / 10)]}${n % 10 ? ' ' + ONES[n % 10] : ''}`;
}

function threeDigits(n) {
  const h = Math.floor(n / 100);
  const r = n % 100;
  let out = '';
  if (h) out += `${ONES[h]} Hundred`;
  if (r) out += `${h ? ' ' : ''}${twoDigits(r)}`;
  return out;
}

/** 123456.5 → "Rupees One Lakh Twenty Three Thousand Four Hundred Fifty Six and Paise Fifty Only" */
function numberToWordsIndian(amount) {
  const n = round2(Number(amount) || 0);
  const neg = n < 0;
  const abs = Math.abs(n);
  const rupees = Math.floor(abs);
  const paise = Math.round((abs - rupees) * 100);
  if (rupees === 0 && paise === 0) return 'Rupees Zero Only';

  const parts = [];
  const crore = Math.floor(rupees / 10000000);
  const lakh = Math.floor((rupees % 10000000) / 100000);
  const thousand = Math.floor((rupees % 100000) / 1000);
  const hundred = rupees % 1000;

  if (crore) parts.push(`${threeDigits(crore)} Crore`);
  if (lakh) parts.push(`${twoDigits(lakh)} Lakh`);
  if (thousand) parts.push(`${twoDigits(thousand)} Thousand`);
  if (hundred) parts.push(threeDigits(hundred));

  let words = `Rupees ${parts.join(' ')}`;
  if (paise) words += ` and Paise ${twoDigits(paise)}`;
  words += ' Only';
  return (neg ? 'Minus ' : '') + words;
}

/* -------------------------------------------------------------------------- */
/*  MISC                                                                       */
/* -------------------------------------------------------------------------- */

/** XML-safe text (Tally chokes on raw & < > in names/narrations). */
function escapeXml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, ''); // strip control chars
}

/** Compact unique id for local tracking (NOT pushed to Tally). */
let _seq = 0;
function uid(prefix = 'id') {
  _seq = (_seq + 1) % 100000;
  return `${prefix}-${Date.now().toString(36)}-${_seq.toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

/**
 * Signed amount helper for Tally XML ledger entries.
 * Debit entries → negative number + ISDEEMEDPOSITIVE=Yes.
 */
function tallyAmount(entry) {
  const amt = round2(Math.abs(entry.amount));
  return entry.debit ? -amt : amt;
}

module.exports = {
  asyncHandler,
  toTallyDate, tallyToDisplay, fmtYmd, todayTally, fyStart, fyEnd, fyLabel,
  round2, formatINR,
  GST_STATE_CODES, STATE_TO_CODE, isValidGSTIN, stateFromGSTIN, computeGst,
  numberToWordsIndian, escapeXml, uid, tallyAmount,
};
