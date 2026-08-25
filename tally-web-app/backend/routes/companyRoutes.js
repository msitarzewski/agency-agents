/**
 * ============================================================================
 * COMPANY ROUTES — /api/company
 * ============================================================================
 */
const express = require('express');
const tally = require('../services/tallyXMLService');
const { asyncHandler } = require('../utils/helpers');

const router = express.Router();

/** GET /api/company/info — name, FY, GSTIN, address from Tally. */
router.get('/info', asyncHandler(async (req, res) => {
  const result = await tally.getCompanyInfo();
  res.json({ success: true, data: result.data, source: result.source });
}));

/** GET /api/company/test — connection probe used by the Settings page. */
router.get('/test', asyncHandler(async (req, res) => {
  try {
    const data = await tally.testConnection();
    res.json({ success: true, data, message: `Tally reachable at ${data.baseUrl}` });
  } catch (err) {
    res.status(503).json({
      success: false,
      error: {
        code: 'TALLY_UNREACHABLE',
        message: err.message,
        hint: 'Check that Tally Prime is running, the company is open, and the XML port (default 9000) matches Settings.',
      },
    });
  }
}));

module.exports = router;
