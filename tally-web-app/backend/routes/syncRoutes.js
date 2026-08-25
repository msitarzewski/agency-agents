/**
 * ============================================================================
 * SYNC ROUTES — /api/sync/*
 * ============================================================================
 * The status endpoint backs the dashboard's sync LED and the polling
 * fallback (browsers that cannot hold a WebSocket still stay current).
 * ============================================================================
 */
const express = require('express');
const sync = require('../services/syncService');
const { asyncHandler } = require('../utils/helpers');

const router = express.Router();

/** GET /api/sync/status */
router.get('/status', asyncHandler(async (req, res) => {
  res.json({ success: true, data: sync.getStatus() });
}));

/** POST /api/sync/manual — force a full sync cycle now. */
router.post('/manual', asyncHandler(async (req, res) => {
  const data = await sync.manualSync();
  res.json({ success: true, data, message: 'Manual sync completed' });
}));

/** GET /api/sync/logs?limit=100 */
router.get('/logs', asyncHandler(async (req, res) => {
  res.json({ success: true, data: sync.getLogs(req.query.limit || 100) });
}));

/** GET /api/sync/queue — pending offline operations. */
router.get('/queue', asyncHandler(async (req, res) => {
  res.json({ success: true, data: sync.getStatus().queue });
}));

/** POST /api/sync/queue/:id — discard one queued op (user decision). */
router.post('/queue/:id/discard', asyncHandler(async (req, res) => {
  const st = sync.state;
  const before = st.queue.length;
  st.queue = st.queue.filter((q) => q.id !== req.params.id);
  require('fs').writeFileSync(require('path').join(__dirname, '..', 'data', 'queue.json'), JSON.stringify(st.queue, null, 2));
  sync.broadcastStatus();
  res.json({ success: true, data: { discarded: before - st.queue.length } });
}));

/** GET /api/sync/conflicts — parked conflicts awaiting resolution. */
router.get('/conflicts', asyncHandler(async (req, res) => {
  res.json({ success: true, data: sync.getStatus().conflicts });
}));

/** POST /api/sync/conflicts/:id/resolve  body: {resolution:'mine'|'theirs'} */
router.post('/conflicts/:id/resolve', asyncHandler(async (req, res) => {
  const { resolution } = req.body;
  if (!['mine', 'theirs'].includes(resolution)) {
    return res.status(422).json({ success: false, error: { code: 'VALIDATION_ERROR', message: "resolution must be 'mine' or 'theirs'" } });
  }
  const data = await sync.resolveConflict(req.params.id, resolution);
  res.json({ success: true, data, message: resolution === 'mine' ? 'Your version was pushed to Tally' : 'Tally version kept' });
}));

module.exports = router;
