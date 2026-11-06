# Ideogram 4 — JSON Caption Prompting

Ideogram 4 is trained **exclusively** on structured JSON captions where every element is named
explicitly. This file is the reference for building those captions. The whole prompt-adherence and
text-rendering advantage flows from following this schema precisely — including its quirks (strict
key ordering, an unusual bbox axis order).

## Top-Level Structure

A caption is a JSON object with three top-level fields:

| Field | Required | Purpose |
|-------|----------|---------|
| `high_level_description` | Optional but **strongly recommended** | 1–2 sentence summary of the whole image |
| `style_description` | Optional object | Visual aesthetics, medium, global color palette |
| `compositional_deconstruction` | **Required** object | Spatial layout: background + every element |

## `style_description`

Must contain **exactly one** of `photo` or `art_style`:
- `photo` — for photographic images
- `art_style` — for illustrations, paintings, 3D renders, vector/graphic design

Required keys when the block is present: `aesthetics`, `lighting`, `medium`. Optional: `color_palette`.

### Strict key ordering (this matters)

> "The model was trained on JSON with a consistent key order, so maintaining it improves
> generation quality." Deviating is *allowed* but samples outside the training distribution.

- **Photos:** `aesthetics` → `lighting` → `photo` → `medium` → `color_palette`
- **Non-photos:** `aesthetics` → `lighting` → `medium` → `art_style` → `color_palette`

```json
"style_description": {
  "aesthetics": "bold, modern, high-contrast corporate",
  "lighting": "flat even studio lighting, no harsh shadows",
  "medium": "flat vector graphic design, clean geometric",
  "art_style": "minimalist tech poster, generous negative space",
  "color_palette": ["#0B0B1A", "#00E0C6", "#FFFFFF"]
}
```

## `compositional_deconstruction`

Two required fields:
- `background` — string describing the environment / backdrop
- `elements` — array of objects and text, each with a **fixed key order**

### Element: object (`type: "obj"`)

Key order: `type` → `bbox` → `desc` → `color_palette`

```json
{ "type": "obj", "bbox": [200, 100, 800, 450], "desc": "A sleek silver laptop, three-quarter view, screen glowing.", "color_palette": ["#C0C0C0", "#1B1B2F"] }
```

### Element: text (`type: "text"`)

Key order: `type` → `bbox` → `text` → `desc` → `color_palette`

The `text` field holds the **literal string to render**; `desc` describes how it looks
(font weight, style, placement feel).

```json
{ "type": "text", "bbox": [120, 80, 300, 920], "text": "AI ENGINEERING REVIEW", "desc": "Bold heavy sans-serif headline, all caps, crisp white, centered.", "color_palette": ["#FFFFFF"] }
```

## Bounding Boxes (`bbox`)

- Format: **`[y_min, x_min, y_max, x_max]`** — note the **y-first** axis order (row before column).
- Coordinates are **normalized 0–1000**, where `0` is top/left and `1000` is bottom/right.
- Optional per element. Omit when you don't care where something lands; include for precise layout.

Quick mental map (full frame is 0–1000 on each axis):

```
x:   0 ............... 500 ............... 1000
y=0   ┌───────────────────────────────────┐
      │  top band  [0,0, 250,1000]         │   ← headline / title text here
      │                                    │
y=500 │  center    [350,150, 650,850]      │   ← hero subject
      │                                    │
y=1000│  bottom    [800,0, 1000,1000]      │   ← CTA / footer text
      └───────────────────────────────────┘
```

So a centered headline across the top third is `[80, 100, 280, 900]`
(`y_min=80, x_min=100, y_max=280, x_max=900`).

## Color Palette Rules

- Up to **16** colors in `style_description.color_palette`; up to **5** per element.
- Must be **uppercase hex**: `#RRGGBB` (e.g. `#1B1B2F`, not `#1b1b2f` or `rgb(...)`).
- Include both background and contrast/accent colors for controlled lighting.
- Per-element palettes override/steer that element specifically — ideal for forcing exact brand
  colors on a logo or headline.

## Serialization Quirks

When emitting the JSON string the model consumes:
- Use compact separators: `separators=(",", ":")` (no spaces) — the `--json` path in the tool
  handles this; if hand-passing, compact JSON is safest.
- `ensure_ascii=False` so non-ASCII / multilingual text passes through literally.
- Preserve key order exactly as above.

## Magic Prompt vs. Claude

Ideogram ships an LLM "magic prompt" that expands plain text → JSON. Three configs exist:
`ideogram-4-v1` (free hosted default), `claude-opus-v1`, `claude-sonnet-v1` (both via OpenRouter).
Their docs warn the shipped expander "is **not** the same used in production — results will differ."

**Claude Code runs on Opus.** So the highest-quality path is: Claude builds the caption directly
using this skill, rather than round-tripping through the weaker free expander or adding an
OpenRouter dependency. Treat *yourself* as the magic-prompt LLM.

## Prompting Principles

1. **Name every element explicitly.** The model rewards exhaustive captions. Don't write "a busy
   office" — list the desk, the monitor, the plant, the window light.
2. **Put literal on-image text in a `text` element**, never bury it in a description. This is what
   unlocks the legible-text advantage.
3. **Keep rendered strings reasonable.** A headline + subhead + CTA is fine (its strength); a
   paragraph of body copy still degrades.
4. **Use bboxes for layout-critical images** (title cards, thumbnails). Skip them for loose scenes.
5. **Use per-element palettes to pin brand colors** on logos/headlines; global palette for mood.
6. **Match the style block to intent** — `photo` for realism, `art_style` for design/graphic work.
   Most title cards and thumbnails are `art_style`.

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Plain-text prompt, generic result | Build the JSON caption — that's the whole point |
| Text rendered garbled/misspelled | Put it in a `text` element with the literal string in `text`, keep it short |
| Wrong colors | Uppercase hex, per-element `color_palette` on the headline/logo |
| Text in wrong spot | Add a `bbox` (remember y-first: `[y_min,x_min,y_max,x_max]`, 0–1000) |
| Mediocre adherence | Add `high_level_description`; name more elements; keep key order |
| `lowercase hex` ignored | Always `#RRGGBB` uppercase |
