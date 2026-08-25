# Tally Web App — Full-Stack Accounting Suite for Tally Prime 2.1

A premium, modern web interface over **Tally Prime** — deep-navy/teal glassmorphism UI,
Node.js (Express) middleware, and **bi-directional real-time sync** with Tally through
its **XML API (port 9000)** and **ODBC server (port 9001)**.

```
Browser (HTML/CSS/JS)  ⇄ REST + Socket.IO  ⇄  Express middleware  ⇄  Tally Prime
                                                ├─ XML API :9000  (read + write)
                                                └─ ODBC    :9001  (fast reads)
```

---

## ✨ Features

| Area | Highlights |
|---|---|
| **Dashboard** | Sales / Purchases (today · month · FY), Cash, Bank, Receivables, Payables, sales-vs-purchase bars, expense doughnut, 30-day cash-flow lines, last 20 transactions, live sync LED |
| **Voucher Entry** | All 8 Tally types — Sales, Purchase, Payment, Receipt, Contra, Journal, Credit Note, Debit Note — with searchable party picker, GSTIN auto-fill, state-based IGST/CGST+SGST auto-split, live item-grid math, drafts, `Ctrl+S`, Save & Print (A4 + 80 mm thermal), duplicate detection |
| **Ledger Master** | Create/Edit/Delete ledgers with groups, GST details, mailing details; searchable/sortable/filterable table; group-wise tree view; Excel export |
| **Reports** | Trial Balance, P&L, Balance Sheet, Day Book, Ledger statement, Outstanding, GSTR-1/GSTR-3B — all with date ranges, PDF / Excel / print |
| **Sync Engine** | 5-second fingerprint polling, Socket.IO push to every browser, offline queue (persisted), conflict resolution dialog, rolling sync journal |
| **Resilience** | Tally down? Reads fall back to a built-in demo dataset, writes queue to `backend/data/queue.json` and auto-flush on reconnect. App never blanks out. |

---

## 🚀 Quick Start

```bash
cd tally-web-app
npm install          # backend deps + vendored frontend libs
npm run vendor       # copy Chart.js/FontAwesome/etc → frontend/assets/vendor
npm start            # → http://localhost:3000
```

> With no Tally reachable, the app boots in **Demo Mode** (blue dot) with a full
> sample company ("Sunrise Traders Pvt Ltd", 42 ledgers, 450+ vouchers) so every
> screen is explorable. Point it at real Tally via **Settings → Tally Connection**.

### Environment variables (optional — `.env` in project root)

```ini
PORT=3000
TALLY_HOST=localhost     # or the LAN IP of the Tally machine
TALLY_PORT=9000
TALLY_COMPANY=           # exact name from Tally's Select Company (blank = open company)
DEMO_MODE=auto           # auto | always | never
ODBC_ENABLED=true
ODBC_DSN=Tally ODBC 64-bit
```

Everything above can also be changed at runtime from the in-app **Settings** page
(persisted to `backend/data/settings.json`, applied without restart).

---

## 🖥️ Tally Prime Setup (one-time)

1. **Enable the XML server**
   Tally Prime → `F1 (Help) → Settings → Connectivity` → *“TallyPrime acts as”* = **Both**
   (or *Server* on dedicated hosts).
2. **Ports** — `F12 → Advanced Configuration`:
   * *Allow XML Server on Port* = **Yes**, Port = **9000**
   * *Allow ODBC* = **Yes**, Port = **9001**
3. **ODBC DSN** (only if you want the fast read channel on the same Windows box):
   Windows → *ODBC Data Sources (64-bit)* → *System DSN* → add **“Tally ODBC 64-bit”**
   (the driver ships with Tally Prime).
4. **Native ODBC module** (Windows host only, optional):
   ```bash
   npm run setup:odbc    # installs the `odbc` npm package (native)
   ```
   Without it the app transparently uses the XML API for reads.
5. Keep Tally running with the target company **open**, then hit
   **Settings → Test Connection**.

> Firewall: allow inbound TCP **9000/9001** on the Tally machine for the LAN.

---

## 📁 Project Structure

```
tally-web-app/
├── frontend/
│   ├── index.html              Dashboard (landing)
│   ├── voucher-entry.html      All 8 voucher types
│   ├── ledger-master.html      Ledger CRUD + tree
│   ├── reports.html            7 financial reports + exports
│   ├── settings.html           Connection / sync / preferences
│   ├── css/                    style.css · dashboard.css · forms.css
│   ├── js/                     app.js · tallySync.js · voucherEntry.js
│   │                           ledgerMaster.js · reports.js · dashboard.js · settings.js
│   └── assets/vendor/          self-hosted Chart.js, FA6, SweetAlert2, Toastify,
│                               SheetJS, html2pdf, socket.io-client, Inter/Poppins
├── backend/
│   ├── server.js               Express + Socket.IO entry
│   ├── config/                 tallyConfig.js · odbcConfig.js
│   ├── routes/                 voucherRoutes · ledgerRoutes · reportRoutes
│   │                           syncRoutes · stockRoutes · companyRoutes · settingsRoutes
│   ├── services/               tallyXMLService (XML core) · odbcService (reads)
│   │                           syncService (real-time engine) · demoStore (fallback)
│   ├── middleware/             errorHandler.js · validator.js
│   └── utils/                  xmlBuilder.js (every Tally template) · helpers.js
│                               settingsStore.js
├── scripts/                    vendor-assets.js
└── package.json
```

