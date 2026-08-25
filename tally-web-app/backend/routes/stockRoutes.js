/**
 * ============================================================================
 * STOCK ROUTES — /api/stock-items, /api/stock-groups
 * ============================================================================
 */
const express = require('express');
const tally = require('../services/tallyXMLService');
const odbc = require('../services/odbcService');
const { asyncHandler } = require('../utils/helpers');
const { validateStockItem } = require('../middleware/validator');

const router = express.Router();
const groupsRouter = express.Router();

/** GET /api/stock-items — ODBC first (fast closing-balance reads). */
router.get('/', asyncHandler(async (req, res) => {
  let out = null;
  if (req.query.channel !== 'xml') {
    try {
      const data = await odbc.stockItems();
      out = { data, source: 'odbc' };
    } catch { /* fall through */ }
  }
  if (!out) out = await tally.getStockItems();
  let data = out.data;
  if (req.query.q) {
    const q = String(req.query.q).toLowerCase();
    data = data.filter((i) => i.name.toLowerCase().includes(q));
  }
  res.json({ success: true, data, source: out.source, count: data.length });
}));

/** POST /api/stock-items — create stock item in Tally. */
router.post('/', validateStockItem, asyncHandler(async (req, res) => {
  const result = await tally.createStockItem(req.body);
  res.status(201).json({ success: true, data: result.data, source: result.source, message: `Stock item "${req.body.name}" created` });
}));

/** GET /api/stock-groups */
groupsRouter.get('/', asyncHandler(async (req, res) => {
  const result = await tally.getStockGroups();
  res.json({ success: true, data: result.data, source: result.source });
}));

module.exports = { router, groupsRouter };
