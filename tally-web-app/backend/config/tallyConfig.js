/**
 * ============================================================================
 * TALLY CONNECTION CONFIGURATION
 * ============================================================================
 * Tally Prime 2.1 exposes two network interfaces:
 *
 *   1. XML API  (primary)  – HTTP server, default port 9000.
 *      Used for BOTH pushing (Import Data) and pulling (Export Data).
 *      Enable in Tally: F1(Help) > Settings > Connectivity >
 *      "TallyPrime acts as" = Both, and set the port under
 *      Advanced Configuration (F12 > Advanced Configuration in older builds).
 *
 *   2. ODBC Server (secondary) – default port 9001.
 *      Used for fast direct reads through the "Tally ODBC 64-bit" DSN.
 *      Enable in Tally: F12 > Advanced Configuration > "Allow ODBC" = Yes.
 *
 * Every setting can be overridden (in priority order) by:
 *   1. The in-app Settings page  (persisted to backend/data/settings.json)
 *   2. Environment variables      (.env file → process.env)
 *   3. The defaults below.
 * ============================================================================
 */
const path = require('path');
const dotenv = require('dotenv');

// Load .env from the project root (tally-web-app/.env) if present.
dotenv.config({ path: path.join(__dirname, '..', '..', '.env') });

const settingsStore = require('../utils/settingsStore');

const ENV = process.env;

/** Static defaults — also used to seed backend/data/settings.json */
const DEFAULTS = {
  // Host/IP of the machine running Tally Prime.
  // Use "localhost" when Node runs on the same machine as Tally.
  tallyHost: ENV.TALLY_HOST || 'localhost',

  // XML API port configured inside Tally (default 9000).
  tallyPort: parseInt(ENV.TALLY_PORT || '9000', 10),

  // Company name EXACTLY as it appears on Tally's "Select Company" screen.
  // Leave blank to operate on the currently-open company in Tally
  // (Tally XML requests with an empty SVCURRENTCOMPANY act on the active one).
  companyName: ENV.TALLY_COMPANY || '',

  // HTTP timeout (ms) for XML API calls. Tally can be slow on huge reports,
  // so keep this generous but bounded.
  requestTimeoutMs: parseInt(ENV.TALLY_TIMEOUT || '15000', 10),

  // demoMode:
  //   'auto'   → try Tally first; if unreachable fall back to a built-in
  //              demo dataset so the UI keeps working (queue writes)  [default]
  //   'always' → never touch Tally, always serve demo data (offline dev)
  //   'never'  → hard Tally mode; errors surface instead of demo fallback
  demoMode: ENV.DEMO_MODE || 'auto',
};

/**
 * Effective Tally config = defaults merged with persisted settings overrides.
 * Re-read on every call so changes made from the Settings page apply
 * immediately without a server restart.
 */
function getTallyConfig() {
  const s = settingsStore.get();
  return {
    host: s.tallyHost || DEFAULTS.tallyHost,
    port: Number(s.tallyPort || DEFAULTS.tallyPort),
    companyName: s.companyName || DEFAULTS.companyName,
    timeoutMs: DEFAULTS.requestTimeoutMs,
    demoMode: s.demoMode || DEFAULTS.demoMode,
    get baseUrl() {
      return `http://${this.host}:${this.port}`;
    },
  };
}

/** Quick URL used by the health/connection ping. */
function getTallyUrl() {
  const c = getTallyConfig();
  return c.baseUrl;
}

module.exports = { getTallyConfig, getTallyUrl, DEFAULTS };