---

## 🔌 Tally Integration — how it works

### XML API (primary, read + write)

* **Read** — `Export Data` envelopes: `List of Accounts` (ledgers/groups),
  `Voucher Register` / `Day Book`, `Trial Balance`, `Profit and Loss`,
  `Balance Sheet`, `Bills Receivable/Payable`, `Company Info`.
  See `backend/utils/xmlBuilder.js`.
* **Write** — `Import Data` envelopes with `<TALLYMESSAGE>` payloads for all 8
  voucher types, ledger create/alter/delete, stock-item create.
* **Sign convention** (handled in one place — `helpers.tallyAmount`):
  `Debit → ISDEEMEDPOSITIVE=Yes + negative AMOUNT`, `Credit → No + positive`.
* **GST engine** — `helpers.computeGst` splits intra-state (CGST+SGST) vs
  inter-state (IGST) from the party’s state, auto-detected from the GSTIN prefix.
* Every import response is scanned for `<LINEERROR>` and the exact Tally message
  is surfaced to the UI.

### ODBC (secondary, fast reads)

TDL-flavoured SQL for ledgers, vouchers, stock and trial balance
(`SELECT $Name, $Parent FROM Ledger` …) — see `backend/config/odbcConfig.js`.
Routes try ODBC first, fall back to XML, then to the demo dataset. The native
`odbc` module is **lazy-loaded**; absence is never fatal.

### Real-time sync (Part 4 of the spec)

1. Entries made in the browser → REST → XML Import → confirmation toast.
2. Entries keyed **inside Tally** → the 5-second fingerprint poll detects the
   change → Socket.IO `tally:changed` → every open dashboard refreshes itself.
3. Tally unreachable → writes land in the persisted **offline queue**
   (`backend/data/queue.json`) → auto-flushed on reconnect (toast confirms).
4. Same record edited on both sides → parked as a **conflict** → the browser
   shows a side-by-side dialog → user picks *keep mine* / *keep Tally’s*.
5. Status LED: 🟢 connected · 🟡 syncing · 🔵 demo · 🔴 disconnected.
   Sync journal (last 200 events) is on the dashboard, plus a manual sync button.

---

## 📮 REST API

```
LEDGERS
GET    /api/ledgers?q=&group=&channel=xml      list (ODBC first, XML fallback)
GET    /api/ledgers/:name                       one ledger
POST   /api/ledgers                             create in Tally
PUT    /api/ledgers/:name                       alter
DELETE /api/ledgers/:name                       delete
GET    /api/ledger-groups                       all groups

VOUCHERS
GET    /api/vouchers?from&to&type&party&limit
GET    /api/vouchers/next-number?voucherType=   auto numbering
GET    /api/vouchers/:id
POST   /api/vouchers/{sales|purchase|payment|receipt|contra|journal|credit-note|debit-note}
PUT    /api/vouchers/:id                        alter (conflict-checked on flush)
DELETE /api/vouchers/:id

STOCK
GET    /api/stock-items      POST /api/stock-items      GET /api/stock-groups

REPORTS
GET    /api/reports/trial-balance | profit-loss | balance-sheet | daybook
GET    /api/reports/ledger/:name | outstanding | gst-summary
GET    /api/dashboard/summary                    (dashboard in one round-trip)

SYNC
GET    /api/sync/status      POST /api/sync/manual      GET /api/sync/logs
GET    /api/sync/queue       POST /api/sync/queue/:id/discard
GET    /api/sync/conflicts   POST /api/sync/conflicts/:id/resolve

COMPANY / SETTINGS / MISC
GET    /api/company/info     GET /api/company/test
GET|PUT /api/settings        POST /api/settings/reset
GET    /api/health
```

Response envelope: `{ success, data, source: 'tally'|'odbc'|'demo', queued?, message? }`
Errors: `{ success:false, error:{ code, message, hint?, errors? } }` — `errors` is a
field→message map the forms highlight inline.

---

## ⌨️ Keyboard shortcuts

| Keys | Action |
|---|---|
| `Ctrl/⌘ + S` | Save the active voucher form |
| `Ctrl/⌘ + K` | Global search (ledgers + vouchers) |
| `Ctrl/⌘ + Alt + N` | New / clear the active form |
| `Enter` | In the item grid → adds the next row |
| `Esc` | Close pickers / dialogs |

---

## 🧪 Development notes

* `npm run dev` — auto-restart on file changes.
* `node --check <file>` passes on every JS file; `npm run check` runs a batch syntax check.
* Front-end libraries are **vendored** (`npm run vendor`) so the app runs on
  fully offline LANs — no CDN required.
* Amounts render in Indian format (₹1,00,000.00) and dates DD-MM-YYYY in the UI /
  YYYYMMDD on the wire to Tally, exactly per Tally conventions.
* `DEMO_MODE=never` gives you a strict, Tally-only deployment: every read/write
  error surfaces (writes still queue while offline).

## ⚠️ Honest caveats for live-Tally use

Tally’s XML export layouts vary slightly between builds/versions. Masters and
voucher register parsing uses deep-search extractors that tolerate layout
differences; the three financial statements (TB/P&L/BS) additionally fall back
to ODBC, which is deterministic. If a specific build returns an unfamiliar
layout, the error toast will say so — adjust the tag lists in
`tallyXMLService.statementRows()` once and everything downstream follows.
