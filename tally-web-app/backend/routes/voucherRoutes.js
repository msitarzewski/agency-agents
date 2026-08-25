/**
 * ============================================================================
 * VOUCHER ROUTES — /api/vouchers
 * ============================================================================
 * Write-path behaviour (the offline-queue contract):
 *   1. Try to push the voucher to Tally through the XML API.
 *   2. If Tally is unreachable and demoMode='auto', the write lands in the
 *      local demo store AND is enqueued for replay — the user sees a toast
 *      "Saved locally — will sync to Tally" and the queue badge increments.
 *   3. When the sync engine reconnects, queued ops are flushed automatically.
 * ============================================================================
 */
const express = require('express');
const tally = require('../services/tallyXMLService');
const sync = require('../services/syncService');
const { getTallyConfig } = require('../config/tallyConfig');
const { asyncHandler } = require('../utils/helpers');
const { validateVoucher } = require('../middleware/validator');

const router = express.Router();

/** Inject the voucher type from the URL path before validation runs. */
const withType = (type) => (req, res, next) => { req.body = { ...req.body, type }; next(); };

/** Wrap a create call with the queue contract described above. */
async function createWithQueue(type, req, res) {
  const payload = { ...req.body, type };
  const cfg = getTallyConfig();
  try {
    const result = await tally.createVoucher(payload);
    const queued =
      result.source === 'demo' && cfg.demoMode === 'auto' &&
      sync.enqueue({
        kind: 'voucher', op: 'create', payload,
        label: `${payload.type} #${result.data.voucherNumber || ''} ${payload.party || ''}`.trim(),
      });
    return res.status(201).json({
      success: true,
      data: result.data,
      source: result.source,
      queued: !!queued || undefined,
      message: queued
        ? 'Saved offline — queued to push to Tally when it reconnects'
        : result.source === 'tally'
          ? 'Voucher pushed to Tally successfully'
          : 'Saved (demo mode)',
    });
  } catch (err) {
    // Unreachable AND demo fallback disabled → explicitly queue.
    if (err.tallyUnreachable && cfg.demoMode === 'never') {
      const item = sync.enqueue({
        kind: 'voucher', op: 'create', payload,
        label: `${type} ${payload.party || ''}`.trim(),
      });
      return res.status(202).json({
        success: true,
        queued: true,
        data: { queueId: item.id },
        message: 'Tally unreachable — entry queued and will be pushed on reconnect',
      });
    }
    if (err.statusCode === 409 && err.code === 'DUPLICATE') {
      return res.status(409).json({ success: false, error: { code: 'DUPLICATE', message: err.message }, data: { confirmField: 'force' } });
    }
    throw err;
  }
}

/* ------------------------------- READS ----------------------------------- */

/** GET /api/vouchers?from&to&type&party&limit */
router.get('/', asyncHandler(async (req, res) => {
  const result = await tally.getVouchers(req.query);
  res.json({ success: true, data: result.data, source: result.source, count: result.data.length });
}));

/** GET /api/vouchers/next-number?voucherType=Sales — auto numbering for forms */
router.get('/next-number', asyncHandler(async (req, res) => {
  const settings = require('../utils/settingsStore').get();
  const result = await tally.getNextVoucherNumber(
    req.query.voucherType || 'Sales', req.query.prefix ?? settings.invoicePrefix ?? ''
  );
  res.json({ success: true, data: { voucherNumber: result.data }, source: result.source });
}));

/** GET /api/vouchers/:id */
router.get('/:id', asyncHandler(async (req, res) => {
  const result = await tally.getVoucherById(req.params.id);
  res.json({ success: true, data: result.data, source: result.source });
}));

/* ------------------------------- WRITES ---------------------------------- */

router.post('/sales', withType('sales'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('sales', req, res)));
router.post('/purchase', withType('purchase'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('purchase', req, res)));
router.post('/payment', withType('payment'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('payment', req, res)));
router.post('/receipt', withType('receipt'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('receipt', req, res)));
router.post('/contra', withType('contra'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('contra', req, res)));
router.post('/journal', withType('journal'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('journal', req, res)));
router.post('/credit-note', withType('credit-note'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('credit-note', req, res)));
router.post('/debit-note', withType('debit-note'), validateVoucher, asyncHandler(async (req, res) => createWithQueue('debit-note', req, res)));

/** PUT /api/vouchers/:id — alteration with conflict baseline */
router.put('/:id', (req, res, next) => { if (!req.body.type) req.body.type = 'journal'; next(); }, validateVoucher, asyncHandler(async (req, res) => {
  const payload = { ...req.body, type: req.body.type };
  const cfg = getTallyConfig();
  let baseline = null;
  try {
    const cur = await tally.getVoucherById(req.params.id);
    baseline = cur.source === 'tally' ? { amount: cur.data.amount, date: cur.data.date } : null;
  } catch { /* new-ish id */ }
  try {
    const result = await tally.updateVoucher(req.params.id, payload);
    res.json({ success: true, data: result.data, source: result.source, message: 'Voucher updated in Tally' });
  } catch (err) {
    if (err.tallyUnreachable) {
      sync.enqueue({
        kind: 'voucher', op: 'update', payload, targetId: req.params.id, baseline,
        label: `Alter ${req.body.type || 'voucher'} ${req.params.id}`,
      });
      return res.status(202).json({ success: true, queued: true, message: 'Tally unreachable — alteration queued' });
    }
    throw err;
  }
}));

/** DELETE /api/vouchers/:id */
router.delete('/:id', asyncHandler(async (req, res) => {
  const cfg = getTallyConfig();
  try {
    const result = await tally.deleteVoucher(req.params.id);
    res.json({ success: true, data: result.data, source: result.source, message: 'Voucher deleted' });
  } catch (err) {
    if (err.tallyUnreachable && cfg.demoMode === 'never') {
      sync.enqueue({ kind: 'voucher', op: 'delete', payload: {}, targetId: req.params.id, label: `Delete voucher ${req.params.id}` });
      return res.status(202).json({ success: true, queued: true, message: 'Deletion queued' });
    }
    throw err;
  }
}));

module.exports = router;
