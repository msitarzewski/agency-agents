/**
 * ============================================================================
 * ODBC CONNECTION CONFIGURATION (secondary read channel)
 * ============================================================================
 * Tally Prime ships an ODBC server (default port 9001). Combined with the
 * "Tally ODBC 64-bit" DSN configured in Windows' ODBC Data Source Administrator
 * (odbcad32.exe), it lets us run TDL-flavoured SQL directly, e.g.:
 *
 *      SELECT $Name, $Parent, $OpeningBalance FROM Ledger
 *      SELECT $VoucherNumber, $Date, $VoucherTypeName, $Amount FROM Voucher
 *      SELECT $Name, $BaseUnits, $ClosingBalance, $ClosingRate FROM StockItem
 *
 * IMPORTANT — the npm `odbc` package is a NATIVE add-on:
 *   • It can only be installed on the machine that has the Tally DSN
 *     (i.e. a Windows box on Tally's LAN, not a Linux cloud server).
 *   • Install it with:  npm run setup:odbc
 *   • The backend lazy-loads it; when absent, every ODBC call throws a clean
 *     OdbcUnavailableError and callers fall back to the Tally XML API.
 * ============================================================================
 */
const settingsStore = require('../utils/settingsStore');

const DEFAULTS = {
  enabled: process.env.ODBC_ENABLED !== 'false', // set ODBC_ENABLED=false to skip
  dsn: process.env.ODBC_DSN || 'Tally ODBC 64-bit', // Windows DSN name
  // Fall back to the 32-bit DSN on older installs: 'Tally ODBC 32-bit'
  user: process.env.ODBC_USER || '',
  password: process.env.ODBC_PASSWORD || '',
  connectionTimeoutMs: 8000,
  queryTimeoutMs: 20000,
};

function getOdbcConfig() {
  const s = settingsStore.get();
  return {
    enabled: s.odbcEnabled !== undefined ? !!s.odbcEnabled : DEFAULTS.enabled,
    dsn: s.odbcDsn || DEFAULTS.dsn,
    user: DEFAULTS.user,
    password: DEFAULTS.password,
    connectionTimeoutMs: DEFAULTS.connectionTimeoutMs,
    queryTimeoutMs: DEFAULTS.queryTimeoutMs,
    /** node-odbc style connection string. The DSN carries the port (9001). */
    get connectionString() {
      let cs = `DSN=${this.dsn}`;
      if (this.user) cs += `;UID=${this.user}`;
      if (this.password) cs += `;PWD=${this.password}`;
      return cs;
    },
  };
}

/** Canonical TDL-SQL queries used by services/odbcService.js */
const QUERIES = {
  ledgers: `SELECT $Name AS name, $Parent AS parent, $OpeningBalance AS openingBalance FROM Ledger`,
  groups: `SELECT $Name AS name, $Parent AS parent, $Nature AS nature FROM Group`,
  vouchers: (fromYmd, toYmd) =>
    `SELECT $VoucherNumber AS number, $Date AS date, $VoucherTypeName AS type, $Amount AS amount, $PartyLedgerName AS party FROM Voucher` +
    (fromYmd ? ` WHERE $Date >= '${fromYmd}'${toYmd ? ` AND $Date <= '${toYmd}'` : ''}` : ''),
  stockItems: `SELECT $Name AS name, $Parent AS parent, $BaseUnits AS unit, $ClosingBalance AS closingBalance, $ClosingRate AS closingRate FROM StockItem`,
  trialBalance: `SELECT $Name AS name, $ClosingBalance AS balance FROM Ledger WHERE $ClosingBalance != 0`,
};

module.exports = { getOdbcConfig, QUERIES };
