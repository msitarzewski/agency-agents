/**
 * ============================================================================
 * SYNC SERVICE — real-time bi-directional sync engine
 * ============================================================================
 * FLOW (HTML ⇄ Node ⇄ Tally):
 *
 *   PUSH  Browser form → REST API → tallyXMLService.createVoucher()
 *         → posts Import-Data XML to Tally (:9000)
 *         → if Tally unreachable: op enters the OFFLINE QUEUE (persisted to
 *           backend/data/queue.json) and is replayed on reconnect.
 *
 *   PULL  node-cron + interval timer poll Tally every N seconds with a cheap
 *         "fingerprint" (ledger/voucher counts + latest voucher stamp).
 *         When the fingerprint changes, Socket.IO broadcasts `tally:changed`
 *         and every open dashboard refreshes itself.
 *
 * STATUS LED  🟢 connected  🟡 syncing  🔵 demo  🔴 disconnected
 *
 * CONFLICTS  If a queued ALTER targets a voucher Tally has changed meanwhile,
 *           the op is parked as a CONFLICT and `sync:conflict` is emitted;
 *           the browser shows a side-by-side dialog and the user picks
 *           "keep mine" / "keep theirs" via /api/sync/conflicts/:id/resolve.
 * ============================================================================
 */
const fs = require('fs');
const path = require('path');
const cron = require('node-cron');
const tally = require('./tallyXMLService');
const { getTallyConfig } = require('../config/tallyConfig');
const settingsStore = require('../utils/settingsStore');
const { todayTally } = require('../utils/helpers');

const DATA_DIR = path.join(__dirname, '..', 'data');
const QUEUE_FILE = path.join(DATA_DIR, 'queue.json');

/* -------------------------------------------------------------------------- */
/*  State                                                                      */
/* -------------------------------------------------------------------------- */
const s = {
  io: null,
  status: 'syncing',        // connected | syncing | demo | disconnected
  source: 'demo',           // tally | demo — what the API layer is serving
  lastSyncAt: null,
  lastError: null,
  queue: [],                // offline ops awaiting replay
  conflicts: [],            // parked conflicts awaiting user decision
  logs: [],                 // rolling sync journal (max 200)
  fingerprint: null,
  timer: null,
  pollBusy: false,
};

/* -------------------------------------------------------------------------- */
/*  Logging + broadcasting                                                     */
/* -------------------------------------------------------------------------- */
function log(action, dataType, status, details) {
  const entry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    timestamp: new Date().toISOString(),
    action,        // Push | Pull | System | Conflict
    dataType,      // Voucher | Ledger | StockItem | Masters | Fingerprint
    status,        // Success | Error | Queued | Info
    details: details || '',
  };
  s.logs.unshift(entry);
  if (s.logs.length > 200) s.logs.length = 200;
  if (s.io) s.io.emit('sync:log', entry);
  console.log(`[sync] ${entry.action}/${entry.dataType} ${entry.status}: ${entry.details}`);
  return entry;
}

function broadcastStatus(extra = {}) {
  const payload = {
    status: s.status,
    source: s.source,
    lastSyncAt: s.lastSyncAt,
    queueCount: s.queue.length,
    conflictCount: s.conflicts.length,
    error: s.lastError,
    ...extra,
  };
  if (s.io) s.io.emit('sync:status', payload);
}

/* -------------------------------------------------------------------------- */
/*  Offline queue (persisted)                                                  */
/* -------------------------------------------------------------------------- */
function loadQueue() {
  try {
    if (fs.existsSync(QUEUE_FILE)) s.queue = JSON.parse(fs.readFileSync(QUEUE_FILE, 'utf8'));
  } catch (err) {
    console.error('[sync] queue load failed:', err.message);
    s.queue = [];
  }
}

function persistQueue() {
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.writeFileSync(QUEUE_FILE, JSON.stringify(s.queue, null, 2));
  } catch (err) {
    console.error('[sync] queue persist failed:', err.message);
  }
}

/**
 * Enqueue an operation that could not reach Tally.
 * op = { kind:'voucher'|'ledger'|'stock', op:'create'|'update'|'delete',
 *        payload, baseline?, label }
 */
function enqueue(op) {
  const item = { ...op, id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, queuedAt: new Date().toISOString(), attempts: 0 };
  s.queue.push(item);
  persistQueue();
  log('Push', cap(op.kind), 'Queued', `${op.label} queued for Tally (offline)`);
  if (s.io) s.io.emit('sync:queue', { count: s.queue.length });
  broadcastStatus();
  return item;
}

