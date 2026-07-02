#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const args = process.argv.slice(2);
const getArg = (name, fallback) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

const manifestPath = getArg("--manifest", "agent-identities/glyph-v3.json");
const outDir = getArg("--out", ".cache/agent-glyphs");
const skipContactSheet = args.includes("--no-contact-sheet");

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
fs.mkdirSync(outDir, { recursive: true });

function fnv1a(input) {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

function slugFromSource(sourceFile) {
  return path.basename(sourceFile, ".md");
}

function hexToRgb(hex) {
  const clean = hex.replace("#", "");
  return [
    parseInt(clean.slice(0, 2), 16),
    parseInt(clean.slice(2, 4), 16),
    parseInt(clean.slice(4, 6), 16),
  ];
}

function mix(rgb, target, amount) {
  return rgb.map((value, index) => Math.round(value + (target[index] - value) * amount));
}

function rgba(rgb, alpha = 255) {
  return [rgb[0], rgb[1], rgb[2], alpha];
}

const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buffer) {
  let c = 0xffffffff;
  for (let i = 0; i < buffer.length; i += 1) {
    c = crcTable[(c ^ buffer[i]) & 0xff] ^ (c >>> 8);
  }
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data = Buffer.alloc(0)) {
  const typeBuffer = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length, 0);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])), 0);
  return Buffer.concat([length, typeBuffer, data, crc]);
}

function encodePng(width, height, rgbaBuffer) {
  const raw = Buffer.alloc((width * 4 + 1) * height);
  for (let y = 0; y < height; y += 1) {
    const row = y * (width * 4 + 1);
    raw[row] = 0;
    rgbaBuffer.copy(raw, row + 1, y * width * 4, (y + 1) * width * 4);
  }

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;

  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw, { level: 9 })),
    chunk("IEND"),
  ]);
}

