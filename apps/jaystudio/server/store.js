// Tiny JSON-file store. Everything stays on the user's machine in data/.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { DATA_DIR } from "./config.js";

function file(name) {
  return path.join(DATA_DIR, `${name}.json`);
}

export function readCollection(name) {
  try {
    return JSON.parse(fs.readFileSync(file(name), "utf8"));
  } catch {
    return [];
  }
}

export function writeCollection(name, items) {
  const tmp = file(name) + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(items, null, 2));
  fs.renameSync(tmp, file(name));
}

export function newId(prefix) {
  return `${prefix}_${crypto.randomBytes(6).toString("hex")}`;
}

export function insert(name, item) {
  const items = readCollection(name);
  items.push(item);
  writeCollection(name, items);
  return item;
}

export function findById(name, id) {
  return readCollection(name).find((x) => x.id === id) || null;
}

export function update(name, id, patch) {
  const items = readCollection(name);
  const i = items.findIndex((x) => x.id === id);
  if (i < 0) return null;
  items[i] = { ...items[i], ...patch, id, updatedAt: new Date().toISOString() };
  writeCollection(name, items);
  return items[i];
}

export function remove(name, id) {
  const items = readCollection(name);
  const next = items.filter((x) => x.id !== id);
  writeCollection(name, next);
  return next.length !== items.length;
}

// Key/value objects (response cache, assistant sessions).
export function readMap(name) {
  try {
    return JSON.parse(fs.readFileSync(file(name), "utf8"));
  } catch {
    return {};
  }
}

export function writeMap(name, obj) {
  const tmp = file(name) + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(obj));
  fs.renameSync(tmp, file(name));
}

export function hash(...parts) {
  return crypto.createHash("sha256").update(JSON.stringify(parts)).digest("hex").slice(0, 32);
}
