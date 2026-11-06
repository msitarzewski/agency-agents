---
name: ideogram4
description: Prompting patterns for Ideogram 4 text-to-image — best-in-class in-image text rendering and exact color/layout control via structured JSON captions. Use when generating images that need legible on-image text (title cards, thumbnails, logos, signage, CTAs), precise brand colors, or controlled spatial layout. Triggers include title slide image, thumbnail with text, on-image text, legible text in image, brand color palette image, bounding-box layout, Ideogram.
---

# Ideogram 4 Skill

Text-to-image generation with **Ideogram 4** (9.3B, open-weight, released June 2026). Its
superpower is **best-in-class in-image text rendering** — it beats much larger models
(FLUX.2 dev 32B, Qwen-Image 20B, Hunyuan 80B) at rendering legible signage, logos, captions,
and multi-line text — plus **exact color-palette and bounding-box control**.

That advantage is **locked behind a structured JSON caption format**. A plain-text prompt gets
you FLUX-level results and misses the entire point of using this model. This skill teaches
Claude to act as the "magic prompt" expander — turning a user's casual request into the JSON
caption Ideogram 4 was trained on.

> **Backend:** The toolkit uses Ideogram's **hosted v4 API** (not self-hosted weights). The API
> accepts a structured `json_prompt`, so everything this skill teaches applies directly — Claude
> builds the caption, the tool posts it as `json_prompt`. Paid API plans include a **commercial
> license**, which the self-hostable weights (non-commercial) do not — that's why we use the API.
> Cost is ~$0.03/image (turbo) to ~$0.10/image (quality).

## When to Use This Skill

Reach for Ideogram 4 (over FLUX.2) when the image needs:
- **Legible on-image text** — title cards, thumbnails, lower-thirds backgrounds, signage, logos,
  quote cards, CTAs with a headline baked in
- **Exact brand colors** — hex color-palette conditioning, per-element
- **Controlled layout** — bounding boxes place text/objects in specific regions
- **Multilingual text** in the image

Use **FLUX.2** instead when: the image has no critical text, you need commercial-licensed output,
or you just want a fast atmospheric background. FLUX takes plain natural-language prompts; Ideogram
wants JSON. See `tools/flux2.py`.

## The One Thing to Get Right

**Always emit a structured JSON caption, not a plain sentence.** The model is trained
*exclusively* on JSON captions that name every element explicitly. Claude is a better expander
than Ideogram's free hosted magic-prompt (their own docs note the shipped one "is not the same
used in production"), so build the caption yourself using this skill rather than passing raw text.

Minimal valid caption:

```json
{"high_level_description":"A sailboat at sunset on calm water.","style_description":{"aesthetics":"serene, warm, golden hour","lighting":"golden hour backlighting","photo":"wide angle, f/8","medium":"photograph","color_palette":["#FF6B35","#F7C59F","#004E89"]},"compositional_deconstruction":{"background":"Calm ocean at low horizon with orange-pink sky.","elements":[{"type":"obj","desc":"White triangular sail silhouetted against the setting sun."}]}}
```

Full schema, strict key-ordering rules, and the bbox coordinate system are in **`prompting.md`**.
Worked title-card / thumbnail / quote-card examples are in **`examples.md`**.

## Quick Reference — `tools/ideogram4.py`

> Thin wrapper over Ideogram's hosted v4 API. Needs `IDEOGRAM_API_KEY` in `.env`
> (key from developer.ideogram.ai). `--json` posts the caption as the API's `json_prompt`
> field (no server-side magic prompt — Claude is the expander); `--prompt` posts `text_prompt`.