const cap = (x) => (x ? x[0].toUpperCase() + x.slice(1) : 'Unknown');

/** Replay one queued op against live Tally (force-real, no demo fallback). */
async function replayOp(op) {
  const forced = { ...op.payload, _forceReal: true };
  switch (`${op.kind}:${op.op}`) {
    case 'voucher:create': return tally.createVoucher(forced);
    case 'voucher:update': return tally.updateVoucher(op.targetId, forced);
    case 'voucher:delete': return tally.deleteVoucher(op.targetId, { forceReal: true });
    case 'ledger:create': return tally.createLedger(forced);
    case 'ledger:update': return tally.updateLedger(op.targetId, forced);
    case 'ledger:delete': return tally.deleteLedger(op.targetId, { forceReal: true });
    default: throw new Error(`Unknown queued op ${op.kind}:${op.op}`);
  }
}

/** Try to flush the whole queue; park unresolvable edits as conflicts. */
async function flushQueue() {
  if (!s.queue.length) return 0;
  let flushed = 0;
  const remaining = [];
  for (const op of s.queue) {
    try {
      // Conflict check for updates: compare Tally's current state to the
      // baseline captured when the edit was queued.
      if (op.op === 'update' && op.baseline) {
        try {
          const cur = await tally.getVoucherById(op.targetId);
          if (cur && op.baseline.amount != null && Math.abs(cur.amount - op.baseline.amount) > 0.01) {
            op.conflict = { local: op.payload, tally: cur, reason: 'Voucher changed in Tally after this edit was made' };
            s.conflicts.push(op);
            log('Conflict', 'Voucher', 'Info', `${op.label} conflicts with Tally version — awaiting user decision`);
            if (s.io) s.io.emit('sync:conflict', op);
            continue; // stays parked; not re-queued
          }
        } catch { /* target vanished or unreadable → attempt plain replay */ }
      }
      await replayOp(op);
      flushed++;
      log('Push', cap(op.kind), 'Success', `${op.label} flushed to Tally`);
    } catch (err) {
      op.attempts = (op.attempts || 0) + 1;
      if (err.tallyUnreachable || op.attempts < 3) remaining.push(op);
      else log('Push', cap(op.kind), 'Error', `${op.label} failed after ${op.attempts} attempts: ${err.message}`);
    }
  }
  s.queue = remaining;
  persistQueue();
  if (flushed) {
    if (s.io) s.io.emit('sync:queue', { count: s.queue.length, flushed });
    log('Pull', 'Queue', 'Success', `${flushed} queued operations pushed to Tally`);
  }
  return flushed;
}

/** Resolve a parked conflict. resolution: 'mine' (push local) | 'theirs' (drop). */
async function resolveConflict(conflictId, resolution) {
  const idx = s.conflicts.findIndex((c) => c.id === conflictId);
  if (idx < 0) throw Object.assign(new Error('Conflict not found'), { statusCode: 404 });
  const [op] = s.conflicts.splice(idx, 1);
  if (resolution === 'mine') {
    try {
      await replayOp(op);
      log('Conflict', cap(op.kind), 'Success', `${op.label}: local version pushed to Tally`);
    } catch (err) {
      log('Conflict', cap(op.kind), 'Error', `${op.label}: ${err.message}`);
      throw err;
    }
  } else {
    log('Conflict', cap(op.kind), 'Info', `${op.label}: Tally version kept, local edit discarded`);
  }
  broadcastStatus();
  return { resolved: true, resolution };
}

/* -------------------------------------------------------------------------- */
/*  Polling loop                                                               */
/* -------------------------------------------------------------------------- */

/**
 * A cheap fingerprint of Tally's current data. Any change in these numbers
 * means somebody entered data in Tally → we tell the browsers.
 */
async function computeFingerprint() {
  const [ledgers, vouchersToday] = await Promise.all([
    tally.getLedgers(),
    tally.getVouchers({ from: todayTally(), limit: 50 }),
  ]);
  const list = vouchersToday.data || [];
  return {
    ledgers: (ledgers.data || []).length,
    vouchersToday: list.length,
    latest: list[0] ? `${list[0].voucherType}#${list[0].voucherNumber}@${list[0].date}` : '',
    source: ledgers.source,
  };
}

