# Ideogram 4 — Worked Examples

Real caption examples for the toolkit's bread-and-butter use cases. Each shows the user's casual
ask and the JSON caption Claude should produce (this *is* the magic-prompt expansion). JSON is
shown pretty-printed for readability — serialize compact (`separators=(",",":")`) when passing.

---

## 1. Title card with headline text (the flagship use case)

**User:** "Title card for the AI Engineering Review video — big bold 'AI ENGINEERING REVIEW' on a
dark techy background."

```json
{
  "high_level_description": "A dark modern tech title card with a large bold headline reading 'AI ENGINEERING REVIEW' centered in the upper-middle.",
  "style_description": {
    "aesthetics": "bold, modern, high-contrast corporate tech, generous negative space",
    "lighting": "soft cyan rim glow from below, deep shadows",
    "medium": "flat vector graphic design with subtle gradient backdrop",
    "art_style": "minimalist tech poster, clean geometric",
    "color_palette": ["#0B0B1A", "#00E0C6", "#1B2A4A", "#FFFFFF"]
  },
  "compositional_deconstruction": {
    "background": "Deep near-black navy gradient with a faint geometric grid and a soft cyan glow rising from the lower edge.",
    "elements": [
      {
        "type": "text",
        "bbox": [340, 120, 540, 880],
        "text": "AI ENGINEERING REVIEW",
        "desc": "Bold heavy sans-serif headline, all caps, crisp white, tight letter spacing, centered.",
        "color_palette": ["#FFFFFF"]
      },
      {
        "type": "obj",
        "bbox": [580, 380, 620, 620],
        "desc": "A thin glowing cyan horizontal accent rule beneath the headline.",
        "color_palette": ["#00E0C6"]
      }
    ]
  }
}
```

Why it works: the headline is a `text` element with the literal string (legible-text strength),
the brand cyan is pinned via per-element palette on the accent rule, and the bbox keeps the title
in the upper-middle band.

---

## 2. Thumbnail with a punchy phrase

**User:** "YouTube thumbnail, the words 'SHIP FASTER' huge on the left, a rocket on the right."

```json
{
  "high_level_description": "A high-energy thumbnail with the huge two-line phrase 'SHIP FASTER' on the left and a stylized rocket launching on the right.",
  "style_description": {
    "aesthetics": "loud, saturated, high-energy, big-text thumbnail style",
    "lighting": "bright punchy lighting with strong contrast",
    "medium": "bold flat illustration",
    "art_style": "modern poster illustration, thick outlines",
    "color_palette": ["#FF3B30", "#FFD60A", "#0B0B1A", "#FFFFFF"]
  },
  "compositional_deconstruction": {
    "background": "Bold diagonal split background, deep navy on the right, warm yellow burst on the left.",
    "elements": [
      {
        "type": "text",
        "bbox": [250, 40, 750, 520],
        "text": "SHIP FASTER",
        "desc": "Massive heavy condensed sans-serif, two lines, all caps, white with a thick dark outline, left-aligned.",
        "color_palette": ["#FFFFFF", "#0B0B1A"]
      },
      {
        "type": "obj",
        "bbox": [200, 560, 850, 960],
        "desc": "A stylized cartoon rocket launching upward with a bright flame trail, slight tilt.",
        "color_palette": ["#FF3B30", "#FFD60A", "#FFFFFF"]
      }
    ]
  }
}
```

Keep thumbnail phrases to 1–3 words — that's where the text rendering is strongest.

---

## 3. Brand CTA with exact colors

**User:** "End-card CTA for Digital Samba: 'Start your free trial' button, on-brand colors."

> When the user names a brand, read `brands/<brand>/brand.json` for the real hex values and place
> them in the palettes. The placeholders below stand in for those.

