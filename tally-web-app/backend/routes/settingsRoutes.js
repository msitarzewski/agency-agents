/**
 * ============================================================================
 * SETTINGS ROUTES — /api/settings
 * ============================================================================
 * Backs the in-app Settings page (connection, sync interval, theme, defaults).
 * Changes apply immediately — no server restart needed.
 * ============================================================================
 */
const express = require('express');
const settingsStore = require('../utils/settingsStore');
const sync = require('../services/syncService');
const { asyncHandler } = require('../utils/helpers');

const router = express.Router();

/** GET /api/settings */
router.get('/', asyncHandler(async (req, res) => {
  res.json({ success: true, data: settingsStore.get() });
}));

/** PUT /api/settings — partial merge; restarts the sync timer if needed. */
router.put('/', asyncHandler(async (req, res) => {
  const { tallyPort, syncIntervalSec } = req.body;
  if (tallyPort != null && !(Number(tallyPort) > 0 && Number(tallyPort) < 65536)) {
    return res.status(422).json({ success: false, error: { code: 'VALIDATION_ERROR', message: 'Invalid Tally port' } });
  }
  if (syncIntervalSec != null && !(Number(syncIntervalSec) >= 2 && Number(syncIntervalSec) <= 300)) {
    return res.status(422).json({ success: false, error: { code: 'VALIDATION_ERROR', message: 'Sync interval must be 2–300 seconds' } });
  }
  const before = settingsStore.get().syncIntervalSec;
  const data = settingsStore.save(req.body);
  if (req.body.syncIntervalSec && Number(req.body.syncIntervalSec) !== before) sync.onSettingsChanged();
  sync.log('System', 'Fingerprint', 'Info', 'Settings updated');
  res.json({ success: true, data, message: 'Settings saved' });
}));

/** POST /api/settings/reset */
router.post('/reset', asyncHandler(async (req, res) => {
  const data = settingsStore.reset();
  sync.onSettingsChanged();
  res.json({ success: true, data, message: 'Settings reset to defaults' });
}));

module.exports = router;
