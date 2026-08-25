/**
 * ============================================================================
 * TALLY WEB APP — EXPRESS SERVER (main entry)
 * ============================================================================
 * Architecture:
 *
 *   Browser (HTML/JS)  ⇄ REST + Socket.IO  ⇄  this Express middleware server
 *                                             ├─ Tally XML API  :9000 (R+W)
 *                                             └─ Tally ODBC     :9001 (R)
 *
 * Why a middleware layer at all? The browser cannot talk to Tally directly
 * (CORS, raw XML, ODBC native module) — so Node does the translating:
 * friendly JSON in ⇄ Tally XML envelopes out, responses parsed back to JSON.
 *
 * Run:  npm start          (production)
 *       npm run dev        (auto-restart on changes)
 * ============================================================================
 */
const path = require('path');
const http = require('http');
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { Server } = require('socket.io');

const { errorHandler, apiNotFound } = require('./middleware/errorHandler');
const syncService = require('./services/syncService');
const tallyService = require('./services/tallyXMLService');
const odbcService = require('./services/odbcService');

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';

/* -------------------------------------------------------------------------- */
/*  Core middleware                                                            */
/* -------------------------------------------------------------------------- */
app.use(cors());                                   // LAN deployments / dev cross-origin
app.use(express.json({ limit: '2mb' }));           // voucher payloads with item tables
app.use(express.urlencoded({ extended: true }));
app.use(morgan(process.env.NODE_ENV === 'production' ? 'tiny' : 'dev'));

/* -------------------------------------------------------------------------- */
/*  REST API                                                                   */
/* -------------------------------------------------------------------------- */
const voucherRoutes = require('./routes/voucherRoutes');
const ledgerRoutes = require('./routes/ledgerRoutes');
const reportRoutes = require('./routes/reportRoutes');
const syncRoutes = require('./routes/syncRoutes');
const stockRoutes = require('./routes/stockRoutes');
const companyRoutes = require('./routes/companyRoutes');
const settingsRoutes = require('./routes/settingsRoutes');

app.get('/api/health', (req, res) => res.json({
  success: true,
  data: {
    status: 'ok', uptimeSec: Math.round(process.uptime()),
    tally: { status: syncService.state.status, source: syncService.state.source },
    odbc: odbcService.status(),
    queue: syncService.state.queue.length,
  },
}));

app.use('/api/vouchers', voucherRoutes);
app.use('/api/ledgers', ledgerRoutes.router);
app.use('/api/ledger-groups', ledgerRoutes.groupsRouter);
app.use('/api/reports', reportRoutes);
app.use('/api/sync', syncRoutes);
app.use('/api/stock-items', stockRoutes.router);
app.use('/api/stock-groups', stockRoutes.groupsRouter);
app.use('/api/company', companyRoutes);
app.use('/api/settings', settingsRoutes);

/** One round-trip powering the whole dashboard. */
app.get('/api/dashboard/summary', async (req, res, next) => {
  try {
    const out = await tallyService.getReport('dashboard', {
      from: req.query.from, to: req.query.to,
    });
    res.json({ success: true, data: out.data, source: out.source });
  } catch (err) { next(err); }
});

/* -------------------------------------------------------------------------- */
/*  Static frontend                                                            */
/* -------------------------------------------------------------------------- */
const FRONTEND_DIR = path.join(__dirname, '..', 'frontend');
app.use(express.static(FRONTEND_DIR, { index: 'index.html', maxAge: 0 }));
// Pretty URLs: /vouchers → voucher-entry.html etc.
const pretty = { '/dashboard': 'index.html', '/vouchers': 'voucher-entry.html', '/ledgers': 'ledger-master.html', '/reports': 'reports.html', '/settings': 'settings.html' };
for (const [route, file] of Object.entries(pretty)) {
  app.get(route, (req, res) => res.sendFile(path.join(FRONTEND_DIR, file)));
}
app.get(/^\/(?!api|socket\.io).*/, (req, res) => res.sendFile(path.join(FRONTEND_DIR, 'index.html')));

/* 404 + errors (after all routes) */
app.use('/api', apiNotFound);
app.use(errorHandler);

/* -------------------------------------------------------------------------- */
/*  HTTP + Socket.IO                                                           */
/* -------------------------------------------------------------------------- */
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
  path: '/socket.io',
});

io.on('connection', (socket) => {
  // Lightweight channel so any page can trigger/report sync events.
  socket.on('voucher:created', (payload) => {
    socket.broadcast.emit('tally:changed', { areas: ['vouchers'], by: 'web' });
    syncService.log('Push', 'Voucher', 'Success', `Web entry: ${payload?.label || 'voucher'}`);
  });
});

/* -------------------------------------------------------------------------- */
/*  Boot                                                                       */
/* -------------------------------------------------------------------------- */
syncService.init(io); // starts polling, queue replay, cron deep-sync

server.listen(PORT, HOST, () => {
  const cfg = require('./config/tallyConfig').getTallyConfig();
  console.log('──────────────────────────────────────────────────────────────');
  console.log('  Tally Web App — http://%s:%s', HOST, PORT);
  console.log('  Tally XML API  → %s   (mode: %s)', cfg.baseUrl, cfg.demoMode);
  console.log('  ODBC           → %s  (%s)', require('./config/odbcConfig').getOdbcConfig().dsn, odbcService.status().installed ? 'module installed' : 'module not installed — reads via XML');
  console.log('──────────────────────────────────────────────────────────────');
});

/* Graceful shutdown */
for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    console.log(`\n[server] ${sig} received — closing`);
    io.close();
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(0), 3000).unref();
  });
}

module.exports = app;