```json
{
  "high_level_description": "A clean end-card with the headline 'Start your free trial' and a rounded call-to-action button, in Digital Samba brand colors.",
  "style_description": {
    "aesthetics": "clean, trustworthy, modern SaaS",
    "lighting": "even soft lighting, airy",
    "medium": "flat UI-style vector graphic",
    "art_style": "minimal product marketing card, lots of whitespace",
    "color_palette": ["#FFFFFF", "#1456F0", "#0B1B3A"]
  },
  "compositional_deconstruction": {
    "background": "Soft white-to-pale-blue gradient, very clean.",
    "elements": [
      {
        "type": "text",
        "bbox": [300, 150, 460, 850],
        "text": "Start your free trial",
        "desc": "Friendly bold sans-serif headline, dark navy, centered.",
        "color_palette": ["#0B1B3A"]
      },
      {
        "type": "obj",
        "bbox": [560, 340, 680, 660],
        "desc": "A rounded rectangular button with subtle shadow.",
        "color_palette": ["#1456F0"]
      },
      {
        "type": "text",
        "bbox": [585, 360, 655, 640],
        "text": "Get started free",
        "desc": "Button label, medium-weight white sans-serif, centered on the button.",
        "color_palette": ["#FFFFFF"]
      }
    ]
  }
}
```

Note the layered text-over-object: the button is an `obj`, its label is a separate `text` element
with a tighter bbox sitting inside the button's bbox.

---

## 4. Quote / stat card (multi-line text + layout)

**User:** "Stat card: big '94%' with 'of teams shipped faster' underneath."

```json
{
  "high_level_description": "A minimal stat card with a giant '94%' figure and the supporting line 'of teams shipped faster' beneath it.",
  "style_description": {
    "aesthetics": "confident, minimal, data-forward",
    "lighting": "flat even studio light",
    "medium": "flat vector graphic design",
    "art_style": "clean infographic card",
    "color_palette": ["#0B0B1A", "#00E0C6", "#FFFFFF"]
  },
  "compositional_deconstruction": {
    "background": "Solid deep navy with a faint radial glow behind the figure.",
    "elements": [
      {
        "type": "text",
        "bbox": [220, 250, 560, 750],
        "text": "94%",
        "desc": "Enormous bold sans-serif figure, bright cyan, centered.",
        "color_palette": ["#00E0C6"]
      },
      {
        "type": "text",
        "bbox": [600, 200, 700, 800],
        "text": "of teams shipped faster",
        "desc": "Medium-weight white sans-serif subline, centered beneath the figure.",
        "color_palette": ["#FFFFFF"]
      }
    ]
  }
}
```

---

## 5. Photographic scene (when to use `photo`)

**User:** "A photo of a modern office at golden hour for a background, no text."

```json
{
  "high_level_description": "A warm, modern open-plan office bathed in golden-hour light, no text.",
  "style_description": {
    "aesthetics": "warm, aspirational, editorial",
    "lighting": "golden hour sunlight streaming through floor-to-ceiling windows, long soft shadows",
    "photo": "35mm, f/2.8, shallow depth of field, eye-level",
    "medium": "photograph",
    "color_palette": ["#F4C77E", "#3A2E25", "#D9C8B4"]
  },
  "compositional_deconstruction": {
    "background": "Open-plan office with wood desks and plants, large windows with sun flare at the far end.",
    "elements": [
      {
        "type": "obj",
        "bbox": [350, 100, 800, 500],
        "desc": "A wooden desk with an open laptop and a steaming coffee mug, foreground left.",
        "color_palette": ["#6B4E2E", "#1B1B1B"]
      },
      {
        "type": "obj",
        "bbox": [300, 600, 750, 780],
        "desc": "A leafy potted plant catching warm backlight.",
        "color_palette": ["#3E5C2E"]
      }
    ]
  }
}
```

Note the key order flips for photos: `aesthetics → lighting → photo → medium → color_palette`.

---

## Good vs. bad at a glance

| Bad (plain text) | Good (JSON caption) |
|------------------|---------------------|
| `"Title card saying AI Engineering Review"` | Example 1 — headline as a `text` element, bbox, brand palette |
| Text described inside `desc` | Literal string in the `text` field of a `text` element |
| `color: blue` | `"color_palette": ["#1456F0"]` (uppercase hex, per element) |
| Paragraph of body copy in one text element | 1–3 word headline + short subline, each its own element |
| Lowercase hex `#1456f0` | Uppercase `#1456F0` |
