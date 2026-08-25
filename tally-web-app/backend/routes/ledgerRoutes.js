/**
 * ============================================================================
 * LEDGER ROUTES — /api/ledgers and /api/ledger-groups
 * ============================================================================
 * Reads try the ODBC channel first (fast) and fall back to the Tally XML API;
 * writes always go through XML Import (ODBC is read-only here).
 * ============================================================================
 */
const express = require('express');
const tally = require('../services/tallyXMLService');
const odbc = require('../services/odbcService');
const sync = require('../services/syncService');
const { asyncHandler } = require('../utils/helpers');
const { validateLedger } = require('../middleware/validator');

const router = express.Router();
const groupsRouter = express.Router();

/* ------------------------------- READS ----------------------------------- */

/** GET /api/ledgers?q=Sund — all ledger masters (ODBC → XML → demo). */
router.get('/', asyncHandler(async (req, res) => {
  let result = null;
  if (req.query.channel !== 'xml') {
    try {
      const data = await odbc.ledgers();
      result = { data, source: 'odbc' };
    } catch { /* fall through to XML */ }
  }
  if (!result) result = await tally.getLedgers();
  let data = result.data;
  if (req.query.q) {
    const q = String(req.query.q).toLowerCase();
    data = data.filter((l) => l.name.toLowerCase().includes(q) || (l.parent || '').toLowerCase().includes(q));
  }
  if (req.query.group) data = data.filter((l) => l.parent === req.query.group);
  res.json({ success: true, data, source: result.source, count: data.length });
}));

/** GET /api/ledgers/:name — single ledger with details. */
router.get('/:name', asyncHandler(async (req, res) => {
  const result = await tally.getLedger(req.params.name);
  res.json({ success: true, data: result.data, source: result.source });
}));

/* ------------------------------- WRITES ---------------------------------- */

/** POST /api/ledgers — create master in Tally. */
router.post('/', validateLedger, asyncHandler(async (req, res) => {
  const result = await tally.createLedger(req.body);
  sync.log('Push', 'Ledger', result.source === 'tally' ? 'Success' : 'Queued',
    `Ledger "${req.body.name}" created (${result.source})`);
  res.status(201).json({ success: true, data: result.data, source: result.source, message: `Ledger "${req.body.name}" created in ${result.source === 'tally' ? 'Tally' : 'demo store'}` });
}));

/** PUT /api/ledgers/:name */
router.put('/:name', validateLedger, asyncHandler(async (req, res) => {
  const result = await tally.updateLedger(req.params.name, req.body);
  sync.log('Push', 'Ledger', 'Success', `Ledger "${req.params.name}" altered`);
  res.json({ success: true, data: result.data, source: result.source, message: 'Ledger updated' });
}));

/** DELETE /api/ledgers/:name */
router.delete('/:name', asyncHandler(async (req, res) => {
  const result = await tally.deleteLedger(req.params.name);
  sync.log('Push', 'Ledger', 'Success', `Ledger "${req.params.name}" deleted`);
  res.json({ success: true, data: result.data, source: result.source, message: 'Ledger deleted' });
}));

/* ------------------------------- GROUPS ----------------------------------- */

/** GET /api/ledger-groups */
groupsRouter.get('/', asyncHandler(async (req, res) => {
  const result = await tally.getGroups();
  res.json({ success: true, data: result.data, source: result.source, count: result.data.length });
}));

module.exports = { router, groupsRouter };
