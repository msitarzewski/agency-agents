// Loads expert personas from this repository (The Agency) to use as system prompts.
import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "./config.js";

const DIVISIONS = ["marketing", "design", "paid-media", "sales", "product", "strategy"];

function parseFrontmatter(src) {
  const m = src.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { meta: {}, body: src };
  const meta = {};
  for (const line of m[1].split("\n")) {
    const kv = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (kv) meta[kv[1]] = kv[2].replace(/^["']|["']$/g, "");
  }
  return { meta, body: src.slice(m[0].length) };
}

let cache = null;
export function listPersonas() {
  if (cache) return cache;
  const out = [];
  for (const div of DIVISIONS) {
    const dir = path.join(REPO_ROOT, div);
    if (!fs.existsSync(dir)) continue;
    for (const f of fs.readdirSync(dir)) {
      if (!f.endsWith(".md")) continue;
      const { meta } = parseFrontmatter(fs.readFileSync(path.join(dir, f), "utf8"));
      if (!meta.name) continue;
      out.push({ id: `${div}/${f.replace(/\.md$/, "")}`, division: div, name: meta.name, description: meta.description || "", emoji: meta.emoji || "" });
    }
  }
  cache = out.sort((a, b) => a.division.localeCompare(b.division) || a.name.localeCompare(b.name));
  return cache;
}

export function personaPrompt(id) {
  if (!id) return null;
  const p = listPersonas().find((x) => x.id === id);
  if (!p) return null;
  const src = fs.readFileSync(path.join(REPO_ROOT, `${id}.md`), "utf8");
  return { ...p, prompt: parseFrontmatter(src).body.trim() };
}