function renderGlyph(agent) {
  const grid = 16;
  const pixels = Buffer.alloc(grid * grid * 4);
  const base = hexToRgb(agent.divisionColor);
  const primary = rgba(base);
  const light = rgba(mix(base, [255, 255, 255], 0.36));
  const shade = rgba(mix(base, [0, 0, 0], 0.34));
  const dim = rgba(mix(base, [38, 38, 42], 0.52));
  const ink = rgba([18, 19, 23]);
  const accentPool = [
    [255, 236, 120],
    [125, 249, 255],
    [255, 117, 117],
    [190, 242, 100],
    [255, 142, 199],
    [253, 186, 116],
    [196, 181, 253],
    [94, 234, 212],
  ];
  const hash = fnv1a(`${agent.sourceFile}:${agent.agentType}:${agent.agentName}:glyph-v3`);
  const accent = rgba(accentPool[hash % accentPool.length]);
  const role = agent.roleGlyph || "operator";

  const set = (x, y, color) => {
    if (x < 0 || y < 0 || x >= grid || y >= grid) return;
    const offset = (y * grid + x) * 4;
    pixels[offset] = color[0];
    pixels[offset + 1] = color[1];
    pixels[offset + 2] = color[2];
    pixels[offset + 3] = color[3];
  };
  const clear = (x, y) => set(x, y, [0, 0, 0, 0]);
  const rect = (x, y, width, height, color) => {
    for (let yy = y; yy < y + height; yy += 1) {
      for (let xx = x; xx < x + width; xx += 1) set(xx, yy, color);
    }
  };
  const hline = (x, y, width, color) => rect(x, y, width, 1, color);
  const vline = (x, y, height, color) => rect(x, y, 1, height, color);
  const diag = (x, y, length, dx, color) => {
    for (let i = 0; i < length; i += 1) set(x + i * dx, y + i, color);
  };
  const visor = (x, y, width) => {
    const variant = (hash >>> 11) % 5;
    if (variant === 0) {
      rect(x, y, width, 2, ink);
      set(x + 1, y, accent);
      set(x + width - 2, y + 1, accent);
    }
    if (variant === 1) {
      hline(x, y, width, ink);
      hline(x + 1, y + 1, width - 2, accent);
    }
    if (variant === 2) {
      rect(x, y, 2, 2, ink);
      rect(x + width - 2, y, 2, 2, ink);
      set(x, y, accent);
      set(x + width - 1, y + 1, accent);
    }
    if (variant === 3) {
      rect(x, y, width, 2, ink);
      for (let i = 1; i < width - 1; i += 2) set(x + i, y + 1, accent);
    }
    if (variant === 4) {
      hline(x, y, width, ink);
      diag(x + 1, y + 1, Math.max(2, Math.min(4, width - 2)), 1, accent);
    }
  };
  const baseHead = (x, y, width, height) => {
    rect(x - 1, y, width + 2, height, shade);
    rect(x, y, width, height, primary);
    hline(x + 1, y, width - 2, light);
    hline(x + 1, y + height - 1, width - 2, shade);
  };

  hline(5, 14, 6, rgba([0, 0, 0], 72));

  switch (agent.division) {
    case "academic":
      hline(3, 3, 10, light);
      hline(5, 2, 6, primary);
      rect(6, 4, 4, 1, shade);
      baseHead(4, 5, 8, 7);
      clear(4, 5);
      clear(11, 5);
      visor(6, 7, 4);
      rect(6, 12, 4, 1, primary);
      break;
    case "design":
      for (let y = 3; y <= 11; y += 1) {
        const width = y < 7 ? (y - 2) * 2 : (12 - y) * 2;
        const x = 8 - Math.floor(width / 2);
        rect(x, y, width, 1, y < 6 ? light : primary);
      }
      rect(5, 6, 6, 4, primary);
      visor(6, 7, 4);
      set(11, 4, accent);
      set(4, 10, shade);
      break;
    case "engineering":
      vline(3, 4, 8, light);
      set(4, 4, light);
      set(4, 11, light);
      vline(12, 4, 8, light);
      set(11, 4, light);
      set(11, 11, light);
      baseHead(5, 5, 6, 6);
      visor(6, 7, 4);
      set(7, 12, primary);
      set(8, 12, primary);
      break;
    case "finance":
      set(8, 2, light);
      hline(5, 3, 6, light);
      hline(4, 4, 8, primary);
      vline(5, 5, 6, primary);
      vline(8, 5, 6, primary);
      vline(11, 5, 6, primary);
      hline(4, 11, 8, shade);
      visor(6, 6, 5);
      hline(5, 13, 6, primary);
      break;
    case "game-development":
      rect(4, 5, 8, 5, primary);
      rect(3, 7, 10, 3, primary);
      set(3, 6, light);
      set(12, 6, light);
      visor(6, 6, 4);
      set(5, 10, accent);
      set(10, 10, accent);
      hline(6, 12, 4, shade);
      break;
    case "gis":
      rect(5, 3, 6, 1, light);
      rect(4, 4, 8, 5, primary);
      rect(5, 9, 6, 1, shade);
      rect(6, 10, 4, 1, primary);
      rect(7, 11, 2, 2, primary);
      visor(6, 6, 4);
      set(8, 13, accent);
      break;
    case "marketing":
      rect(5, 5, 5, 6, primary);
      rect(10, 4, 2, 8, light);
      set(12, 3, light);
      set(12, 12, shade);
      vline(4, 6, 4, shade);
      visor(6, 7, 3);
      set(3, 8, accent);
      set(13, 5, accent);
      break;
    case "paid-media":
      rect(4, 4, 8, 8, primary);
      rect(5, 5, 6, 6, ink);
      rect(6, 6, 4, 4, primary);
      rect(7, 7, 2, 2, accent);
      set(4, 4, light);
      set(11, 4, light);
      set(4, 11, shade);
      set(11, 11, shade);
      break;
    case "product":
      hline(6, 3, 4, light);
      hline(5, 4, 6, light);
      rect(4, 5, 8, 6, primary);
      vline(8, 4, 8, shade);
      hline(5, 8, 6, shade);
      visor(5, 6, 3);
      set(10, 7, accent);
      rect(6, 12, 4, 1, primary);
      break;
    case "project-management":
      rect(5, 3, 6, 1, light);
      rect(4, 4, 8, 8, primary);
      rect(6, 5, 4, 1, ink);
      hline(6, 7, 4, ink);
      hline(6, 9, 3, ink);
      set(5, 7, accent);
      set(5, 9, accent);
      hline(6, 12, 4, shade);
      break;
    case "sales":
      baseHead(4, 5, 8, 7);
      visor(6, 7, 4);
      diag(5, 11, 5, 1, accent);
      hline(8, 7, 4, light);
      vline(11, 4, 4, light);
      set(10, 4, light);
      set(9, 4, light);
      break;
    case "security":
      hline(5, 3, 6, light);
      rect(4, 4, 8, 5, primary);
      rect(5, 9, 6, 1, primary);
      rect(6, 10, 4, 1, shade);
      rect(7, 11, 2, 1, shade);
      visor(6, 6, 4);
      set(8, 9, accent);
      break;
    case "spatial-computing":
      rect(4, 4, 4, 4, primary);
      rect(9, 3, 4, 4, light);
      rect(6, 9, 4, 4, shade);
      hline(7, 7, 4, accent);
      set(5, 5, ink);
      set(10, 4, ink);
      set(7, 10, accent);
      break;
    case "specialized":
      set(8, 2, light);
      set(7, 3, light);
      set(8, 3, light);
      set(9, 3, light);
      rect(5, 5, 6, 6, primary);
      set(4, 8, light);
      set(11, 8, light);
      set(8, 12, shade);
      visor(6, 7, 4);
      set(8, 8, accent);
      break;
    case "support":
      baseHead(5, 5, 6, 6);
      vline(4, 6, 5, light);
      vline(11, 6, 5, light);
      set(3, 8, light);
      set(12, 8, light);
      visor(6, 7, 4);
      hline(7, 12, 4, accent);
      break;
    case "testing":
      rect(6, 3, 4, 1, light);
      rect(7, 4, 2, 3, primary);
      rect(5, 7, 6, 4, primary);
      hline(4, 11, 8, shade);
      visor(6, 8, 4);
      set(6, 10, accent);
      set(9, 10, accent);
      break;
    default:
      baseHead(4, 5, 8, 7);
      visor(6, 7, 4);
      rect(7, 12, 2, 1, primary);
  }

  if ((hash >>> 1) & 1) {
    set(7, 2, accent);
    set(8, 2, accent);
  }
  if ((hash >>> 2) & 1) {
    set(3, 6, light);
    set(12, 6, light);
  }
  if ((hash >>> 4) & 1) {
    set(4, 13, shade);
    set(11, 13, shade);
  }
  if ((hash >>> 6) & 1) clear(4, 4);
  if ((hash >>> 8) & 1) clear(11, 4);

  const chipPositions = [
    [3, 4],
    [12, 4],
    [3, 11],
    [12, 11],
    [6, 2],
    [9, 2],
    [6, 13],
    [9, 13],
  ];
  for (let i = 0; i < 3; i += 1) {
    const [x, y] = chipPositions[(hash >>> (i * 4 + 3)) % chipPositions.length];
    set(x, y, i % 2 ? accent : light);
  }

  const badge = (kind) => {
    const x = (hash >>> 20) & 1 ? 1 : 12;
    const y = (hash >>> 21) & 1 ? 1 : 12;
    const c = accent;
    const d = ink;
    if (kind === "interface") {
      hline(x, y, 3, c);
      vline(x, y, 3, c);
      vline(x + 2, y, 3, c);
    } else if (kind === "server") {
      hline(x, y, 3, c);
      hline(x, y + 1, 3, dim);
      hline(x, y + 2, 3, c);
    } else if (kind === "mobile") {
      rect(x, y, 2, 4, c);
      set(x + 1, y + 3, d);
    } else if (kind === "ai") {
      set(x, y, c);
      set(x + 2, y, c);
      set(x + 1, y + 1, c);
      set(x, y + 2, c);
      set(x + 2, y + 2, c);
    } else if (kind === "ops") {
      set(x + 1, y, c);
      hline(x, y + 1, 3, c);
      set(x + 1, y + 2, c);
    } else if (kind === "data") {
      hline(x, y, 3, c);
      hline(x, y + 1, 3, dim);
      hline(x, y + 2, 3, c);
      set(x, y + 3, c);
      set(x + 2, y + 3, c);
    } else if (kind === "security") {
      hline(x, y + 1, 3, c);
      rect(x, y + 2, 3, 2, c);
      set(x + 1, y, c);
    } else if (kind === "money") {
      rect(x + 1, y, 2, 1, c);
      hline(x, y + 1, 3, c);
      rect(x + 1, y + 2, 2, 1, c);
    } else if (kind === "media") {
      rect(x, y, 4, 4, c);
      rect(x + 1, y + 1, 2, 2, d);
      set(x + 2, y + 2, c);
    } else if (kind === "marketing") {
      hline(x, y + 1, 3, c);
      set(x + 3, y, c);
      set(x + 3, y + 2, c);
      set(x, y + 3, c);
    } else if (kind === "sales") {
      diag(x, y + 3, 4, 1, c);
      hline(x + 2, y, 2, c);
      vline(x + 3, y, 2, c);
    } else if (kind === "project") {
      set(x, y + 1, c);
      set(x + 1, y + 2, c);
      set(x + 2, y + 1, c);
      set(x + 3, y, c);
    } else if (kind === "research") {
      rect(x, y, 2, 3, c);
      rect(x + 2, y, 2, 3, dim);
      hline(x, y + 3, 4, c);
    } else if (kind === "map") {
      rect(x + 1, y, 2, 2, c);
      set(x + 2, y + 1, d);
      set(x + 1, y + 2, c);
      set(x + 1, y + 3, c);
    } else if (kind === "test") {
      hline(x + 1, y, 2, c);
      vline(x + 1, y + 1, 2, c);
      hline(x, y + 3, 4, c);
    } else if (kind === "doc") {
      rect(x, y, 3, 4, c);
      set(x + 2, y, light);
      hline(x + 1, y + 2, 2, d);
    } else if (kind === "support") {
      vline(x, y + 1, 3, c);
      vline(x + 3, y + 1, 3, c);
      hline(x + 1, y, 2, c);
      set(x + 2, y + 3, c);
    } else if (kind === "game") {
      set(x + 1, y + 1, c);
      hline(x, y + 2, 3, c);
      set(x + 3, y + 1, c);
      set(x + 3, y + 3, c);
    } else if (kind === "product") {
      hline(x + 1, y, 2, c);
      hline(x, y + 1, 4, c);
      hline(x + 1, y + 2, 2, c);
      set(x + 2, y + 3, c);
    } else {
      set(x + 1, y, c);
      hline(x, y + 1, 3, c);
      set(x + 1, y + 2, c);
    }
  };
  badge(role);

  const scale = 8;
  const output = Buffer.alloc(128 * 128 * 4);
  for (let y = 0; y < grid; y += 1) {
    for (let x = 0; x < grid; x += 1) {
      const sourceOffset = (y * grid + x) * 4;
      for (let yy = 0; yy < scale; yy += 1) {
        for (let xx = 0; xx < scale; xx += 1) {
          const targetOffset = ((y * scale + yy) * 128 + (x * scale + xx)) * 4;
          output[targetOffset] = pixels[sourceOffset];
          output[targetOffset + 1] = pixels[sourceOffset + 1];
          output[targetOffset + 2] = pixels[sourceOffset + 2];
          output[targetOffset + 3] = pixels[sourceOffset + 3];
        }
      }
    }
  }

  return { width: 128, height: 128, rgba: output };
}

