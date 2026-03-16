# /tweet-card-brief

Generate a complete design brief for a single Telcoin Association tweet card graphic.

## Usage
Provide the tweet text (or topic + tier). This skill outputs a Figma-ready design brief that a designer (human or AI) can execute directly.

## What you must do

1. Read `strategy/BRAND-GUIDE.md` before generating the brief
2. Read the tweet text provided via $ARGUMENTS
3. Determine the content tier:
   - **Tier 1** (Governance): Strictly institutional - no decorative elements, type-only or minimal graphic
   - **Tier 2** (Education): Informative visual - diagram, architecture illustration, or abstract concept
   - **Tier 3** (Milestone): Announcement visual - bold, controlled, proud but not flashy
   - **Tier 4** (Community): Warmer but still institutional - human element allowed
4. Output a complete design brief in the format below

## Output format

---

## Tweet Card Design Brief

**Tweet text**: [quoted text from input]
**Content tier**: [1/2/3/4]
**Card type**: [Header / Mid-thread insert / Standalone]
**Dimensions**: 1200 x 675px (16:9 for header) OR 1080 x 1080px (1:1 for insert)

---

### Canvas

| Element | Spec |
|---|---|
| Background | [color or gradient from brand palette] |
| Background texture | [solid / subtle hex grid overlay at 8% opacity / none] |
| Card style | [solid / glass panel / gradient overlay] |

### Typography

| Element | Font | Weight | Size | Color | Alignment |
|---|---|---|---|---|---|
| Headline | New Hero | Bold | 48-56px | TEL White #F1F4FF | Left-aligned |
| Body (if any) | New Hero | Regular | 24-28px | TEL Blue Soft #C9CFED | Left-aligned |
| Label/Tag | New Hero | Regular | 18px | TEL Blue #14C8FF | Left-aligned |

### Copy to place on card
> **Headline**: [extracted or condensed from tweet - max 8 words]
> **Supporting text**: [optional - max 1 short sentence if needed]
> **Label**: [optional - e.g., "Governance Update" / "Platform Architecture" / "TELx"]

### Brand elements

| Element | Placement | Spec |
|---|---|---|
| Horizontal logo | Top-left | 1 mark height from top; 1.5 mark widths from left |
| Hexagon motif | Background right / corner | 20-30% opacity, Royal Blue #3642B2, no fill |
| Accent line | Bottom or left edge | 2px, TEL Blue #14C8FF |

### Visual element (if applicable)
> [Describe what supporting visual goes here - e.g., "abstract hexagonal node network, glowing blue, top-right quadrant" OR "none - type-only card"]

### Color usage

| Area | Color | Hex |
|---|---|---|
| Canvas background | [name] | [hex] |
| Primary text | TEL White | #F1F4FF |
| Secondary text | TEL Blue Soft | #C9CFED |
| Accent / highlight | TEL Blue | #14C8FF |
| Geometric elements | Tel Royal Blue | #3642B2 |

### Compliance checks
- [ ] No hype language or promotional tone in copy
- [ ] Logo present and correctly placed
- [ ] Font is New Hero (or documented fallback)
- [ ] Colors match brand palette
- [ ] Tier 1: no emojis anywhere on card
- [ ] No busy background that interferes with text legibility
- [ ] Text passes contrast ratio (4.5:1 minimum)

### Image prompt (if AI-generated visual needed)
> Use `/brand-image-prompt [topic]` to generate the visual element separately, then composite in Figma.

---

$ARGUMENTS