```bash
# Hand-authored JSON caption (the recommended path for text/layout) — Claude writes caption.json
uv run tools/ideogram4.py --json caption.json --output title.png

# Caption from stdin (Claude can pipe it directly)
cat caption.json | uv run tools/ideogram4.py --json - --output title.png

# Plain prompt — Ideogram's server-side magic prompt expands it (weaker; prefer --json)
uv run tools/ideogram4.py --prompt "Title card: 'AI ENGINEERING REVIEW' bold white on dark" --output title.png

# Inject brand hex colors into the caption's palette (JSON mode)
uv run tools/ideogram4.py --json caption.json --brand digital-samba --output cta.png

# Quality tier + resolution
uv run tools/ideogram4.py --json caption.json --speed QUALITY --resolution 2048x2048 --output slide.png
```

## Ideogram 4.5 (opt-in)

`--model 4.5` sends the same flags to Ideogram 4.5 on the v2 API
(`POST /v2/image/generate/ideogram-4-5`, multipart like the v1 call). It has been run live:
**JSON captions render near-perfect text; plain prompts add garbled filler text**, so always
send a JSON caption to 4.5. Ideogram 4 stays the default because 4.5 sizes must be multiples
of 32, which rules out exact YouTube 1280x720 (`/thumbnail` uses 4.0 for that).

```bash
uv run tools/ideogram4.py --model 4.5 --json caption.json --speed QUALITY --resolution 1440x2560 --output card.png
```

- **Prompt:** both modes go in 4.5's single `prompt` field. `--json` sends the caption as
  compact JSON. 4.5 reads the Ideogram 4 caption format, and a valid caption skips
  server-side magic prompt. `--prompt` text is expanded by magic prompt, as on v1.
- **`--speed` maps to `quality`**: TURBO, DEFAULT and QUALITY at the same price as on
  Ideogram 4, and FLASH, which has no Ideogram 4 price, to low (Ideogram's list prices,
  checked 2026-10-12; 1K and 2K sizes cost the same):

  | `--speed` | 4.5 `quality` | Per image |
  |-----------|---------------|-----------|
  | FLASH, TURBO | `low` | $0.03 |
  | DEFAULT (the default) | `medium` | $0.06 |
  | QUALITY | `high` | $0.10 |

  4.5's `very_low` tier needs source images, so the tool never sends it. On `--model 4`,
  FLASH is still sent as is, but Ideogram's docs say it currently returns HTTP 400.
- **`--resolution` is sent as `size`:** `auto`, or WIDTHxHEIGHT with both sides multiples of
  32 and at least 256px, at most 2048x2048 pixels in total, and an aspect ratio of at most
  6:1. Omit it and Ideogram picks a size from the prompt. The tool checks these rules before
  calling the API and exits 2 when a size breaks them. `1440x2560` (the 9:16 card size) and
  `2048x2048` pass. Six Ideogram 4 presets don't, and the error suggests a replacement:
  720x1280 (1440x2560), 1280x720 (2560x1440), 720x1440 (1440x2880), 1440x720 (2880x1440),
  1296x3168 (1280x3072), 3168x1296 (3072x1280). Without source images Ideogram also needs
  one of its supported 1K/2K presets, a list it doesn't publish, so a size that passes the
  checks can still get an HTTP 400.

## Key Files

- `prompting.md` — full JSON schema, strict key ordering, bbox coordinate system, palette rules
- `examples.md` — worked captions for title cards, thumbnails, quote cards, brand CTAs

## Video Production Fit

Ideogram 4's niche in the toolkit is **slides and thumbnails with baked-in text**, where FLUX and
LTX-2 fail (both render garbled text). Natural pairings:

| Use case | Why Ideogram 4 |
|----------|----------------|
| Title-card / CTA background **with headline text** | Legible text + exact brand hex colors in one pass |
| YouTube/social **thumbnail with a punchy phrase** | Big readable text is its strongest suit |
| Quote card / stat card | Multi-line text + layout control via bboxes |
| Signage/logos inside a product-demo scene | In-image text other models can't render |

Then feed the still into Remotion (`<OffthreadVideo>`/`Img`) or animate it with `tools/ltx2.py --input`.