function composite(target, targetWidth, targetHeight, source, sourceWidth, sourceHeight, offsetX, offsetY) {
  for (let y = 0; y < sourceHeight; y += 1) {
    for (let x = 0; x < sourceWidth; x += 1) {
      const sourceOffset = (y * sourceWidth + x) * 4;
      const alpha = source[sourceOffset + 3] / 255;
      if (!alpha) continue;
      const targetX = offsetX + x;
      const targetY = offsetY + y;
      if (targetX < 0 || targetY < 0 || targetX >= targetWidth || targetY >= targetHeight) continue;
      const targetOffset = (targetY * targetWidth + targetX) * 4;
      const inverse = 1 - alpha;
      target[targetOffset] = Math.round(source[sourceOffset] * alpha + target[targetOffset] * inverse);
      target[targetOffset + 1] = Math.round(source[sourceOffset + 1] * alpha + target[targetOffset + 1] * inverse);
      target[targetOffset + 2] = Math.round(source[sourceOffset + 2] * alpha + target[targetOffset + 2] * inverse);
      target[targetOffset + 3] = 255;
    }
  }
}

function nearestScale(image, width, height) {
  const output = Buffer.alloc(width * height * 4);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const sourceX = Math.floor((x * image.width) / width);
      const sourceY = Math.floor((y * image.height) / height);
      const sourceOffset = (sourceY * image.width + sourceX) * 4;
      const targetOffset = (y * width + x) * 4;
      output[targetOffset] = image.rgba[sourceOffset];
      output[targetOffset + 1] = image.rgba[sourceOffset + 1];
      output[targetOffset + 2] = image.rgba[sourceOffset + 2];
      output[targetOffset + 3] = image.rgba[sourceOffset + 3];
    }
  }
  return output;
}

