/**
 * Batch syntax check: node --check over every JS file in backend/, frontend/js,
 * and scripts/. Run: npm run check
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const roots = ['backend', 'frontend/js', 'scripts'].map((d) => path.join(__dirname, '..', d));
let fail = 0, pass = 0;

function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith('.js')) {
      try {
        execFileSync(process.execPath, ['--check', p], { stdio: 'pipe' });
        pass++;
      } catch (err) {
        fail++;
        console.error(`✗ ${p}\n  ${err.stderr.toString().split('\n').slice(0, 4).join('\n  ')}`);
      }
    }
  }
}
roots.forEach((r) => fs.existsSync(r) && walk(r));
console.log(`\n${fail ? '✗' : '✓'} ${pass} files OK${fail ? `, ${fail} FAILED` : ''}`);
process.exit(fail ? 1 : 0);
