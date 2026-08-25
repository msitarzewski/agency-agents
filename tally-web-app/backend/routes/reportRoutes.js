/**
 * ============================================================================
 * REPORT ROUTES — /api/reports/*
 * ============================================================================
 * Channel strategy per report:
 *   • Trial Balance can come from ODBC (fast, deterministic) when installed;
 *     everything else uses the XML Export API.
 *   • Whatever the channel, an unreachable Tally + demoMode=auto serves the
 *     computed demo dataset so the UI never blanks out.
 * ============================================================================
 */
const express = require('express');
const tally = require('../services/tallyXMLService');
const odbc = require('../services/odbcService');
const { asyncHandler, fyStart, todayTally } = require('../utils/helpers');

const router = express.Router();

/** Default period = current Indian financial year. */
function period(req) {
  return {
    from: req.query.from || fyStart(),
    to: req.query.to || todayTally(),
  };
}

/** GET /api/reports/trial-balance?from&to */
router.get('/trial-balance', asyncHandler(async (req, res) => {
  let out = null;
  if (req.query.channel !== 'xml') {
    try {
      const rows = await odbc.trialBalance();
      const totalDebit = rows.reduce((s, r) => s + r.debit, 0);
      const totalCredit = rows.reduce((s, r) => s + r.credit, 0);
      out = { data: { rows, totalDebit, totalCredit, balanced: Math.abs(totalDebit - totalCredit) < 1 }, source: 'odbc' };
    } catch { /* ODBC absent → XML */ }
  }
  if (!out) out = await tally.getReport('trial-balance', period(req));
  res.json({ success: true, data: out.data, source: out.source });
}));

/** GET /api/reports/profit-loss?from&to */
router.get('/profit-loss', asyncHandler(async (req, res) => {
  const out = await tally.getReport('profit-loss', period(req));
  res.json({ success: true, data: out.data, source: out.source });
}));

/** GET /api/reports/balance-sheet?to */
router.get('/balance-sheet', asyncHandler(async (req, res) => {
  const out = await tally.getReport('balance-sheet', { to: req.query.to || todayTally() });
  res.json({ success: true, data: out.data, source: out.source });
}));

/** GET /api/reports/daybook?from&to&limit */
router.get('/daybook', asyncHandler(async (req, res) => {
  const out = await tally.getReport('daybook', { ...period(req), limit: req.query.limit || 200 });
  res.json({ success: true, data: out.data, source: out.source, count: out.data.length });
}));

/** GET /api/reports/ledger/:name?from&to */
router.get('/ledger/:name', asyncHandler(async (req, res) => {
  const out = await tally.getReport('ledger-report', { ...period(req), ledger: req.params.name });
  res.json({ success: true, data: out.data, source: out.source });
}));

/** GET /api/reports/outstanding?to — receivables + payables */
router.get('/outstanding', asyncHandler(async (req, res) => {
  const out = await tally.getReport('outstanding', { to: req.query.to || todayTally() });
  res.json({ success: true, data: out.data, source: out.source });
}));

/** GET /api/reports/gst-summary?from&to — GSTR-1 & GSTR-3B style summary */
router.get('/gst-summary', asyncHandler(async (req, res) => {
  const out = await tally.getReport('gst-summary', period(req));
  res.json({ success: true, data: out.data, source: out.source });
}));

module.exports = router;
