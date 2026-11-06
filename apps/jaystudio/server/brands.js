// Brand profile fields and validation.
export const BRAND_FIELDS = [
  "name", "kind", "tagline", "industry", "offer", "audience", "problems", "differentiators", "values",
  "voice", "competitors", "channels", "goals", "budget", "currency", "colors", "fonts", "assets", "language", "notes",
];

export function sanitizeBrand(input = {}) {
  const out = {};
  for (const k of BRAND_FIELDS) {
    if (input[k] === undefined) continue;
    let v = input[k];
    if (k === "budget") v = v === "" || v === null ? null : Number(v);
    else if (k === "channels") v = Array.isArray(v) ? v.map(String) : String(v).split(",").map((s) => s.trim()).filter(Boolean);
    else if (k === "kind") v = v === "personal" ? "personal" : "business";
    else v = String(v).slice(0, 4000);
    out[k] = v;
  }
  return out;
}
