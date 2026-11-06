---
description: Brand profiles - list, edit, or create new
---

# Brand

Unified command for brand profiles. Lists existing brands or creates new ones.

## Entry Point Logic

On invocation, scan for brands and adapt:

### Step 1: Scan Brands

```
1. Glob brands/*/brand.json
2. For each brand found:
   - Read brand.json
   - Extract name, primary color, description
   - Check if voice.json exists
   - Check if logo exists in assets/
3. Sort alphabetically
```

### Step 2: Present Options

**Show existing brands with option to create:**

```
Available brands:

  1. **default**
     Primary: #3B82F6 (blue)
     Voice: configured
     Logo: ✅

  2. **digital-samba**
     Primary: #FF6B00 (orange)
     Voice: configured
     Logo: ✅

  → Use a brand: enter number
  → Create new brand: enter 'new'
  → Edit a brand: enter 'edit N'
```

**If user selects a brand:**
Show details and offer to edit or confirm for use.

**If user selects 'new':**
Proceed to New Brand Flow.

**If user selects 'edit N':**
Proceed to Edit Brand Flow.

---

## New Brand Flow

### Step 1: Gather Brand Information

**Brand Basics:**
```
Let's create a new brand profile.

Brand name: (e.g., "Acme Corp", "My Startup")
Description: (one sentence about the brand)
Website URL: (optional, for color extraction)
```

### Step 2: Color Source

Ask how to get colors:

```
How would you like to set up colors?

  1. Extract from website URL
  2. Provide a primary color (I'll generate a palette)
  3. Enter all colors manually
```

**Option 1 - Extract from URL:**
```
1. WebFetch the website
2. Analyze for:
   - CSS custom properties (--primary-color, --accent, etc.)
   - Header/nav background colors
   - Button colors
   - Text color hierarchy
3. Present extracted colors for confirmation
4. Allow adjustments
```

**Option 2 - Generate from primary:**
```
What's your primary brand color? (hex, e.g., #FF6B00)

I'll generate a cohesive palette from this.
```

Generate:
- Primary: user's color
- Primary Light: lighten 15-20%
- Text Dark: #1e293b
- Text Medium: #475569
- Text Light: #94a3b8
- Bg Light: #ffffff
- Bg Dark: darken primary or #0f172a

**Option 3 - Manual entry:**
```
Enter colors (hex format):

Primary color: #
Primary light: #
Text dark: #
Text medium: #
Text light: #
Background light: # (default: #ffffff)
Background dark: #
```

### Step 3: Typography

```
Typography settings:

Primary font family: (default: "Inter, system-ui, sans-serif")
Monospace font: (default: "ui-monospace, SFMono-Regular, monospace")
```

### Step 4: Logo

```
Do you have a logo to add?

  1. Yes, I have a file ready
  2. No logo for now
  3. I need to create one later

If yes:
  - What format? (PNG/SVG preferred)
  - Do you have a light version for dark backgrounds?

Place your logo at:
  brands/{name}/assets/logo.png
  brands/{name}/assets/logo-light.png (optional)
```

### Step 5: Voice Settings (Optional)

```
Configure voice settings?

  1. ElevenLabs — I have a voice ID
  2. Qwen3-TTS — built-in speaker (free, self-hosted)
  3. Qwen3-TTS — voice clone (record your own voice)
  4. Skip for now (can configure later)

Option 1 (ElevenLabs):
  Voice ID: ___
  Stability: (default: 0.75)
  Similarity boost: (default: 0.9)

Option 2 (Qwen3-TTS built-in):
  Speaker: Ryan, Aiden (EN), Vivian, Serena (ZH), Ono_Anna (JA), Sohee (KO)
  Language: Auto (default)
  Instruction: (optional, e.g., "Speak warmly")

Option 3 (Qwen3-TTS clone):
  → Run /voice-clone to set up a cloned voice for this brand
```