for (const agent of manifest.agents) {
  const image = renderGlyph(agent);
  const outputPath = path.join(outDir, `${slugFromSource(agent.sourceFile)}.png`);
  fs.writeFileSync(outputPath, encodePng(image.width, image.height, image.rgba));
}

if (!skipContactSheet) {
  const columns = 16;
  const cell = 72;
  const rows = Math.ceil(manifest.agents.length / columns);
  const sheetWidth = columns * cell;
  const sheetHeight = rows * cell;
  const sheet = Buffer.alloc(sheetWidth * sheetHeight * 4);
  for (let i = 0; i < sheet.length; i += 4) {
    sheet[i] = 39;
    sheet[i + 1] = 39;
    sheet[i + 2] = 42;
    sheet[i + 3] = 255;
  }

  for (let i = 0; i < manifest.agents.length; i += 1) {
    const image = renderGlyph(manifest.agents[i]);
    const scaled = nearestScale(image, 56, 56);
    const x = (i % columns) * cell + Math.floor((cell - 56) / 2);
    const y = Math.floor(i / columns) * cell + Math.floor((cell - 56) / 2);
    composite(sheet, sheetWidth, sheetHeight, scaled, 56, 56, x, y);
  }

  fs.writeFileSync(path.join(outDir, "_contact-sheet.png"), encodePng(sheetWidth, sheetHeight, sheet));
}

console.log(`Generated ${manifest.agents.length} glyph avatars in ${outDir}`);