async function pollTick() {
  if (s.pollBusy) return;
  s.pollBusy = true;
  const cfg = getTallyConfig();
  try {
    if (cfg.demoMode === 'always') {
      s.status = 'demo';
      s.source = 'demo';
      s.lastError = null;
      s.lastSyncAt = new Date().toISOString();
      broadcastStatus();
      return;
    }
    const prev = s.status;
    s.status = 'syncing';
    broadcastStatus();
    await tally.testConnection();
    s.lastError = null;

    // Connected → replay anything queued, then fingerprint Tally.
    await flushQueue();
    const fp = await computeFingerprint();
    s.source = fp.source || 'tally';
    s.lastSyncAt = new Date().toISOString();
    const changed = s.fingerprint && JSON.stringify(s.fingerprint) !== JSON.stringify(fp);
    s.fingerprint = fp;
    s.status = 'connected';
    if (changed) {
      log('Pull', 'Fingerprint', 'Success', 'Tally data changed — notifying clients');
      if (s.io) s.io.emit('tally:changed', { areas: ['vouchers', 'ledgers'], fingerprint: fp });
    } else if (prev !== 'connected') {
      log('Pull', 'Fingerprint', 'Success', `Connected to Tally (${fp.ledgers} ledgers)`);
    }
    broadcastStatus();
  } catch (err) {
    s.status = 'disconnected';
    s.lastError = err.message || String(err);
    if (tally.state.demoActive) {
      // Auto-fallback engaged: API keeps serving demo data while writes queue.
      s.status = 'demo';
      s.source = 'demo';
    }
    broadcastStatus();
    // Rate-limit repeated identical errors so a 5-second poller doesn't spam
    // the journal: log the first failure, then at most once per 5 minutes.
    const now = Date.now();
    const msg = `Tally unreachable: ${s.lastError}`;
    if (s._lastErrLogged !== msg || now - (s._lastErrLoggedAt || 0) > 5 * 60 * 1000) {
      s._lastErrLogged = msg;
      s._lastErrLoggedAt = now;
      log('Pull', 'Fingerprint', 'Error', msg);
    }
  } finally {
    s.pollBusy = false;
  }
}

function restartTimer() {
  if (s.timer) clearInterval(s.timer);
  const sec = Math.max(2, Number(settingsStore.get().syncIntervalSec) || 5);
  s.timer = setInterval(() => pollTick().catch(() => {}), sec * 1000);
}

/** Full manual sync (button on dashboard). */
async function manualSync() {
  log('System', 'Fingerprint', 'Info', 'Manual sync triggered');
  await pollTick();
  return getStatus();
}

function getStatus() {
  return {
    status: s.status,
    source: s.source,
    lastSyncAt: s.lastSyncAt,
    queueCount: s.queue.length,
    queue: s.queue.map((q) => ({ id: q.id, label: q.label, kind: q.kind, op: q.op, queuedAt: q.queuedAt, attempts: q.attempts })),
    conflictCount: s.conflicts.length,
    conflicts: s.conflicts.map((c) => ({ id: c.id, label: c.label, kind: c.kind, queuedAt: c.queuedAt, conflict: c.conflict })),
    error: s.lastError,
    demoActive: tally.state.demoActive,
    intervalSec: settingsStore.get().syncIntervalSec,
  };
}

function getLogs(limit = 100) {
  return s.logs.slice(0, Number(limit));
}

/* -------------------------------------------------------------------------- */
/*  Bootstrap                                                                  */
/* -------------------------------------------------------------------------- */
function init(io) {
  s.io = io;
  loadQueue();
  restartTimer();
  // Scheduled deep-sync every 5 minutes keeps long-lived dashboards honest
  // even if the 5-second fingerprint somehow misses a change.
  cron.schedule('*/5 * * * *', () => pollTick().catch(() => {}));
  io.on('connection', (socket) => {
    socket.emit('sync:status', getStatus()); // seed the new client immediately
    socket.on('sync:manual', () => manualSync().catch(() => {}));
  });
  log('System', 'Fingerprint', 'Info', 'Sync engine started');
  pollTick().catch(() => {});
}

/** Called by the settings route when the interval changes. */
function onSettingsChanged() {
  restartTimer();
  pollTick().catch(() => {});
}

module.exports = { init, log, broadcastStatus, enqueue, flushQueue, resolveConflict, manualSync, getStatus, getLogs, onSettingsChanged, state: s };