### Step 6: Create Brand Profile

1. Create directory: `brands/{name-lowercase}/`

2. Write `brand.json`:
```json
{
  "name": "Brand Name",
  "description": "Brand description",
  "version": "1.0.0",
  "website": "https://example.com",
  "colors": {
    "primary": "#...",
    "primaryLight": "#...",
    "textDark": "#...",
    "textMedium": "#...",
    "textLight": "#...",
    "bgLight": "#ffffff",
    "bgDark": "#...",
    "bgOverlay": "rgba(255, 255, 255, 0.95)",
    "divider": "#e2e8f0",
    "shadow": "rgba(0, 0, 0, 0.12)"
  },
  "fonts": {
    "primary": "Inter, system-ui, sans-serif",
    "mono": "ui-monospace, SFMono-Regular, monospace"
  },
  "spacing": {
    "xs": 8, "sm": 16, "md": 24, "lg": 48, "xl": 80, "xxl": 120
  },
  "borderRadius": {
    "sm": 6, "md": 10, "lg": 16
  },
  "typography": {
    "h1": { "size": 88, "weight": 700 },
    "h2": { "size": 72, "weight": 700 },
    "h3": { "size": 48, "weight": 600 },
    "body": { "size": 44, "weight": 400 },
    "label": { "size": 34, "weight": 600, "letterSpacing": 2 }
  },
  "assets": {
    "logo": "assets/logo.png",
    "logoLight": "assets/logo-light.png"
  }
}
```

3. Write `voice.json`:
```json
{
  "voiceId": "YOUR_VOICE_ID_HERE",
  "description": "Voice description",
  "settings": {
    "stability": 0.75,
    "similarityBoost": 0.9,
    "style": 0.2,
    "useSpeakerBoost": true
  },
  "model": "eleven_multilingual_v2"
}
```

4. Create `assets/` directory

### Step 7: Confirmation

```
Brand created: brands/{name}/

Files:
  ✅ brand.json - visual identity
  ✅ voice.json - ElevenLabs settings
  ✅ assets/ - logo directory

Next steps:
  1. Add your logo to brands/{name}/assets/logo.png
  2. Update voice.json with your ElevenLabs voice ID
  3. Use with /video when creating projects

See docs/creating-brands.md for more details.
```

---

## Edit Brand Flow

When editing an existing brand:

```
Editing: digital-samba

What would you like to change?

  1. Colors
  2. Typography
  3. Voice settings
  4. View current config

Enter choice:
```

Load current config, apply changes, write back.

---

## Brand Details View

When viewing a brand:

```
Brand: digital-samba

Colors:
  Primary: #FF6B00
  Primary Light: #FF8533
  Text Dark: #1e293b
  Background: #ffffff / #0f172a

Typography:
  Primary: Inter, system-ui, sans-serif
  Headings: 88/72/48px bold

Voice:
  ID: configured (use ELEVENLABS_VOICE_ID env var to override)
  Model: eleven_multilingual_v2

Assets:
  Logo: ✅ assets/logo.png
  Logo Light: ❌ not found

Actions:
  → Edit this brand
  → Back to list
```

---

## Color Extraction Tips

When extracting from a website:
- Look for CSS custom properties (--primary-color, --brand-color, etc.)
- Check header/navigation for primary brand color
- Analyze button and link colors for accents
- Note text color hierarchy (headings vs body vs muted)
- Check dark mode if present
- Look for gradients that might indicate color direction

---

## Integration

This command is referenced by:
- `/video` - when selecting brand for new projects
- Templates - load brand via `src/config/brand.ts`

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/brand.md` → Update `_internal/CHANGELOG.md`
3. Share upstream → `gh pr create`

**Remote contributions:**
- Issues: `github.com/digitalsamba/claude-code-video-toolkit/issues`
- PRs welcome for new features, bug fixes, documentation

History: `/new-brand` → `/brand` (unified with list/edit support)
