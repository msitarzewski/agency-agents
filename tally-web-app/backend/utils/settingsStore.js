/**
 * ============================================================================
 * SETTINGS STORE
 * ============================================================================
 * Tiny JSON-file-backed store for user-configurable settings (Settings page).
 * Settings persist across restarts in backend/data/settings.json and override
 * the .env defaults at runtime (see config/tallyConfig.js / odbcConfig.js).
 * ============================================================================
 */
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const FILE = path.join(DATA_DIR, 'settings.json');

const DEFAULTS = {
  tallyHost: 'localhost',
  tallyPort: 9000,
  companyName: '',
  demoMode: 'auto', // auto | always | never
  odbcEnabled: true,
  odbcDsn: 'Tally ODBC 64-bit',
  syncIntervalSec: 5,
  theme: 'light',
  defaultPrint: 'A4', // A4 | Thermal80
  invoicePrefix: '', // e.g. "INV/" — prepended to auto numbers
  defaultVoucherView: 'Sales',
  autoRoundOff: true,
};

let cache = null;

function load() {
  if (cache) return cache;
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    if (fs.existsSync(FILE)) {
      cache = { ...DEFAULTS, ...JSON.parse(fs.readFileSync(FILE, 'utf8')) };
    } else {
      cache = { ...DEFAULTS };
      persist();
    }
  } catch (err) {
    console.error('[settings] failed to read settings.json, using defaults:', err.message);
    cache = { ...DEFAULTS };
  }
  return cache;
}

function persist() {
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    const tmp = FILE + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(cache, null, 2));
    fs.renameSync(tmp, FILE); // atomic-ish write
  } catch (err) {
    console.error('[settings] failed to persist settings:', err.message);
  }
}

function get() {
  return { ...load() };
}

/** Merge-patch settings and persist. Returns the new settings object. */
function save(patch = {}) {
  const allowed = Object.keys(DEFAULTS);
  const clean = {};
  for (const k of allowed) {
    if (patch[k] !== undefined) clean[k] = patch[k];
  }
  cache = { ...load(), ...clean };
  persist();
  return { ...cache };
}

function reset() {
  cache = { ...DEFAULTS };
  persist();
  return { ...cache };
}

module.exports = { get, save, reset, DEFAULTS };
