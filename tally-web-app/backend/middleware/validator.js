/**
 * ============================================================================
 * VALIDATOR MIDDLEWARE
 * ============================================================================
 * Field-level validation performed BEFORE any XML is built — Tally error
 * messages are cryptic, so we catch problems here with human-friendly text.
 * Each validator sets req.body to a normalised copy and calls next(), or
 * responds 422 with an errors[] map the frontend highlights field-by-field.
 * ============================================================================
 */
const { isValidGSTIN, toTallyDate } = require('../utils/helpers');

function fail(res, errors) {
  return res.status(422).json({
    success: false,
    error: { code: 'VALIDATION_ERROR', message: 'Please fix the highlighted fields', errors },
  });
}

const req = (body, field, label, errors) => {
  const v = body[field];
  if (v === undefined || v === null || String(v).trim() === '') {
    errors[field] = `${label} is required`;
    return null;
  }
  return v;
};

/* -------------------------------------------------------------------------- */
/*  Ledger master                                                              */
/* -------------------------------------------------------------------------- */
function validateLedger(reqVal, res, next) {
  const b = reqVal.body;
  const errors = {};
  req(b, 'name', 'Ledger name', errors);
  if (b.name && /[<>&]/.test(b.name)) errors.name = 'Name cannot contain < > &';
  if (!req(b, 'parent', 'Under group', errors)) { /* marked */ }
  if (b.openingBalance != null && b.openingBalance !== '' && isNaN(Number(b.openingBalance))) {
    errors.openingBalance = 'Opening balance must be a number';
  }
  if (b.gstin && !isValidGSTIN(b.gstin)) errors.gstin = 'Invalid GSTIN (expected 15 characters, e.g. 27AAACS1867F1Z5)';
  if (b.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(b.email)) errors.email = 'Invalid email address';
  if (b.pincode && !/^\d{6}$/.test(b.pincode)) errors.pincode = 'PIN code must be 6 digits';
  if (Object.keys(errors).length) return fail(res, errors);
  next();
}

/* -------------------------------------------------------------------------- */
/*  Vouchers                                                                   */
/* -------------------------------------------------------------------------- */
const TRADING = ['sales', 'purchase', 'credit-note', 'debit-note'];
const SIMPLE = ['payment', 'receipt', 'contra', 'journal'];

function validateVoucher(reqVal, res, next) {
  const b = reqVal.body;
  const errors = {};
  const type = b.type;
  if (![...TRADING, ...SIMPLE].includes(type)) {
    return res.status(422).json({ success: false, error: { code: 'VALIDATION_ERROR', message: `Unknown voucher type "${type}"` } });
  }

  // Date
  try {
    if (!b.date) throw new Error();
    b._dateYmd = toTallyDate(b.date);
  } catch {
    errors.date = 'Valid date required (DD-MM-YYYY)';
  }

  if (TRADING.includes(type)) {
    req(b, 'party', 'Party ledger', errors);
    const items = (b.items || []).filter((i) => i.name);
    if (!items.length) errors.items = 'Add at least one item line';
    for (const it of items) {
      if (!(Number(it.qty) > 0)) errors.items = 'Every line needs a quantity > 0';
      if (!(Number(it.rate) >= 0)) errors.items = 'Every line needs a valid rate';
    }
    if (b.partyGstin && !isValidGSTIN(b.partyGstin)) errors.partyGstin = 'Invalid GSTIN format';
  } else {
    const entries = (b.entries || []).filter((e) => e.ledger && Number(e.amount) > 0);
    if (entries.length < 2) errors.entries = 'At least two ledger lines are required';
    const dr = entries.filter((e) => e.debit).reduce((s, e) => s + Number(e.amount), 0);
    const cr = entries.filter((e) => !e.debit).reduce((s, e) => s + Number(e.amount), 0);
    if (entries.length >= 2 && Math.abs(dr - cr) > 0.01) {
      errors.entries = `Debit total (${dr.toFixed(2)}) must equal Credit total (${cr.toFixed(2)})`;
    }
    if (type === 'payment' && !entries.some((e) => /cash|bank/i.test(e.ledger))) {
      errors.entries = 'Payment must be made from a Cash or Bank ledger';
    }
    if (type === 'receipt' && !entries.some((e) => /cash|bank/i.test(e.ledger))) {
      errors.entries = 'Receipt must be received into a Cash or Bank ledger';
    }
    if (type === 'contra' && !((/cash/i.test(entries[0]?.ledger || '') || /bank/i.test(entries[0]?.ledger || '')) && (/cash/i.test(entries[1]?.ledger || '') || /bank/i.test(entries[1]?.ledger || '')))) {
      errors.entries = 'Contra must be between a Cash and a Bank ledger';
    }
  }

  if (b.narration && String(b.narration).length > 500) errors.narration = 'Narration too long (max 500 chars)';

  if (Object.keys(errors).length) return fail(res, errors);
  next();
}

/* -------------------------------------------------------------------------- */
/*  Stock item                                                                 */
/* -------------------------------------------------------------------------- */
function validateStockItem(reqVal, res, next) {
  const b = reqVal.body;
  const errors = {};
  req(b, 'name', 'Item name', errors);
  if (b.rate != null && isNaN(Number(b.rate))) errors.rate = 'Rate must be numeric';
  if (b.openingQty != null && isNaN(Number(b.openingQty))) errors.openingQty = 'Quantity must be numeric';
  if (Object.keys(errors).length) return fail(res, errors);
  next();
}

module.exports = { validateLedger, validateVoucher, validateStockItem };
