/**
 * ============================================================================
 * VENDOR ASSETS — copies frontend libraries from node_modules into
 * frontend/assets/vendor so the app is fully self-hosted (works on a LAN
 * with no internet — typical for Tally deployments).
 *
 * Run once after `npm install`:   npm run vendor
 * ============================================================================
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const VENDOR = path.join(ROOT, 'frontend', 'assets', 'vendor');

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  return 1;
}
function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  let n = 0;
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    if (e.isDirectory()) n += copyDir(path.join(src, e.name), path.join(dest, e.name));
    else { fs.copyFileSync(path.join(src, e.name), path.join(dest, e.name)); n++; }
  }
  return n;
}

const NM = path.join(ROOT, 'node_modules');
let count = 0;

/* --- Libraries (single-file builds) -------------------------------------- */
count += copyFile(path.join(NM, 'chart.js/dist/chart.umd.js'), path.join(VENDOR, 'chartjs/chart.umd.js'));
count += copyFile(path.join(NM, 'socket.io-client/dist/socket.io.min.js'), path.join(VENDOR, 'socket.io/socket.io.min.js'));
count += copyFile(path.join(NM, 'sweetalert2/dist/sweetalert2.all.min.js'), path.join(VENDOR, 'sweetalert2/sweetalert2.all.min.js'));
count += copyFile(path.join(NM, 'toastify-js/src/toastify.js'), path.join(VENDOR, 'toastify/toastify.js'));
count += copyFile(path.join(NM, 'toastify-js/src/toastify.css'), path.join(VENDOR, 'toastify/toastify.css'));
count += copyFile(path.join(NM, 'xlsx/dist/xlsx.full.min.js'), path.join(VENDOR, 'xlsx/xlsx.full.min.js'));
count += copyFile(path.join(NM, 'html2pdf.js/dist/html2pdf.bundle.min.js'), path.join(VENDOR, 'html2pdf/html2pdf.bundle.min.js'));

/* --- Font Awesome (css + woff2 webfonts only) ----------------------------- */
count += copyFile(path.join(NM, '@fortawesome/fontawesome-free/css/all.min.css'), path.join(VENDOR, 'fontawesome/css/all.min.css'));
const wfSrc = path.join(NM, '@fortawesome/fontawesome-free/webfonts');
const wfDst = path.join(VENDOR, 'fontawesome/webfonts');
fs.mkdirSync(wfDst, { recursive: true });
for (const f of fs.readdirSync(wfSrc)) if (f.endsWith('.woff2')) { copyFile(path.join(wfSrc, f), path.join(wfDst, f)); count++; }

/* --- Inter & Poppins — latin subset, weights 400/500/600/700/800 ---------- */
for (const [pkg, family] of [['@fontsource/inter', 'Inter'], ['@fontsource/poppins', 'Poppins']]) {
  const dest = path.join(VENDOR, 'fonts', family.toLowerCase());
  fs.mkdirSync(dest, { recursive: true });
  const css = [`/* ${family} — latin subsets, self-hosted (@fontsource) */`];
  for (const w of ['400', '500', '600', '700', '800']) {
    const src = path.join(NM, pkg, 'files', `${family.toLowerCase()}-latin-${w}-normal.woff2`);
    if (!fs.existsSync(src)) { console.warn(`  ! missing font ${family} ${w}`); continue; }
    copyFile(src, path.join(dest, `${w}-latin.woff2`)); count++;
    css.push(`@font-face {
  font-family: '${family}';
  font-style: normal;
  font-display: swap;
  font-weight: ${w};
  src: url('./${w}-latin.woff2') format('woff2');
}`);
  }
  fs.writeFileSync(path.join(dest, `${family.toLowerCase()}.css`), css.join('\n') + '\n');
}

console.log(`\u2714 vendored ${count} files \u2192 frontend/assets/vendor`);
