/**
 * Post-build script: generate CommonJS wrapper files so the package
 * can be consumed with `require()` as well as `import`.
 *
 * We rely on TypeScript's NodeNext module output (pure ESM .js files) and
 * then write thin .cjs wrappers that use dynamic import().
 */

import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const distDir = join(root, 'dist');

if (!existsSync(distDir)) {
  console.error('dist/ not found. Run `tsc` first.');
  process.exit(1);
}

// Write dist/index.cjs  →  wraps dist/index.js for CJS consumers
writeFileSync(
  join(distDir, 'index.cjs'),
  `'use strict';
module.exports = require('./index.js');
`,
);

// Write dist/package.json so Node correctly treats dist/ files as ESM
const distPkg = join(distDir, 'package.json');
writeFileSync(distPkg, JSON.stringify({ type: 'module' }, null, 2) + '\n');

console.log('[build-cjs] Wrote dist/index.cjs and dist/package.json');
