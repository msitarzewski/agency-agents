/**
 * ============================================================================
 * ODBC SERVICE — fast direct reads from Tally Prime
 * ============================================================================
 * Why ODBC *and* XML?  Tally's ODBC server answers simple reads much faster
 * than round-tripping report XML, which matters for dashboards/reports.
 * ODBC is READ-ONLY for our purposes — every write goes through the XML API.
 *
 * Setup (on the machine that runs this Node server — typically the same
 * Windows box as Tally, or another box on its LAN):
 *   1. Tally → F12 → Advanced Configuration → "Allow ODBC" = Yes, Port 9001
 *   2. Windows → ODBC Data Sources (64-bit) → System DSN → "Tally ODBC 64-bit"
 *   3. In this project:  npm run setup:odbc   (installs the native module)
 *
 * The `odbc` package is loaded lazily — if it is missing (Linux/cloud deploy)
 * every call rejects with OdbcUnavailableError and callers fall back to the
 * XML API transparently.
 * ============================================================================
 */
const { getOdbcConfig, QUERIES } = require('../config/odbcConfig');
const { round2 } = require('../utils/helpers');

class OdbcUnavailableError extends Error {
  constructor(msg) {
    super(msg);
    this.name = 'OdbcUnavailableError';
    this.statusCode = 503;
  }
}

let odbcModule = null;
let loadAttempted = false;

/** Lazy-require('odbc') with a friendly failure. */
function loadModule() {
  if (loadAttempted) return odbcModule;
  loadAttempted = true;
  try {
    // eslint-disable-next-line global-require
    odbcModule = require('odbc');
  } catch {
    odbcModule = null;
  }
  return odbcModule;
}

let connection = null;          // reused connection
let lastHealthyAt = null;

async function getConnection() {
  const cfg = getOdbcConfig();
  if (!cfg.enabled) throw new OdbcUnavailableError('ODBC disabled in settings');
  const mod = loadModule();
  if (!mod) {
    throw new OdbcUnavailableError(
      "npm package 'odbc' is not installed on this machine. Run `npm run setup:odbc` on the Windows host that has the Tally DSN."
    );
  }
  if (connection) return connection;
  try {
    connection = await mod.connect(cfg.connectionString);
    connection.queryTimeout = cfg.queryTimeoutMs;
    lastHealthyAt = new Date();
    return connection;
  } catch (err) {
    connection = null;
    throw new OdbcUnavailableError(`ODBC connect failed (${cfg.connectionString}): ${err.message}`);
  }
}

/** Run a TDL-SQL query → array of plain row objects. */
async function query(sql) {
  const conn = await getConnection();
  try {
    const result = await conn.query(sql);
    lastHealthyAt = new Date();
    // node-odbc returns { columns, rows } — normalise to POJOs.
    const cols = (result.columns || []).map((c) => c.name);
    return (result.rows || result).map((r) => {
      const o = {};
      if (Array.isArray(r)) cols.forEach((c, i) => (o[c] = r[i]));
      else for (const c of cols) o[c] = r[c];
      return o;
    });
  } catch (err) {
    connection = null; // force reconnect next time
    throw new OdbcUnavailableError(`ODBC query failed: ${err.message}`);
  }
}

/* -------------------------------------------------------------------------- */
/*  Canonical read helpers (shapes match the XML channel so routes can        */
/*  try ODBC first and fall back to XML without any mapping code)             */
/* -------------------------------------------------------------------------- */

const ledgers = async () =>
  (await query(QUERIES.ledgers)).map((r) => ({
    name: r.name, parent: r.parent || '',
    openingBalance: { amount: Math.abs(Number(r.openingBalance) || 0), drCr: Number(r.openingBalance) >= 0 ? 'Dr' : 'Cr' },
    gstin: '', state: '', regType: '', address: '', city: '', pincode: '', phone: '', email: '',
  }));

const groups = async () =>
  (await query(QUERIES.groups)).map((r) => ({ name: r.name, parent: r.parent || '', nature: r.nature || '' }));

const vouchers = async (fromYmd, toYmd) => {
  const rows = await query(QUERIES.vouchers(fromYmd, toYmd));
  return rows.map((r) => ({
    voucherNumber: r.number, date: String(r.date || '').replace(/-/g, ''),
    voucherType: r.type, party: r.party || '',
    amount: round2(Math.abs(Number(r.amount) || 0)),
  }));
};

const stockItems = async () =>
  (await query(QUERIES.stockItems)).map((r) => ({
    name: r.name, group: r.parent || '', unit: r.unit || 'Nos',
    rate: round2(Number(r.closingRate) || 0),
    closingBalance: Number(r.closingBalance) || 0,
    closingValue: round2((Number(r.closingBalance) || 0) * (Number(r.closingRate) || 0)),
  }));

const trialBalance = async () => {
  const rows = await query(QUERIES.trialBalance);
  return rows
    .map((r) => ({ name: r.name, debit: Number(r.balance) > 0 ? round2(Number(r.balance)) : 0, credit: Number(r.balance) < 0 ? round2(-Number(r.balance)) : 0, group: '' }))
    .filter((r) => r.debit || r.credit);
};

function status() {
  return {
    installed: !!loadModule(),
    enabled: getOdbcConfig().enabled,
    dsn: getOdbcConfig().dsn,
    connected: !!connection,
    lastHealthyAt,
  };
}

module.exports = {
  OdbcUnavailableError,
  query,
  ledgers, groups, vouchers, stockItems, trialBalance,
  status,
};
